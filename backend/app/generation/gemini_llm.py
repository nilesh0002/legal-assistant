"""
Google Gemini LLM wrapper implementing BaseLLM.
Features exponential backoff retry on HTTP 503 / 429 errors.
"""

import asyncio
import json
import os
from typing import List, Optional
import httpx

from app.generation.base import BaseLLM
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models.schemas import AnswerStatus, LegalResponse
from app.retrieval.base import RetrievedChunk


class UpstreamServiceError(Exception):
    """Raised when an external LLM provider encounters a transient or server failure."""
    pass


class GeminiLLM(BaseLLM):
    """
    Google Gemini LLM wrapper.
    Features automatic retry with exponential backoff on 503 and 429 errors.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

    async def is_available(self) -> bool:
        """Available if a non-placeholder API key is configured."""
        return bool(
            self.api_key
            and self.api_key.strip()
            and self.api_key not in ("your-api-key-here", "placeholder", "")
        )

    async def generate(
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
    ) -> LegalResponse:
        if not await self.is_available():
            raise UpstreamServiceError("Gemini API key is not configured in .env")

        if not context_chunks:
            return LegalResponse(
                status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                question=question,
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        user_content = build_user_prompt(question, context_chunks)

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_content}]}
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0,  # Strict deterministic grounding
            },
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)

                # Retry on 503 Service Unavailable or 429 Rate Limit
                if resp.status_code in (503, 429):
                    last_error = f"HTTP {resp.status_code}: {resp.text[:120]}"
                    if attempt < self.max_retries:
                        backoff = 1.0 * (2 ** attempt)
                        await asyncio.sleep(backoff)
                        continue
                    raise UpstreamServiceError(f"Gemini service unavailable after {self.max_retries} retries ({last_error})")

                if resp.status_code != 200:
                    raise UpstreamServiceError(f"Gemini API error ({resp.status_code}): {resp.text[:120]}")

                data = resp.json()
                candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(candidate_text)
                return LegalResponse(**parsed)

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = str(net_err)
                if attempt < self.max_retries:
                    backoff = 1.0 * (2 ** attempt)
                    await asyncio.sleep(backoff)
                    continue
                raise UpstreamServiceError(f"Gemini network error after retries: {last_error}")

        raise UpstreamServiceError(f"Gemini failed after {self.max_retries} attempts: {last_error}")
