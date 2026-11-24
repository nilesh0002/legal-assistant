"""
Ollama local model wrapper implementing BaseLLM.
"""

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


class OllamaLLM(BaseLLM):
    """
    Ollama local LLM runner (e.g., llama3.1, mistral, qwen).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.timeout = timeout

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
    ) -> LegalResponse:
        if not context_chunks:
            return LegalResponse(
                status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                question=question,
            )

        prompt = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(question, context_chunks)}"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.0},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code != 200:
                    raise UpstreamServiceError(f"Ollama error: HTTP {resp.status_code}")
                data = resp.json()
                parsed = json.loads(data["response"])
                return LegalResponse(**parsed)
        except Exception as e:
            raise UpstreamServiceError(f"Ollama generation failed: {e}")
