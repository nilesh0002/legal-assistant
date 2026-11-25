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

    async def rewrite_search_queries(self, question: str) -> List[str]:
        """Rewrite a lay question into 2-3 legal search queries (search only, never answer content)."""
        prompt = (
            "Rewrite the following citizen question about Indian law into 2 to 3 concise "
            "statutory search queries using formal legal terms. Do NOT answer the question. "
            "Output a JSON array of strings only.\n\nQuestion: " + question
        )
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.0},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    arr = json.loads(data["response"])
                    if isinstance(arr, list):
                        return [str(x) for x in arr[:3]]
        except Exception:
            pass
        return []
