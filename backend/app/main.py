"""
Indian Legal Knowledge Assistant — Backend Entry Point

A RAG-based legal Q&A service that answers questions about Indian law
using ONLY approved, verified sources.
"""

from contextlib import asynccontextmanager
import json
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi.staticfiles import StaticFiles
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

_ip_request_counts = {}
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ["/ask", "/search"]:
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        timestamps = _ip_request_counts.get(client_ip, [])
        timestamps = [t for t in timestamps if t > window_start]
        if len(timestamps) >= MAX_REQUESTS_PER_WINDOW:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait a minute before querying again."}
            )
        timestamps.append(now)
        _ip_request_counts[client_ip] = timestamps
    return await call_next(request)

app.include_router(router)

# Mount Web frontend
web_dir = Path(__file__).resolve().parent.parent / "web"
if not web_dir.exists():
    web_dir = Path(__file__).resolve().parent.parent.parent / "web"

if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
