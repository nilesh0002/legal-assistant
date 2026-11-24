"""
M4 Tests: Verify /ask RAG pipeline, grounded generation, citations, and evidence gating.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.generation.service import AskService
from app.main import app
from app.models.schemas import AnswerStatus, LegalResponse


@pytest.mark.asyncio
async def test_ask_grounded_article_21():
    """Grounded question about Article 21 returns answered with exact citations."""
    service = AskService()
    resp = await service.answer_question("What is Article 21 of the Indian Constitution?")

    assert isinstance(resp, LegalResponse)
    assert resp.status == AnswerStatus.ANSWERED
    assert resp.short_answer is not None
    assert resp.short_answer.simple
    assert resp.short_answer.detailed
    assert len(resp.key_points) > 0
    assert len(resp.details) > 0

    detail = resp.details[0]
    assert "Article 21" in detail.section
    assert detail.law == "Constitution of India"
    assert detail.source_id == "constitution-india"
    assert "life" in detail.quote.lower() or "personal liberty" in detail.quote.lower()
    assert resp.disclaimer == "General information, not legal advice."


@pytest.mark.asyncio
async def test_article_21_regression_no_citizens():
    """Regression test: Article 21 answer must not contain 'citizens' unless source passage does."""
    service = AskService()
    resp = await service.answer_question("What is Article 21 of the Indian Constitution?")

    assert resp.status == AnswerStatus.ANSWERED
    assert resp.short_answer is not None

    # Retrieve source chunk to verify ground truth
    from app.retrieval.hybrid import HybridRetriever
    chunks = await HybridRetriever().search("protection of life personal liberty", top_k=1)
    source_text = chunks[0].text.lower() if chunks else ""

    # "citizens" must not appear unless explicitly in the source passage (Art 21 protects all persons)
    if "citizen" not in source_text:
        assert "citizen" not in resp.short_answer.simple.lower(), "simple answer erroneously included 'citizen'"
        assert "citizen" not in resp.short_answer.detailed.lower(), "detailed answer erroneously included 'citizen'"

    # Verify no double period
    assert ".." not in resp.short_answer.simple
    assert ".." not in resp.short_answer.detailed

    # Verify no truncated ellipses in key points
    for kp in resp.key_points:
        assert "..." not in kp

    # Verify claim wording is clean and natural
    for detail in resp.details:
        assert not detail.claim.startswith("Claim:")
        assert not detail.claim.endswith("..")


@pytest.mark.asyncio
async def test_ask_grounded_article_14():
    """Grounded question about equality before the law."""
    service = AskService()
    resp = await service.answer_question("Explain the right to equality under Article 14")

    assert resp.status == AnswerStatus.ANSWERED
    assert resp.short_answer is not None
    assert any("Article 14" in d.section for d in resp.details)
    assert any("equality" in d.quote.lower() for d in resp.details)


@pytest.mark.asyncio
async def test_ask_out_of_scope():
    """Cooking/recipe question must return out_of_scope immediately."""
    service = AskService()
    resp = await service.answer_question("What is the recipe for cooking butter chicken?")

    assert resp.status == AnswerStatus.OUT_OF_SCOPE
    assert resp.short_answer is None
    assert resp.details == []
    assert resp.disclaimer == "General information, not legal advice."


@pytest.mark.asyncio
async def test_ask_insufficient_evidence():
    """Uncovered legal topic must return insufficient_evidence instead of hallucinating."""
    service = AskService()
    # Topic not in Part III of the Constitution or approved corpus
    resp = await service.answer_question("What is the penalty for municipal zoning violation in ward 42?")

    assert resp.status in (AnswerStatus.INSUFFICIENT_EVIDENCE, AnswerStatus.NOT_COVERED_YET)
    assert resp.short_answer is None
    assert resp.disclaimer == "General information, not legal advice."


@pytest.mark.asyncio
async def test_api_post_ask_endpoint():
    """Test HTTP POST /ask endpoint integration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ask",
            json={"question": "What is the protection against untouchability?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "answered"
    assert data["short_answer"]["simple"]
    assert any("Article 17" in d["section"] for d in data["details"])
    assert data["disclaimer"] == "General information, not legal advice."
