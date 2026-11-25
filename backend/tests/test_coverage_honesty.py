"""
Tests for Coverage Honesty.
Verifies that:
1. /coverage endpoint explicitly notes "selected sections only".
2. If a query mentions an unindexed Article or Section number, the system returns
   NOT_COVERED_YET or INSUFFICIENT_EVIDENCE, and NEVER substitutes a nearby section.
"""

import pytest
from app.generation.service import AskService
from app.models.schemas import AnswerStatus
from app.api.routes import get_coverage


@pytest.mark.asyncio
async def test_coverage_endpoint_honesty():
    cov = await get_coverage()
    assert "note" in cov
    assert "selected sections" in cov["note"].lower()
    for law in cov["laws"]:
        assert "coverage_note" in law
        assert "selected sections" in law["coverage_note"].lower()
        assert len(law["sections"]) > 0


@pytest.mark.asyncio
async def test_unindexed_section_never_substitutes_nearby():
    service = AskService()
    # Section 399 of BNSS is not in the indexed selected sections
    query = "What is the procedure under Section 399 of BNSS?"
    resp = await service.answer_question(query)

    assert resp.status in (AnswerStatus.NOT_COVERED_YET, AnswerStatus.INSUFFICIENT_EVIDENCE)
    # Proves it did not answer with a nearby section like Section 35 or 478
    assert resp.status != AnswerStatus.ANSWERED


@pytest.mark.asyncio
async def test_unindexed_bns_section_refused():
    service = AskService()
    # Section 250 of BNS is not in indexed selected sections
    query = "What does Section 250 of BNS provide?"
    resp = await service.answer_question(query)

    assert resp.status in (AnswerStatus.NOT_COVERED_YET, AnswerStatus.INSUFFICIENT_EVIDENCE)
    assert resp.status != AnswerStatus.ANSWERED


@pytest.mark.asyncio
async def test_unindexed_constitution_article_refused():
    service = AskService()
    # Article 356 (President's Rule in Part XVIII) is not in indexed Part III/IV/IVA
    query = "What are the conditions for imposing President's Rule under Article 356?"
    resp = await service.answer_question(query)

    assert resp.status in (AnswerStatus.NOT_COVERED_YET, AnswerStatus.INSUFFICIENT_EVIDENCE)
    assert resp.status != AnswerStatus.ANSWERED
