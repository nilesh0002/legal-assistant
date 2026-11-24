"""
Index parsed chunks from backend/data/processed into Chroma vector database.
"""

import asyncio
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.retrieval.chroma_retriever import ChromaRetriever

PROCESSED_CHUNKS = BASE_DIR / "data" / "processed" / "all_chunks.json"
FALLBACK_CHUNKS = BASE_DIR / "data" / "processed" / "constitution_chunks.json"


async def main():
    target_path = PROCESSED_CHUNKS if PROCESSED_CHUNKS.exists() else FALLBACK_CHUNKS
    if not target_path.exists():
        raise FileNotFoundError(f"Processed chunks not found at {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loading {len(chunks)} chunks into Chroma from {target_path.name}...")
    retriever = ChromaRetriever()
    count = await retriever.add_documents(chunks)
    total = await retriever.document_count()
    print(f"Successfully indexed {count} chunks into Chroma! Total count in collection: {total}")

    # Smoke search test 1: Constitution
    test_query_1 = "What is the protection of life and personal liberty?"
    print(f"\nRunning test query 1: '{test_query_1}'")
    top_results = await retriever.search(test_query_1, top_k=2)
    for idx, r in enumerate(top_results, 1):
        provision = r.metadata.get('article') or r.metadata.get('section', '')
        print(f"  {idx}. [{provision}] {r.metadata.get('title', '')} (score: {r.score:.4f})")

    # Smoke search test 2: BNSS
    test_query_2 = "When can a police officer arrest without warrant?"
    print(f"\nRunning test query 2: '{test_query_2}'")
    top_results_2 = await retriever.search(test_query_2, top_k=2)
    for idx, r in enumerate(top_results_2, 1):
        provision = r.metadata.get('article') or r.metadata.get('section', '')
        print(f"  {idx}. [{provision}] {r.metadata.get('title', '')} (score: {r.score:.4f})")


if __name__ == "__main__":
    asyncio.run(main())
