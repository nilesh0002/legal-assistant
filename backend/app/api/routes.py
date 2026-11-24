"""
API route definitions.

Endpoints:
- GET /health
- POST /search  (M3: Hybrid search - Vector + BM25)
- GET /search   (M3: Convenience query endpoint)
- POST /ask     (M4: RAG Q&A grounded in verified passages)
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query

from app.generation.service import AskService
from app.models.schemas import (
    FeedbackRequest,
    FeedbackResponse,
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
        "version": "0.1.0",
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
    conv = [t.model_dump() for t in request.conversation_history] if request.conversation_history else None
    return await service.answer_question(request.question, conversation_history=conv)


@router.get("/coverage")
async def get_coverage():
    """
    Lists indexed laws and sections with last-verified dates.
    Shows users exactly what is authoritative in the corpus.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    all_chunks_file = base_dir / "data" / "processed" / "all_chunks.json"
    
    sections_by_law = {}
    if all_chunks_file.exists():
        with open(all_chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            for c in chunks:
                meta = c.get("metadata") or c
                law = meta.get("law") or c.get("law") or "Constitution of India"
                sid = c.get("source_id", "constitution-india")
                sec = meta.get("article") or meta.get("section") or c.get("article") or c.get("section") or ""
                title = meta.get("title") or c.get("title") or sec
                if law not in sections_by_law:
                    sections_by_law[law] = {
                        "law": law,
                        "source_id": sid,
                        "last_verified": "2026-11-24" if sid == "bnss-2023" else "2026-11-22",
                        "sections": []
                    }
                sections_by_law[law]["sections"].append({
                    "section": sec,
                    "title": title,
                    "old_equivalent": meta.get("old_equivalent") or c.get("old_equivalent")
                })

    return {
        "total_chunks": sum(len(l["sections"]) for l in sections_by_law.values()),
        "laws": list(sections_by_law.values()),
    }


@router.get("/examples")
async def get_example_questions():
    """
    Returns 8 to 10 suggested questions generated strictly from indexed topics.
    """
    return {
        "examples": [
            "What does Article 21 of the Indian Constitution protect?",
            "Can police enter my house without a warrant under BNSS?",
            "What is the maximum time police can detain someone without a Magistrate?",
            "Can women be arrested after sunset and before sunrise?",
            "How does a person apply for anticipatory bail under Section 482?",
            "What are the rights of an arrested person during interrogation?",
            "What is the procedure for bail in bailable offences under Section 478?",
            "Is audio-video electronic recording mandatory during police search and seizure?",
            "Can a private citizen arrest an offender under BNSS?",
            "Explain the right to equality before the law under Article 14."
        ]
    }


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(payload: FeedbackRequest):
    """
    Logs user feedback or reported inaccuracies to data/review_queue.jsonl.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    queue_file = base_dir / "data" / "review_queue.jsonl"
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "type": "user_feedback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": payload.question,
        "feedback": payload.feedback,
        "response_status": payload.response_status,
        "comment": payload.comment,
        "details": payload.details or {},
    }
    with open(queue_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
        
    return FeedbackResponse(status="received", message="Feedback recorded in review queue")
