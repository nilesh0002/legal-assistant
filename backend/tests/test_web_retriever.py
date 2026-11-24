"""
Unit test for WebLegalRetriever (live Indian Kanoon & legal sources).
"""

import pytest
from app.retrieval.web_search import WebLegalRetriever
from app.generation.service import AskService
from app.models.schemas import AnswerStatus


@pytest.mark.asyncio
async def test_web_retriever_live_kanoon():
    retriever = WebLegalRetriever(timeout=10.0)
    chunks = await retriever.search_live_legal_web("Maneka Gandhi v. Union of India", max_docs=1)
    
    # If network is available, it should retrieve chunks with indian-kanoon source_id
    if chunks:
        assert chunks[0].source_id == "indian-kanoon"
        assert "indiankanoon.org" in chunks[0].metadata["source_url"]
        assert len(chunks[0].text) > 50
        assert "Gandhi" in chunks[0].metadata["title"] or "Maneka" in chunks[0].text


@pytest.mark.asyncio
async def test_ask_service_with_landmark_case():
    service = AskService()
    # Query for landmark judgment
    resp = await service.answer_question("What did the Supreme Court hold in the Maneka Gandhi case?")
    
    assert resp.status == AnswerStatus.ANSWERED
    assert resp.short_answer is not None
    assert len(resp.details) > 0
    assert any("indian-kanoon" in d.source_id or "constitution" in d.source_id for d in resp.details)
