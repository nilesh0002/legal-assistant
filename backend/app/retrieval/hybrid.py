"""
Hybrid retriever fusing dense vector search (Chroma) and sparse keyword search (BM25).
Uses Reciprocal Rank Fusion (RRF) to combine ranks, preserving underlying vector
and keyword metrics for confidence gating.
"""

from typing import Dict, List, Optional
from app.retrieval.base import BaseRetriever, RetrievedChunk
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.chroma_retriever import ChromaRetriever


class HybridRetriever(BaseRetriever):
    """
    Combines dense semantic search (Chroma + BGE) and sparse lexical search (BM25).
    Guarantees both conceptual matching ('right to live with dignity' -> Art 21)
    and exact keyword/article lookup ('Article 21A', 'untouchability' -> Art 17).
    """

    def __init__(
        self,
        vector_retriever: Optional[ChromaRetriever] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        self.vector_retriever = vector_retriever or ChromaRetriever()
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

    async def document_count(self) -> int:
        return await self.vector_retriever.document_count()

    async def add_documents(self, chunks: List[dict]) -> int:
        v_count = await self.vector_retriever.add_documents(chunks)
        b_count = await self.bm25_retriever.add_documents(chunks)
        return max(v_count, b_count)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        # Query both retrievers with candidate pool size
        fetch_k = max(top_k * 3, 15)

        vector_results = await self.vector_retriever.search(query, top_k=fetch_k)
        bm25_results = await self.bm25_retriever.search(query, top_k=fetch_k)

        # Map chunk_id -> chunk data and metrics
        chunk_map: Dict[str, RetrievedChunk] = {}
        rrf_scores: Dict[str, float] = {}
        vector_scores: Dict[str, float] = {}
        bm25_scores: Dict[str, float] = {}

        # 1. Process vector ranks
        for rank, chunk in enumerate(vector_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            vector_scores[cid] = chunk.score
            score = self.vector_weight / (self.rrf_k + rank + 1)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        # 2. Process BM25 ranks
        for rank, chunk in enumerate(bm25_results):
            cid = chunk.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = chunk
            bm25_scores[cid] = chunk.score
            score = self.bm25_weight / (self.rrf_k + rank + 1)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        # Max theoretical score for rank 1 in both: (v_weight / (k+1)) + (b_weight / (k+1))
        max_possible_rrf = (self.vector_weight + self.bm25_weight) / (self.rrf_k + 1)

        fused: List[RetrievedChunk] = []
        for cid, raw_rrf in rrf_scores.items():
            normalized_score = float(min(1.0, raw_rrf / max_possible_rrf))
            if normalized_score >= min_score:
                base_chunk = chunk_map[cid]
                v_score = vector_scores.get(cid, 0.0)
                b_score = bm25_scores.get(cid, 0.0)

                fused.append(
                    RetrievedChunk(
                        chunk_id=base_chunk.chunk_id,
                        source_id=base_chunk.source_id,
                        text=base_chunk.text,
                        score=round(normalized_score, 4),
                        metadata={
                            **base_chunk.metadata,
                            "rrf_score": round(raw_rrf, 6),
                            "vector_score": round(v_score, 4),
                            "bm25_score": round(b_score, 4),
                            "retrieval_mode": "hybrid",
                        },
                    )
                )

        # Sort descending by fused score
        fused.sort(key=lambda x: x.score, reverse=True)
        return fused[:top_k]
