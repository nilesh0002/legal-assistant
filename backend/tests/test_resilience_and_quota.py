"""
Tests for multi-provider LLM fallback (Gemini -> Groq -> LocalGroundedLLM),
Groq rate-limit header tracking, /ask response caching, and GET /quota.
"""

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient

from app.generation.factory import ResilientLLMProvider
from app.generation.gemini_llm import GeminiLLM, UpstreamServiceError
from app.generation.groq_llm import GroqLLM
from app.generation.local_llm import LocalGroundedLLM
from app.generation.service import AskService, _RESPONSE_CACHE
from app.main import app
from app.models.schemas import AnswerStatus
from app.retrieval.base import RetrievedChunk


def _sample_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="bns-2023_s131",
        source_id="bns-2023",
        text=(
            "131. Whoever assaults or uses criminal force to any person otherwise than on grave "
            "and sudden provocation given by that person, shall be punished with imprisonment "
            "of either description for a term which may extend to three months, or with fine "
            "which may extend to one thousand rupees, or with both."
        ),
        metadata={
            "law": "Bharatiya Nyaya Sanhita, 2023",
            "section": "Section 131",
            "title": "Section 131: Punishment for assault or criminal force otherwise than on grave provocation",
            "source_url": "https://egazette.gov.in/bns_2023.pdf",
            "vector_score": 0.85,
            "rerank_score": 0.85,
        },
        score=0.85,
    )


def test_gemini_defaults_to_flash_lite(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    g = GeminiLLM(api_key="test-key")
    assert g.model_name == "gemini-2.5-flash-lite"


def test_groq_records_rate_limit_headers():
    groq = GroqLLM(api_key="test-groq-key")
    headers = httpx.Headers({
        "x-ratelimit-remaining-requests": "14399",
        "x-ratelimit-limit-requests": "14400",
        "x-ratelimit-remaining-tokens": "5980",
        "x-ratelimit-limit-tokens": "6000",
        "x-ratelimit-reset-requests": "1s",
    })
    groq._record_rate_limits(headers)
    assert groq.last_rate_limits["remaining_requests"] == "14399"
    assert groq.last_rate_limits["remaining_tokens"] == "5980"


@pytest.mark.asyncio
async def test_resilient_provider_falls_back_gemini_to_groq_to_local():
    chunk = _sample_chunk()
    local = LocalGroundedLLM()
    valid_local_resp = await local.generate("What is punishment for assault?", [chunk])

    gemini = MagicMock(spec=GeminiLLM)
    gemini.is_available = AsyncMock(return_value=True)
    gemini.generate = AsyncMock(side_effect=UpstreamServiceError("429 quota exceeded"))
    gemini.rewrite_search_queries = AsyncMock(return_value=[])

    groq = MagicMock(spec=GroqLLM)
    groq.is_available = AsyncMock(return_value=True)
    groq.last_rate_limits = {"remaining_requests": "100"}
    groq.generate = AsyncMock(return_value=valid_local_resp)
    groq.rewrite_search_queries = AsyncMock(return_value=["punishment for assault criminal force"])

    provider = ResilientLLMProvider(gemini=gemini, groq=groq, local=local)

    rewrites = await provider.rewrite_search_queries("someone slapped me")
    assert rewrites == ["punishment for assault criminal force"]

    resp = await provider.generate("What is punishment for assault?", [chunk])
    assert resp.status == AnswerStatus.ANSWERED
    assert groq.generate.await_count == 1

    # If Groq also fails, falls back to LocalGroundedLLM
    groq.generate = AsyncMock(side_effect=UpstreamServiceError("429 groq limit"))
    resp2 = await provider.generate("What is punishment for assault?", [chunk])
    assert resp2.status == AnswerStatus.ANSWERED


@pytest.mark.asyncio
async def test_ask_service_caches_repeated_answered_queries():
    _RESPONSE_CACHE.clear()
    chunk = _sample_chunk()
    retriever = MagicMock()
    retriever.search = AsyncMock(return_value=[chunk])

    local = LocalGroundedLLM()
    spy_llm = MagicMock()
    spy_llm.generate = AsyncMock(side_effect=local.generate)

    svc = AskService(retriever=retriever, llm=spy_llm)
    r1 = await svc.answer_question("What is the punishment for slapping someone?")
    r2 = await svc.answer_question("  what is the punishment   for slapping someone? ")

    assert r1.status == AnswerStatus.ANSWERED
    assert r2.status == AnswerStatus.ANSWERED
    assert spy_llm.generate.await_count == 1


def test_quota_endpoint_exposes_stats_without_secrets():
    client = TestClient(app)
    resp = client.get("/quota")
    assert resp.status_code == 200
    body = resp.json()
    assert "providers" in body
    assert "cache" in body
    assert "gemini_configured" in body["providers"]
    assert "groq_configured" in body["providers"]
    assert "gemini_model" in body["providers"]
    # Never leak actual API key values
    serialized = str(body)
    assert "AIza" not in serialized
    assert "gsk_" not in serialized
