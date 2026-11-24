"""
M4/M5 Tests: Evidence Threshold Verification across 10 in-scope and 10 out-of-scope questions.
Ensures semantic evidence gating (vector_score >= 0.68 or bm25 > 0.05 + vector >= 0.60)
reliably admits genuine constitutional questions and rejects uncovered legal topics.
"""

import pytest
from app.generation.service import AskService
from app.models.schemas import AnswerStatus

IN_SCOPE_QUESTIONS = [
    "What does Article 21 protect?",
    "Explain the right to equality under Article 14",
    "Abolition of untouchability under Article 17",
    "What is the right to education under Article 21A?",
    "Freedom of speech and expression under Article 19",
    "Protection against arbitrary arrest and detention under Article 22",
    "Prohibition of human trafficking and forced labour under Article 23",
    "Remedies for enforcement of fundamental rights under Article 32",
    "Protection of interests of minorities under Article 29",
    "Definition of State under Article 12 of the Constitution",
]

OUT_OF_SCOPE_UNCOVERED_QUESTIONS = [
    "What is the penalty for municipal zoning violation in ward 42?",
    "What are the rules for filing corporate tax returns for private limited companies?",
    "How to register a trademark for a software product in India?",
    "What is the minimum stamp duty for residential property registration in Bangalore?",
    "What is the procedure for obtaining a municipal trade license for a restaurant?",
    "What are the traffic fines for jumping a red light under motor vehicles act?",
    "How to apply for an Indian passport renewal online?",
    "What are the water bill tariff rates for commercial establishments in Chennai?",
    "What is the noise decibel limit for residential areas during night hours under municipal bylaws?",
    "What are the customs import duties on electronics from China?",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query", IN_SCOPE_QUESTIONS)
async def test_in_scope_evidence_threshold(query: str):
    """All 10 in-scope questions must pass evidence threshold and be answered."""
    service = AskService()
    resp = await service.answer_question(query)

    assert resp.status == AnswerStatus.ANSWERED, f"In-scope query '{query}' failed with status {resp.status}"
    assert resp.short_answer is not None
    assert len(resp.details) > 0
    assert resp.disclaimer == "General information, not legal advice."


@pytest.mark.asyncio
@pytest.mark.parametrize("query", OUT_OF_SCOPE_UNCOVERED_QUESTIONS)
async def test_out_of_scope_evidence_threshold(query: str):
    """All 10 out-of-scope / uncovered questions must fail evidence threshold or scope filter."""
    service = AskService()
    resp = await service.answer_question(query)

    assert resp.status in (
        AnswerStatus.INSUFFICIENT_EVIDENCE,
        AnswerStatus.OUT_OF_SCOPE,
        AnswerStatus.NOT_COVERED_YET,
    ), f"Out-of-scope query '{query}' should not be answered; got {resp.status}"
    assert resp.short_answer is None
    assert resp.details == []
    assert resp.disclaimer == "General information, not legal advice."
