"""
Abstract LLM generation interface.

Any LLM (Gemini, Ollama, OpenAI, etc.) implements this.
The generation layer receives retrieved passages and must
produce an answer grounded ONLY in those passages.
"""

from abc import ABC, abstractmethod
from typing import List

from app.models.schemas import LegalResponse
from app.retrieval.base import RetrievedChunk


class BaseLLM(ABC):
    """
    Interface that every LLM wrapper must implement.

    The generate method receives the user question AND the retrieved
    context chunks.  The LLM must answer from those chunks only.
    """

    @abstractmethod
    async def generate(
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
    ) -> LegalResponse:
        """
        Generate an answer grounded in the provided context chunks.

        Returns a LegalResponse.  If the chunks don't contain enough
        information, the implementation MUST return status
        "insufficient_evidence" rather than guessing.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether the LLM backend is reachable."""
        ...
