"""
Indian Legal Knowledge Assistant — Backend Entry Point

A RAG-based legal Q&A service that answers questions about Indian law
using ONLY approved, verified sources.
"""

from contextlib import asynccontextmanager
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.retrieval.chroma_retriever import ChromaRetriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure vector index is populated on startup
    try:
        retriever = ChromaRetriever()
        count = await retriever.document_count()
        if count == 0:
            base_dir = Path(__file__).resolve().parent.parent
            chunks_path = base_dir / "data" / "processed" / "all_chunks.json"
            if chunks_path.exists():
                with open(chunks_path, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                await retriever.add_documents(chunks)
                print(f"[Startup] Initialized Chroma with {len(chunks)} chunks.")
    except Exception as e:
        print(f"[Startup Warning] Could not verify/initialize Chroma: {e}")
    yield


app = FastAPI(
    title="Indian Legal Knowledge Assistant",
    description=(
        "RAG-based legal Q&A backed by approved Indian legal sources. "
        "Every answer is grounded in retrieved passages and validated "
        "before being returned."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the Android app (and local dev tools) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
