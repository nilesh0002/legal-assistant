"""
Abstract retrieval interface.

Any retriever (Chroma, Elasticsearch, etc.) implements this.
The rest of the app depends only on this interface, so you can
swap the vector DB without touching anything else.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class RetrievedChunk:
    """A single chunk returned by the retriever."""
    chunk_id: str
    source_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)  # law, section, article, page, etc.


class BaseRetriever(ABC):
    """
    Interface that every retriever must implement.

    Why an interface? The brief says:
      "Keep the LLM, embeddings and vector DB behind interfaces
       so I can swap them later."
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        """Return the top-k most relevant chunks for the query."""
        ...

    @abstractmethod
    async def add_documents(
        self,
        chunks: List[dict],
    ) -> int:
        """Index a batch of chunks. Returns the count added."""
        ...

    @abstractmethod
    async def document_count(self) -> int:
        """How many chunks are currently indexed."""
        ...
