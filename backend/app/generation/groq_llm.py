"""
Groq LLM wrapper implementing BaseLLM via OpenAI-compatible Chat Completions API.
Provides a high-rate-limit secondary fallback and exposes remaining rate-limit headers.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional
import httpx

from app.generation.base import BaseLLM
from app.generation.gemini_llm import UpstreamServiceError
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models.schemas import AnswerStatus, LegalResponse
from app.retrieval.base import RetrievedChunk


class GroqLLM(BaseLLM):
    """
    Groq Chat Completions wrapper with exponential backoff on 429/503
    and live tracking of x-ratelimit-remaining-* response headers.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_name = model_name or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_rate_limits: Dict[str, Optional[str]] = {}

    async def is_available(self) -> bool:
        """Available if a non-placeholder GROQ_API_KEY is configured."""
        return bool(
            self.api_key
            and self.api_key.strip()
            and self.api_key not in ("your-api-key-here", "placeholder", "")
        )

    def _record_rate_limits(self, headers: httpx.Headers) -> None:
        self.last_rate_limits = {
            "remaining_requests": headers.get("x-ratelimit-remaining-requests"),
            "limit_requests": headers.get("x-ratelimit-limit-requests"),
            "remaining_tokens": headers.get("x-ratelimit-remaining-tokens"),
            "limit_tokens": headers.get("x-ratelimit-limit-tokens"),
            "reset_requests": headers.get("x-ratelimit-reset-requests"),
        }

    async def generate(
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
    ) -> LegalResponse:
        if not await self.is_available():
            raise UpstreamServiceError("GROQ_API_KEY is not configured")

        if not context_chunks:
            return LegalResponse(
                status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                question=question,
                key_points=["No retrieved legal sources provided for generation."],
                disclaimer="General information, not legal advice.",
            )

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, context_chunks)},
            ],
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)

                self._record_rate_limits(resp.headers)

                if resp.status_code in (503, 429):
                    last_error = f"HTTP {resp.status_code}: {resp.text[:120]}"
                    if attempt < self.max_retries:
                        await asyncio.sleep(1.0 * (2 ** attempt))
                        continue
                    raise UpstreamServiceError(f"Groq service unavailable after retries ({last_error})")

                if resp.status_code != 200:
                    raise UpstreamServiceError(f"Groq API error ({resp.status_code}): {resp.text[:120]}")

                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return LegalResponse(**parsed)

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = str(net_err)
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                    continue
                raise UpstreamServiceError(f"Groq network error after retries: {last_error}")

        raise UpstreamServiceError(f"Groq failed after {self.max_retries} attempts: {last_error}")

    async def rewrite_search_queries(self, question: str) -> List[str]:
        """Rewrite a lay question into 2-3 legal search queries (search only, never answer content)."""
        if not await self.is_available():
            return []
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Rewrite the following citizen question about Indian law into 2 to 3 concise "
                        "statutory search queries using formal legal terms. Do NOT answer the question. "
                        "Return JSON object {\"queries\": [\"...\"]}.\n\nQuestion: " + question
                    ),
                }
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                self._record_rate_limits(resp.headers)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    obj = json.loads(content)
                    arr = obj.get("queries", [])
                    if isinstance(arr, list):
                        return [str(x) for x in arr[:3] if str(x).strip()]
        except Exception:
            pass
        return []
