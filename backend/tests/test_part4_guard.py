"""
Tests for Private-Person / Directive Principle (Part IV) Guard.
Verifies that questions regarding private employers, companies, or private individuals
do NOT return Part IV Directive Principles as answers, and instead return Article 37 note.
"""

import pytest
from app.generation.service import AskService
from app.models.schemas import AnswerStatus


@pytest.mark.asyncio
async def test_private_company_maternity_leave_guarded():
    service = AskService()
    query = "What are the rules regarding maternity leave in private IT companies under the Maternity Benefit Act?"
    resp = await service.answer_question(query)

    # Must NOT present Article 42 DPSP as a binding answer against private company
    assert resp.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert any("Article 37" in pt or "Directive Principles" in pt for pt in resp.key_points)
    # Check that Article 37 note is taken from official indexed text
    assert any("not be enforceable by any court" in pt for pt in resp.key_points)
    # Check that it returns related sources instead of an authoritative answer
    assert len(resp.related_sources) > 0


@pytest.mark.asyncio
async def test_private_employer_living_wage_guarded():
    service = AskService()
    query = "Can a worker enforce a living wage against a private employer under Article 43?"
    resp = await service.answer_question(query)

    assert resp.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert any("Article 37" in pt or "enforceable" in pt for pt in resp.key_points)


@pytest.mark.asyncio
async def test_private_individual_equal_pay_guarded():
    service = AskService()
    query = "Can I sue my private company manager for equal pay under Directive Principles?"
    resp = await service.answer_question(query)

    assert resp.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert len(resp.related_sources) > 0
