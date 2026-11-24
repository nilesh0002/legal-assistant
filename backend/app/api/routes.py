"""
API route definitions.

Endpoints:
- GET /health
- POST /search  (M3: Hybrid search - Vector + BM25)
- GET /search   (M3: Convenience query endpoint)
- POST /ask     (M4: RAG Q&A grounded in verified passages)
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query

from app.generation.service import AskService
from app.models.schemas import (
    LegalResponse,
    QuestionRequest,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.retrieval.hybrid import HybridRetriever

router = APIRouter()

# Singleton service instances
_hybrid_retriever: Optional[HybridRetriever] = None
_ask_service: Optional[AskService] = None


def get_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever


def get_ask_service() -> AskService:
    global _ask_service
    if _ask_service is None:
        _ask_service = AskService(retriever=get_retriever())
    return _ask_service


@router.get("/health")
async def health_check():
    """
    Returns service status. The Android app calls this on startup
    to confirm the backend is reachable.
    """
    return {
        "status": "healthy",
        "service": "Indian Legal Knowledge Assistant",
        "version": "0.2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Hybrid search across approved legal corpus using dense vector embeddings (Chroma + BGE)
    and sparse keyword indexing (BM25) fused via Reciprocal Rank Fusion (RRF).
    """
    retriever = get_retriever()
    chunks = await retriever.search(
        query=request.query,
        top_k=request.top_k,
        min_score=request.min_score,
    )

    items = [
        SearchResultItem(
            chunk_id=c.chunk_id,
            source_id=c.source_id,
            score=c.score,
            law=c.metadata.get("law", "Constitution of India"),
            article=c.metadata.get("article", ""),
            title=c.metadata.get("title", ""),
            text=c.text,
            location=c.metadata.get("location", ""),
            subheading=c.metadata.get("subheading", ""),
            metadata=c.metadata,
        )
        for c in chunks
    ]

    return SearchResponse(
        query=request.query,
        total_results=len(items),
        results=items,
    )


@router.get("/search", response_model=SearchResponse)
async def search_documents_get(
    q: str = Query(..., min_length=2, description="Legal search query"),
    top_k: int = Query(default=5, ge=1, le=20),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """Convenience GET endpoint for browser queries and fast testing."""
    return await search_documents(SearchRequest(query=q, top_k=top_k, min_score=min_score))


@router.post("/ask", response_model=LegalResponse)
async def ask_legal_question(request: QuestionRequest):
    """
    RAG legal Q&A endpoint:
    1. Checks if question is within legal scope.
    2. Retrieves verified passages from approved corpus.
    3. Checks evidence threshold (refuses to answer if evidence is lacking).
    4. Generates two-layer answer grounded in passages with citations and quotes.
    5. Returns structured JSON with mandatory legal disclaimer.
    """
    service = get_ask_service()
    return await service.answer_question(request.question)
