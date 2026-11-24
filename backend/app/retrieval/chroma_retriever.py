"""
Chroma vector database retriever implementing BaseRetriever.
"""

from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings

from app.retrieval.base import BaseRetriever, RetrievedChunk
from app.retrieval.embeddings import BaseEmbeddingModel, FastEmbedBGE


class ChromaRetriever(BaseRetriever):
    """
    Chroma-backed persistent vector store.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "legal_corpus",
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ):
        if persist_directory is None:
            # Default to backend/data/chroma_db
            base = Path(__file__).resolve().parent.parent.parent
            self.persist_directory = str(base / "data" / "chroma_db")
        else:
            self.persist_directory = persist_directory

        self.collection_name = collection_name
        self.embedding_model = embedding_model or FastEmbedBGE()

        self._client = chromadb.PersistentClient(path=self.persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def document_count(self) -> int:
        return self._collection.count()

    async def add_documents(self, chunks: List[dict]) -> int:
        """
        Index chunks into the Chroma collection.
        Each chunk dict must contain:
          chunk_id, source_id, text, law, article, title, location, etc.
        """
        if not chunks:
            return 0

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        
        # Prepare metadata (flat dict only for Chroma)
        metadatas = []
        for c in chunks:
            meta = {
                "source_id": c.get("source_id", ""),
                "law": c.get("law", ""),
                "part": c.get("part", ""),
                "part_title": c.get("part_title", ""),
                "article": c.get("article", ""),
                "section": c.get("section", ""),
                "old_equivalent": c.get("old_equivalent", "") or "",
                "title": c.get("title", ""),
                "location": c.get("location", ""),
                "subheading": c.get("subheading", ""),
            }
            metadatas.append(meta)

        # Generate embeddings
        embeddings = self.embedding_model.embed_texts(documents)

        # Upsert into Chroma
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        """
        Query Chroma by vector cosine similarity.
        Cosine distance d in [0, 2] -> score = 1 - d (or 1 - d/2).
        For normalized vectors with cosine space, score = 1.0 - distance.
        """
        query_embedding = self.embedding_model.embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        chunks: List[RetrievedChunk] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return chunks

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            # Cosine similarity score
            score = 1.0 - dist
            if score >= min_score:
                chunks.append(
                    RetrievedChunk(
                        chunk_id=chunk_id,
                        source_id=meta.get("source_id", "constitution-india"),
                        text=doc,
                        score=float(score),
                        metadata=meta,
                    )
                )

        # Sort descending by score
        chunks.sort(key=lambda x: x.score, reverse=True)
        return chunks
