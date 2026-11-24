"""
M2 Tests: Verify vector database indexing and semantic retrieval.
"""

import pytest
from pathlib import Path
from app.retrieval.base import BaseRetriever, RetrievedChunk
from app.retrieval.chroma_retriever import ChromaRetriever
from app.retrieval.embeddings import BaseEmbeddingModel, FastEmbedBGE

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


def test_chroma_directory_exists():
    """Chroma database files must exist on disk."""
    assert CHROMA_DIR.exists(), f"Chroma directory {CHROMA_DIR} not found"


def test_embedding_model_bge():
    """Verify BGE embedding model generates correct vector dimension."""
    embedder = FastEmbedBGE()
    assert isinstance(embedder, BaseEmbeddingModel)
    assert embedder.dimension == 384

    query_emb = embedder.embed_query("What are fundamental rights?")
    assert len(query_emb) == 384
    assert isinstance(query_emb[0], float)

    texts_emb = embedder.embed_texts(["Right to life", "Equality before law"])
    assert len(texts_emb) == 2
    assert len(texts_emb[0]) == 384
    assert len(texts_emb[1]) == 384


@pytest.mark.asyncio
async def test_retriever_is_base_retriever():
    """ChromaRetriever must strictly implement BaseRetriever."""
    retriever = ChromaRetriever()
    assert isinstance(retriever, BaseRetriever)


@pytest.mark.asyncio
async def test_document_count_in_chroma():
    """Chroma collection must contain all 31 chunks (Preamble + Part III)."""
    retriever = ChromaRetriever()
    count = await retriever.document_count()
    assert count >= 31, f"Expected at least 31 indexed chunks, found {count}"


@pytest.mark.asyncio
async def test_semantic_retrieval_article_21():
    """Querying about life and personal liberty should return Article 21 top-ranked."""
    retriever = ChromaRetriever()
    results = await retriever.search("deprived of life or personal liberty", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert isinstance(top, RetrievedChunk)
    assert top.chunk_id == "constitution-art-21"
    assert top.source_id == "constitution-india"
    assert "personal liberty" in top.text.lower()
    assert top.score > 0.70


@pytest.mark.asyncio
async def test_semantic_retrieval_article_14():
    """Querying about equality before law should retrieve Article 14 top-ranked."""
    retriever = ChromaRetriever()
    results = await retriever.search("equality before law equal protection", top_k=3)
    assert len(results) > 0
    assert results[0].chunk_id == "constitution-art-14"
    assert "equality before the law" in results[0].text.lower()


@pytest.mark.asyncio
async def test_semantic_retrieval_article_17():
    """Querying about untouchability abolition should retrieve Article 17."""
    retriever = ChromaRetriever()
    results = await retriever.search("abolition of untouchability", top_k=3)
    assert len(results) > 0
    assert results[0].chunk_id == "constitution-art-17"


@pytest.mark.asyncio
async def test_semantic_retrieval_article_21a():
    """Querying about right to education for children should retrieve Article 21A."""
    retriever = ChromaRetriever()
    results = await retriever.search("free and compulsory education children age six to fourteen", top_k=3)
    assert len(results) > 0
    assert results[0].chunk_id == "constitution-art-21a"
