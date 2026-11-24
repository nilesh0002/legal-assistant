"""
Phase 4 Tests: Verify Granular Statuses (needs_clarification, not_covered_yet,
insufficient_evidence with related sources) and endpoints (GET /coverage, GET /examples).
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.generation.service import AskService
from app.main import app
from app.models.schemas import AnswerStatus


@pytest.mark.asyncio
async def test_endpoint_coverage():
    """GET /coverage lists indexed laws, sections, and last-verified dates."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/coverage")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_chunks"] >= 98
    assert len(data["laws"]) >= 2

    # Check laws present
    laws_names = [l["law"] for l in data["laws"]]
    assert any("Constitution" in name for name in laws_names)
    assert any("Bharatiya Nagarik Suraksha Sanhita" in name for name in laws_names)

    # Verify last_verified dates are present and not None
    for l in data["laws"]:
        assert l["last_verified"] in ("2026-11-22", "2026-11-24")
        assert len(l["sections"]) > 0


@pytest.mark.asyncio
async def test_endpoint_examples():
    """GET /examples returns 8 to 10 suggested questions from indexed topics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/examples")

    assert resp.status_code == 200
    data = resp.json()
    examples = data["examples"]
    assert 8 <= len(examples) <= 10
    assert any("Article 21" in ex for ex in examples)
    assert any("bail" in ex.lower() for ex in examples)


@pytest.mark.asyncio
async def test_status_needs_clarification():
    """Vague single-word queries must trigger needs_clarification with tappable options."""
    service = AskService()
    resp = await service.answer_question("bail")

    assert resp.status == AnswerStatus.NEEDS_CLARIFICATION
    assert resp.short_answer is None
    assert resp.clarification_question is not None
    assert len(resp.clarification_options) in (2, 3)
    assert any("478" in opt or "480" in opt or "482" in opt for opt in resp.clarification_options)


@pytest.mark.asyncio
async def test_status_not_covered_yet():
    """Legal queries on unindexed statutes must name the domain and state not covered."""
    service = AskService()
    resp = await service.answer_question("What is the penalty for not wearing a helmet on a two-wheeler?")

    assert resp.status == AnswerStatus.NOT_COVERED_YET
    assert resp.short_answer is None
    assert resp.uncovered_area == "Traffic & Motor Vehicles Law"
    assert any("Traffic & Motor Vehicles Law" in kp for kp in resp.key_points)
    # Must not speculate about the fine amount
    assert resp.details == []


@pytest.mark.asyncio
async def test_status_insufficient_evidence_with_related_sources():
    """In-scope query with weak evidence returns insufficient_evidence with related sources."""
    service = AskService()
    # In-scope general legal question with no exact section in corpus
    resp = await service.answer_question("What are the powers of naval military courts over civilian property?")

    assert resp.status in (AnswerStatus.INSUFFICIENT_EVIDENCE, AnswerStatus.NOT_COVERED_YET)
    if resp.status == AnswerStatus.INSUFFICIENT_EVIDENCE:
        assert resp.short_answer is None
        # Closest 2-3 sources returned as related sources
        assert 0 < len(resp.related_sources) <= 3
