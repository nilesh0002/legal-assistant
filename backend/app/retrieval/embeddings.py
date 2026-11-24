"""
Abstract and concrete embedding model implementations.
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingModel(ABC):
    """Abstract interface for text embeddings."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of texts."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Compute embedding for a single search query."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        ...


class FastEmbedBGE(BaseEmbeddingModel):
    """
    Local BGE embedding model using fastembed (ONNX runtime).
    Default: BAAI/bge-small-en-v1.5 (dimension: 384).
    Upgrade path: BAAI/bge-m3 for multilingual (Hindi) support.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)
        # Determine dimension
        sample = list(self._model.embed(["test"]))
        self._dimension = len(sample[0])

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = list(self._model.embed(texts))
        return [e.tolist() for e in embeddings]

    def embed_query(self, query: str) -> List[float]:
        # BGE recommends adding query prefix or direct embedding
        embeddings = list(self._model.embed([query]))
        return embeddings[0].tolist()

    @property
    def dimension(self) -> int:
        return self._dimension
