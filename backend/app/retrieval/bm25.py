"""
BM25 sparse keyword search implementation over legal chunks.
Supports both Constitution (Articles) and BNSS (Sections).
"""

import json
import re
from pathlib import Path
from typing import List, Optional
from rank_bm25 import BM25Okapi

from app.retrieval.base import BaseRetriever, RetrievedChunk

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ALL_CHUNKS = BASE_DIR / "data" / "processed" / "all_chunks.json"
FALLBACK_CHUNKS = BASE_DIR / "data" / "processed" / "constitution_chunks.json"


def tokenize(text: str) -> List[str]:
    """Basic lowercased word tokenization for keyword matching."""
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


class BM25Retriever(BaseRetriever):
    """
    Keyword-based sparse retriever using BM25Okapi.
    Excels at exact section/article numbers, legal terminology, and unique words
    (e.g., 'untouchability', 'habeas corpus', 'Article 21A', 'Section 35', 'bail').
    """

    def __init__(self, chunks_path: Optional[Path] = None):
        if chunks_path is not None:
            self.chunks_path = chunks_path
        elif ALL_CHUNKS.exists():
            self.chunks_path = ALL_CHUNKS
        else:
            self.chunks_path = FALLBACK_CHUNKS

        self.chunks: List[dict] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

        if self.chunks_path.exists():
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
            self._build_index()

    def _build_index(self):
        self.tokenized_corpus = []
        for c in self.chunks:
            # Index article, section, title, subheading, old equivalent, and full text
            full_searchable = (
                f"{c.get('article', '')} {c.get('section', '')} {c.get('title', '')} "
                f"{c.get('subheading', '')} {c.get('old_equivalent', '')} {c.get('text', '')}"
            )
            self.tokenized_corpus.append(tokenize(full_searchable))
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    async def document_count(self) -> int:
        return len(self.chunks)

    async def add_documents(self, chunks: List[dict]) -> int:
        self.chunks.extend(chunks)
        self._build_index()
        return len(chunks)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        if not self.bm25 or not self.chunks:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0

        # Rank documents
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results: List[RetrievedChunk] = []
        for idx in ranked_indices[:top_k]:
            raw_score = scores[idx]
            if raw_score <= 0.0:
                continue
            normalized_score = float(raw_score / max_score)
            if normalized_score >= min_score:
                c = self.chunks[idx]
                results.append(
                    RetrievedChunk(
                        chunk_id=c.get("chunk_id", ""),
                        source_id=c.get("source_id", "constitution-india"),
                        text=c.get("text", ""),
                        score=normalized_score,
                        metadata={
                            "source_id": c.get("source_id", "constitution-india"),
                            "law": c.get("law", ""),
                            "part": c.get("part", ""),
                            "part_title": c.get("part_title", ""),
                            "article": c.get("article", ""),
                            "section": c.get("section", ""),
                            "title": c.get("title", ""),
                            "location": c.get("location", ""),
                            "subheading": c.get("subheading", ""),
                            "old_equivalent": c.get("old_equivalent", ""),
                            "bm25_raw_score": float(raw_score),
                        },
                    )
                )

        return results
