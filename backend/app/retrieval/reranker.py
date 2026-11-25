"""
Cross-Encoder Reranker & Calibrated Evidence Gating.
Uses a true ONNX Cross-Encoder (fastembed TextCrossEncoder) behind a BaseReranker
interface, with deterministic HeuristicReranker kept as offline fallback.
"""

from abc import ABC, abstractmethod
import math
import os
import re
from typing import Dict, List, Optional, Tuple
from app.retrieval.base import RetrievedChunk


class BaseReranker(ABC):
    """Interface for reranking and evidence gating implementations."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        query_agreement_counts: Optional[Dict[str, int]] = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        pass

    @abstractmethod
    def has_sufficient_evidence(self, top_chunk: RetrievedChunk) -> bool:
        pass


class HeuristicReranker(BaseReranker):
    """
    Deterministic offline fallback reranker based on lexical coverage,
    title alignment, and multi-query agreement.
    """

    def compute_cross_score(self, query: str, chunk: RetrievedChunk) -> float:
        v_score = float(chunk.metadata.get("vector_score", chunk.score or 0.0))
        b_score = float(chunk.metadata.get("bm25_score", 0.0))

        q_tokens = set(re.findall(r"\b\w{3,}\b", query.lower()))
        chunk_text_lower = chunk.text.lower()
        title_lower = chunk.metadata.get("title", "").lower()

        body_matches = sum(1 for t in q_tokens if t in chunk_text_lower)
        token_coverage = body_matches / max(len(q_tokens), 1)

        title_words = [
            w for w in re.findall(r"\b\w{3,}\b", title_lower)
            if w not in ("section", "article", "the", "and", "for", "may")
        ]
        if title_words:
            t_prec = sum(1 for w in title_words if w in q_tokens) / len(title_words)
            t_rec = sum(1 for w in q_tokens if w in title_words) / max(len(q_tokens), 1)
            title_f1 = (2 * t_prec * t_rec) / (t_prec + t_rec) if (t_prec + t_rec) > 0 else 0.0
        else:
            title_f1 = 0.0
        title_boost = 0.25 * title_f1

        distinction_penalty = 0.0
        q_lower = query.lower()
        if "bailable" in q_lower and "non-bailable" not in q_lower:
            if "non-bailable" in title_lower:
                distinction_penalty += 0.20
            if "anticipatory" not in q_lower and "apprehend" not in q_lower:
                if "anticipatory" in title_lower or "apprehending" in title_lower:
                    distinction_penalty += 0.25
        if re.search(r"without\s+(?:a\s+)?warrant", q_lower) and "subordinate" not in q_lower and ("subordinate" in title_lower or "depute" in title_lower):
            distinction_penalty += 0.20
        if "arrest" in q_lower and "trespass" not in q_lower and ("trespass" in title_lower or "breaking" in title_lower):
            distinction_penalty += 0.35
        if not any(w in q_lower for w in ("woman", "women", "female", "girl", "modesty", "disrobe", "stalk", "voyeur")):
            if any(w in title_lower for w in ("woman", "modesty", "disrobe")):
                distinction_penalty += 0.25

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

        calibrated = (
            (0.40 * v_score)
            + (0.25 * b_score)
            + (0.15 * token_coverage)
            + title_boost
            + provision_boost
            - distinction_penalty
        )
        return min(max(calibrated, 0.0), 1.0)

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        query_agreement_counts: Optional[Dict[str, int]] = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        if not candidates:
            return []

        scored_candidates: List[Tuple[float, RetrievedChunk]] = []
        agreement_map = query_agreement_counts or {}

        for c in candidates:
            cross_score = self.compute_cross_score(query, c)
            agreement = agreement_map.get(c.chunk_id, 1)
            agreement_boost = 0.05 * min(agreement - 1, 3)
            final_rerank_score = min(cross_score + agreement_boost, 1.0)

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

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_candidates[:top_k]]

    def has_sufficient_evidence(self, top_chunk: RetrievedChunk) -> bool:
        if not top_chunk:
            return False

        v_score = float(top_chunk.metadata.get("vector_score", top_chunk.score or 0.0))
        r_score = float(top_chunk.metadata.get("rerank_score", top_chunk.score or 0.0))
        agreement = top_chunk.metadata.get("agreement_count", 1)

        if v_score >= 0.67:
            return True
        if v_score >= 0.64 and agreement >= 2 and r_score >= 0.67:
            return True
        return False


class CrossEncoderReranker(BaseReranker):
    """
    True Cross-Encoder reranker using fastembed TextCrossEncoder,
    with HeuristicReranker as automatic fallback if ONNX model is unavailable.
    """

    def __init__(self, model_name: str = "Xenova/ms-marco-MiniLM-L-6-v2"):
        self.model_name = os.getenv("CROSS_ENCODER_MODEL", model_name)
        self._cross_encoder = None
        self._load_attempted = False
        self._fallback = HeuristicReranker()

    def _get_encoder(self):
        if self._cross_encoder is not None:
            return self._cross_encoder
        if self._load_attempted:
            return None
        self._load_attempted = True
        try:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            # Load from local cache without network calls if already cached
            self._cross_encoder = TextCrossEncoder(
                model_name=self.model_name,
                local_files_only=True,
            )
        except Exception:
            try:
                from fastembed.rerank.cross_encoder import TextCrossEncoder
                self._cross_encoder = TextCrossEncoder(model_name=self.model_name)
            except Exception:
                self._cross_encoder = None
        return self._cross_encoder

    @staticmethod
    def _sigmoid(x: float) -> float:
        try:
            return 1.0 / (1.0 + math.exp(-max(min(x, 20.0), -20.0)))
        except OverflowError:
            return 0.0 if x < 0 else 1.0

    def compute_cross_score(self, query: str, chunk: RetrievedChunk) -> float:
        encoder = self._get_encoder()
        if encoder is None:
            return self._fallback.compute_cross_score(query, chunk)
        try:
            doc_text = f"{chunk.metadata.get('title', '')}. {chunk.text[:2500]}"
            raw_logit = list(encoder.rerank(query, [doc_text]))[0]
            ce_prob = self._sigmoid(float(raw_logit))
            h_score = self._fallback.compute_cross_score(query, chunk)
            return min(max((0.45 * ce_prob) + (0.55 * h_score), 0.0), 1.0)
        except Exception:
            return self._fallback.compute_cross_score(query, chunk)

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        query_agreement_counts: Optional[Dict[str, int]] = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        if not candidates:
            return []

        encoder = self._get_encoder()
        if encoder is None:
            return self._fallback.rerank(query, candidates, query_agreement_counts, top_k=top_k)

        agreement_map = query_agreement_counts or {}
        try:
            docs = [f"{c.metadata.get('title', '')}. {c.text[:2500]}" for c in candidates]
            raw_logits = list(encoder.rerank(query, docs))
        except Exception:
            return self._fallback.rerank(query, candidates, query_agreement_counts, top_k=top_k)

        scored_candidates: List[Tuple[float, RetrievedChunk]] = []
        for c, raw_logit in zip(candidates, raw_logits):
            ce_prob = self._sigmoid(float(raw_logit))
            h_score = self._fallback.compute_cross_score(query, c)
            agreement = agreement_map.get(c.chunk_id, 1)
            agreement_boost = 0.05 * min(agreement - 1, 3)

            # Combined calibrated cross-encoder + retrieval alignment score
            final_rerank_score = min(max((0.45 * ce_prob) + (0.55 * h_score) + agreement_boost, 0.0), 1.0)

            updated_meta = dict(c.metadata)
            updated_meta["ce_logit"] = round(float(raw_logit), 4)
            updated_meta["ce_prob"] = round(ce_prob, 4)
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

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_candidates[:top_k]]

    def has_sufficient_evidence(self, top_chunk: RetrievedChunk) -> bool:
        if not top_chunk:
            return False

        v_score = float(top_chunk.metadata.get("vector_score", top_chunk.score or 0.0))
        r_score = float(top_chunk.metadata.get("rerank_score", top_chunk.score or 0.0))
        agreement = top_chunk.metadata.get("agreement_count", 1)

        if v_score >= 0.67:
            return True
        if v_score >= 0.64 and agreement >= 2 and r_score >= 0.67:
            return True
        return False
