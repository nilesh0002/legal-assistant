"""
Indian Legal Knowledge Assistant — Backend Entry Point

A RAG-based legal Q&A service that answers questions about Indian law
using ONLY approved, verified sources.
"""

from contextlib import asynccontextmanager
import ipaddress
import json
import os
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

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

DEFAULT_ALLOWED_ORIGINS = [
    "https://legal-assistant-web-rho.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
]


def get_allowed_origins() -> list[str]:
    """Read allowed CORS origins from ALLOWED_ORIGINS env var; never allow '*' wildcard."""
    raw = os.getenv("ALLOWED_ORIGINS", "")
    if raw.strip():
        origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip() and o.strip() != "*"]
        if origins:
            return origins
    return list(DEFAULT_ALLOWED_ORIGINS)


def _is_trusted_proxy_ip(ip_str: str) -> bool:
    """Return True if the socket peer IP is a loopback, private proxy, or in-process testclient."""
    if ip_str == "testclient":
        return True
    try:
        addr = ipaddress.ip_address(ip_str)
        return addr.is_loopback or (addr.is_private and not addr.is_global)
    except ValueError:
        return False


def get_real_client_ip(request: Request) -> str:
    """
    Extract the real client IP behind Render/Cloudflare reverse proxies.
    Only trusts forwarded headers when the immediate socket peer is a trusted
    local/private proxy (or when TRUST_PROXY_HEADERS=true).
    """
    peer_ip = request.client.host if request.client else "127.0.0.1"
    trust_proxy = os.getenv("TRUST_PROXY_HEADERS", "true").lower() == "true"

    if trust_proxy and _is_trusted_proxy_ip(peer_ip):
        for header_name in ("cf-connecting-ip", "true-client-ip", "x-real-ip"):
            val = request.headers.get(header_name, "").strip()
            if val:
                return val

        xff = request.headers.get("x-forwarded-for", "").strip()
        if xff:
            first_ip = xff.split(",")[0].strip()
            if first_ip:
                return first_ip

    return peer_ip


# Allow only explicit Vercel and local dev origins (never wildcard '*')
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

_ip_request_counts = {}
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ["/ask", "/search"]:
        client_ip = get_real_client_ip(request)
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


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect browser visitors on the API root to the live Vercel Stitch web app."""
    frontend_url = os.getenv("FRONTEND_URL", "https://legal-assistant-web-rho.vercel.app").strip()
    return RedirectResponse(url=frontend_url, status_code=307)
