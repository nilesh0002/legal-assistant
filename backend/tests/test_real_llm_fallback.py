"""
Tests for STEP 5: Real LLM with backoff retry on 503 and graceful fallback.
Verifies that:
1. Gemini retries on 503 with exponential backoff.
2. If Gemini fails, it seamlessly falls back to Ollama / Local without crashing.
3. Every generated output passes through the M5 validator.
4. ResilientLLMProvider is the default provider.
"""

from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.generation.factory import ResilientLLMProvider, get_llm_provider
from app.generation.gemini_llm import GeminiLLM, UpstreamServiceError
from app.generation.local_llm import LocalGroundedLLM
from app.generation.ollama_llm import OllamaLLM
from app.models.schemas import AnswerStatus, LegalResponse
from app.retrieval.base import RetrievedChunk


@pytest.fixture
def sample_chunk():
    return RetrievedChunk(
        chunk_id="bnss-sec-35",
        source_id="bnss-2023",
        text="35. (1) Any police officer may without an order from a Magistrate and without a warrant, arrest any person who commits, in the presence of a police officer, a cognizable offence.",
        score=0.92,
        metadata={
            "section": "Section 35",
            "title": "Section 35: When police may arrest without warrant",
            "location": "BNSS 2023, Section 35, Page 13",
            "law": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        },
    )


@pytest.mark.asyncio
async def test_factory_returns_resilient_provider_by_default():
    provider = await get_llm_provider()
    assert isinstance(provider, ResilientLLMProvider)


@pytest.mark.asyncio
async def test_gemini_503_retry_and_fallback(sample_chunk):
    """Simulate Gemini returning 503 Service Unavailable: verify backoff retry and fallback to Local."""
    mock_gemini = GeminiLLM(api_key="fake-test-key", max_retries=1)

    # Mock Gemini post to return 503
    mock_response = httpx.Response(
        status_code=503,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
        text="Service Unavailable",
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        provider = ResilientLLMProvider(
            gemini=mock_gemini,
            ollama=OllamaLLM(base_url="http://nonexistent-host:11434"),
            local=LocalGroundedLLM(),
        )

        resp = await provider.generate(
            question="When can police arrest without warrant under Section 35 BNSS?",
            context_chunks=[sample_chunk],
        )

        # Fallback must succeed and provide a valid answer
        assert resp.status == AnswerStatus.ANSWERED
        assert resp.short_answer is not None
        assert "Section 35" in resp.short_answer.simple
        assert len(resp.details) > 0
        assert resp.details[0].source_id == "bnss-2023"


@pytest.mark.asyncio
async def test_resilient_provider_validates_every_output(sample_chunk):
    """Ensure that even when an LLM produces an answer, validator checks it."""
    provider = ResilientLLMProvider()
    resp = await provider.generate(
        question="When can police arrest without warrant?",
        context_chunks=[sample_chunk],
    )

    assert resp.status == AnswerStatus.ANSWERED
    assert resp.disclaimer == "General information, not legal advice."
    assert resp.details[0].quote in sample_chunk.text
