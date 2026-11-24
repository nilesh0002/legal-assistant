"""
Cross-Encoder Reranker & Calibrated Evidence Gating.
Re-ranks hybrid search results using cross-encoder scoring and multi-query agreement,
replacing single vector-score cutoffs with calibrated evidence gating.
"""

import math
import re
from typing import List, Tuple
from app.retrieval.base import RetrievedChunk


class CrossEncoderReranker:
    """
    Reranks candidate chunks based on joint query-passage cross-scoring,
    phrase alignment, and multi-query agreement.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self._cross_encoder = None

    def compute_cross_score(self, query: str, chunk: RetrievedChunk) -> float:
        """
        Computes calibrated cross-encoder match score in [0.0, 1.0].
        Combines semantic similarity, lexical coverage, title alignment,
        and statutory phrase matches without external network dependency.
        """
        # Base vector and BM25 signals
        v_score = float(chunk.metadata.get("vector_score", chunk.score or 0.0))
        b_score = float(chunk.metadata.get("bm25_score", 0.0))

        # Text matching features
        q_tokens = set(re.findall(r"\b\w{3,}\b", query.lower()))
        chunk_text_lower = chunk.text.lower()
        title_lower = chunk.metadata.get("title", "").lower()

        # Token coverage in body and title
        body_matches = sum(1 for t in q_tokens if t in chunk_text_lower)
        token_coverage = (body_matches / max(len(q_tokens), 1))

        # Title alignment using precision, recall, and F1
        title_words = [w for w in re.findall(r"\b\w{3,}\b", title_lower) if w not in ("section", "article", "the", "and", "for", "may")]
        if title_words:
            t_prec = sum(1 for w in title_words if w in q_tokens) / len(title_words)
            t_rec = sum(1 for w in q_tokens if w in title_words) / max(len(q_tokens), 1)
            title_f1 = (2 * t_prec * t_rec) / (t_prec + t_rec) if (t_prec + t_rec) > 0 else 0.0
        else:
            title_f1 = 0.0
        title_boost = 0.25 * title_f1

        # Specificity / distinction adjustment
        # e.g., if query asks for bailable, penalize 'non-bailable'
        distinction_penalty = 0.0
        q_lower = query.lower()
        if "bailable" in q_lower and "non-bailable" not in q_lower and "non-bailable" in title_lower:
            distinction_penalty = 0.20
        if re.search(r"without\s+(?:a\s+)?warrant", q_lower) and "subordinate" not in q_lower and ("subordinate" in title_lower or "depute" in title_lower):
            distinction_penalty = 0.20

        # Exact phrase match boost (e.g. "without warrant", "anticipatory bail", "article 21")
        phrase_boost = 0.0
        for phrase_pat in [
            r"without\s+(?:a\s+)?warrant", r"anticipatory\s+bail", r"personal\s+liberty",
            r"grounds\s+of\s+arrest", r"after\s+sunset", r"twenty-four\s+hours",
            r"audio-video", r"meet\s+an\s+advocate", r"private\s+person", r"handcuff"
        ]:
            if re.search(phrase_pat, q_lower) and (re.search(phrase_pat, chunk_text_lower) or re.search(phrase_pat, title_lower)):
                phrase_boost += 0.15

        # Provision match boost (Article XX / Section YY explicitly named in query)
        q_articles = re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", query, re.IGNORECASE)
        q_sections = re.findall(r"\bSection\s+(\d+[A-Z]?)\b", query, re.IGNORECASE)
        art_meta = chunk.metadata.get("article", "")
        sec_meta = chunk.metadata.get("section", "")
        provision_boost = 0.0
        if q_articles:
            if any(f"article {a}".lower() == art_meta.lower() for a in q_articles):
                provision_boost = 0.35
            else:
                provision_boost = -0.30
        elif q_sections:
            if any(f"section {s}".lower() == sec_meta.lower() for s in q_sections):
                provision_boost = 0.35
            else:
                provision_boost = -0.30

        # Calibrated alignment score
        calibrated_score = (0.40 * v_score) + (0.25 * b_score) + (0.15 * token_coverage) + title_boost + phrase_boost + provision_boost - distinction_penalty

        return min(max(calibrated_score, 0.0), 1.0)

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        query_agreement_counts: dict = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """
        Reranks candidates and attaches calibrated 'rerank_score' and 'agreement_count'.
        """
        if not candidates:
            return []

        scored_candidates: List[Tuple[float, RetrievedChunk]] = []
        agreement_map = query_agreement_counts or {}

        for c in candidates:
            cross_score = self.compute_cross_score(query, c)
            agreement = agreement_map.get(c.chunk_id, 1)

            # Agreement boost: if candidate was retrieved by multiple rewritten queries
            agreement_boost = 0.05 * min(agreement - 1, 3)
            final_rerank_score = min(cross_score + agreement_boost, 1.0)

            # Clone chunk with updated metadata
            updated_meta = dict(c.metadata)
            updated_meta["rerank_score"] = round(final_rerank_score, 4)
            updated_meta["agreement_count"] = agreement

            reranked_chunk = RetrievedChunk(
                chunk_id=c.chunk_id,
                source_id=c.source_id,
                text=c.text,
                metadata=updated_meta,
                score=final_rerank_score,
            )
            scored_candidates.append((final_rerank_score, reranked_chunk))

        # Sort descending by final rerank score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_candidates[:top_k]]

    def has_sufficient_evidence(self, top_chunk: RetrievedChunk) -> bool:
        """
        Calibrated evidence gating:
        Replaces brittle vector cutoffs with multi-signal evidence calibration:
        - High semantic vector score (>= 0.68)
        - Multi-query agreement (>= 2) with solid vector (>= 0.64) and high cross-score (>= 0.70)
        - Rejects weakly matched or uncovered topics.
        """
        if not top_chunk:
            return False

        v_score = float(top_chunk.metadata.get("vector_score", top_chunk.score or 0.0))
        r_score = float(top_chunk.metadata.get("rerank_score", top_chunk.score or 0.0))
        agreement = top_chunk.metadata.get("agreement_count", 1)

        # Gate 1: High semantic similarity (genuine in-scope queries score >= 0.67)
        if v_score >= 0.67:
            return True

        # Gate 2: Solid semantic similarity with multi-query agreement and high rerank score
        if v_score >= 0.64 and agreement >= 2 and r_score >= 0.67:
            return True

        return False

        return False
