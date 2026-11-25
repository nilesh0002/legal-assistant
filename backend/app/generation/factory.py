"""
Factory and Resilient Multi-tier LLM Provider.
Enforces the mandatory cascading chain:
  Gemini (default with backoff retry on 503/429) -> Groq -> Ollama -> Local grounded generator (last resort)
Ensures every generation is validated by the M5 validator.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from app.generation.base import BaseLLM
from app.generation.gemini_llm import GeminiLLM, UpstreamServiceError
from app.generation.groq_llm import GroqLLM
from app.generation.local_llm import LocalGroundedLLM
from app.generation.ollama_llm import OllamaLLM
from app.models.schemas import AnswerStatus, LegalResponse
from app.retrieval.base import RetrievedChunk
from app.validation.validator import LegalResponseValidator

load_dotenv()

_PROVIDER_STATS: Dict[str, Any] = {
    "gemini_calls": 0,
    "groq_calls": 0,
    "ollama_calls": 0,
    "local_fallbacks": 0,
    "last_groq_rate_limits": {},
}


def get_provider_stats() -> Dict[str, Any]:
    """Return live provider usage counters and last-seen Groq rate limit headers."""
    return {
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        **_PROVIDER_STATS,
    }


class ResilientLLMProvider(BaseLLM):
    """
    Orchestrates LLM generation with automatic failover and M5 validation.
    Hierarchy:
      1. Gemini (with exponential backoff on 503 / 429)
      2. Groq (high-rate-limit OpenAI-compatible fallback)
      3. Ollama (local server)
      4. LocalGroundedLLM (deterministic offline fallback)
    """

    def __init__(
        self,
        gemini: Optional[GeminiLLM] = None,
        groq: Optional[GroqLLM] = None,
        ollama: Optional[OllamaLLM] = None,
        local: Optional[LocalGroundedLLM] = None,
        validator: Optional[LegalResponseValidator] = None,
    ):
        self.gemini = gemini or GeminiLLM()
        self.groq = groq or GroqLLM()
        self.ollama = ollama or OllamaLLM()
        self.local = local or LocalGroundedLLM()
        self.validator = validator or LegalResponseValidator()

    async def is_available(self) -> bool:
        return True

    async def rewrite_search_queries(self, question: str) -> List[str]:
        """Forward lay-to-legal query rewriting to Gemini, then Groq, else empty (rule fallback)."""
        if await self.gemini.is_available():
            rewrites = await self.gemini.rewrite_search_queries(question)
            if rewrites:
                return rewrites
        if await self.groq.is_available():
            rewrites = await self.groq.rewrite_search_queries(question)
            if self.groq.last_rate_limits:
                _PROVIDER_STATS["last_groq_rate_limits"] = dict(self.groq.last_rate_limits)
            if rewrites:
                return rewrites
        return []

    async def generate(
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
    ) -> LegalResponse:
        # Tier 1: Try Gemini if available
        if await self.gemini.is_available():
            try:
                _PROVIDER_STATS["gemini_calls"] += 1
                resp = await self.gemini.generate(question, context_chunks)
                val = self.validator.validate(resp, context_chunks)
                if val.is_valid:
                    return resp
                # Retry once if validation failed
                resp = await self.gemini.generate(question, context_chunks)
                val = self.validator.validate(resp, context_chunks)
                if val.is_valid:
                    return resp
                print(f"[ResilientLLM] Gemini response failed validation ({val.errors}). Falling back.")
            except UpstreamServiceError as err:
                print(f"[ResilientLLM] Gemini error ({err}). Falling back to Groq / Ollama / Local.")
            except Exception as e:
                print(f"[ResilientLLM] Unexpected Gemini failure: {e}. Falling back.")

        # Tier 2: Try Groq if available
        if await self.groq.is_available():
            try:
                _PROVIDER_STATS["groq_calls"] += 1
                resp = await self.groq.generate(question, context_chunks)
                if self.groq.last_rate_limits:
                    _PROVIDER_STATS["last_groq_rate_limits"] = dict(self.groq.last_rate_limits)
                val = self.validator.validate(resp, context_chunks)
                if val.is_valid:
                    return resp
                resp = await self.groq.generate(question, context_chunks)
                if self.groq.last_rate_limits:
                    _PROVIDER_STATS["last_groq_rate_limits"] = dict(self.groq.last_rate_limits)
                val = self.validator.validate(resp, context_chunks)
                if val.is_valid:
                    return resp
                print(f"[ResilientLLM] Groq response failed validation ({val.errors}). Falling back.")
            except UpstreamServiceError as err:
                if self.groq.last_rate_limits:
                    _PROVIDER_STATS["last_groq_rate_limits"] = dict(self.groq.last_rate_limits)
                print(f"[ResilientLLM] Groq error ({err}). Falling back to Ollama / Local.")
            except Exception as e:
                print(f"[ResilientLLM] Unexpected Groq failure: {e}. Falling back.")

        # Tier 3: Try Ollama if available
        if await self.ollama.is_available():
            try:
                _PROVIDER_STATS["ollama_calls"] += 1
                resp = await self.ollama.generate(question, context_chunks)
                val = self.validator.validate(resp, context_chunks)
                if val.is_valid:
                    return resp
                # Retry once
                resp = await self.ollama.generate(question, context_chunks)
                val = self.validator.validate(resp, context_chunks)
                if val.is_valid:
                    return resp
                print(f"[ResilientLLM] Ollama response failed validation ({val.errors}). Falling back to Local.")
            except UpstreamServiceError as err:
                print(f"[ResilientLLM] Ollama error ({err}). Falling back to Local.")
            except Exception as e:
                print(f"[ResilientLLM] Unexpected Ollama failure: {e}. Falling back.")

        # Tier 4: Deterministic Local Grounded Generator (last resort)
        _PROVIDER_STATS["local_fallbacks"] += 1
        resp = await self.local.generate(question, context_chunks)
        val = self.validator.validate(resp, context_chunks)
        if val.is_valid:
            return resp

        # If even local output fails validation, return insufficient_evidence
        return LegalResponse(
            status=AnswerStatus.INSUFFICIENT_EVIDENCE,
            question=question,
            key_points=["All candidate answers failed M5 source validation: " + "; ".join(val.errors)],
            disclaimer="General information, not legal advice.",
        )


async def get_llm_provider(preferred: Optional[str] = None) -> BaseLLM:
    """
    Returns the configured LLM provider.
    Defaults to the ResilientLLMProvider ensuring real LLM first with fallback.
    """
    pref = (preferred or os.getenv("LLM_PROVIDER", "resilient")).lower()

    if pref == "local":
        return LocalGroundedLLM()
    elif pref == "ollama":
        ollama = OllamaLLM()
        if await ollama.is_available():
            return ollama
        print("[LLMFactory] Ollama requested but unavailable. Falling back to resilient provider.")

    return ResilientLLMProvider()
