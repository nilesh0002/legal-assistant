"""
Indian Legal Knowledge Assistant — Backend Entry Point

A RAG-based legal Q&A service that answers questions about Indian law
using ONLY approved, verified sources.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Indian Legal Knowledge Assistant",
    description=(
        "RAG-based legal Q&A backed by approved Indian legal sources. "
        "Every answer is grounded in retrieved passages and validated "
        "before being returned."
    ),
    version="0.1.0",
)

# Allow the Android app (and local dev tools) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this before any public deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
