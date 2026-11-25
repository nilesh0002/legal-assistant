"""
Phase 5 Tests: 15 Benchmark Questions + 5 Out-of-Scope Questions for BNS 2023.
Verifies grounded retrieval and answering for substantive criminal law (offences & punishments).
"""

import pytest
from app.generation.service import AskService
from app.models.schemas import AnswerStatus

BENCHMARK_BNS_QUESTIONS = [
    ("What is the punishment for murder under Section 103 of BNS?", ["Section 103", "Section 101"]),
    ("What are the legal grounds for the right of private defence of the body extending to causing death?", ["Section 37", "Section 34"]),
    ("Is an act committed by a child under seven years an offence under BNS?", ["Section 20"]),
    ("What is the punishment for causing death by rash or negligent act under Section 106?", ["Section 106"]),
    ("What constitutes the offence of sexual harassment under Section 75 of BNS?", ["Section 75"]),
    ("What is the definition of dowry death under Section 80 of BNS?", ["Section 80"]),
    ("What are the essential ingredients of the offence of theft under Section 303 of BNS?", ["Section 303"]),
    ("What is the punishment for cheating under Section 318 of BNS?", ["Section 318"]),
    ("What is criminal breach of trust under Section 316 of BNS?", ["Section 316"]),
    ("How does BNS define the offence of stalking under Section 78?", ["Section 78"]),
    ("What is the punishment for defamation under Section 356 of BNS?", ["Section 356"]),
    ("What constitutes criminal intimidation under Section 351 of BNS?", ["Section 351"]),
    ("What is an unlawful assembly under Section 189 of BNS?", ["Section 189"]),
    ("What constitutes grievous hurt under Section 115 of BNS?", ["Section 115", "Section 114"]),
    ("What constitutes acts endangering the sovereignty, unity, and integrity of India under Section 152 of BNS?", ["Section 152"]),
]

OUT_OF_SCOPE_QUESTIONS = [
    "What is the fine for speeding on a state highway?",
    "How to file a consumer complaint for a defective refrigerator?",
    "What is the penalty for driving without a valid motor vehicle registration?",
    "What is the maximum imprisonment for hacking under the IT Act?",
    "What are the rules for adopting a child under the Hindu Adoptions and Maintenance Act?",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_secs", BENCHMARK_BNS_QUESTIONS)
async def test_bns_benchmarks(query: str, expected_secs):
    service = AskService()
    resp = await service.answer_question(query)

    assert resp.status == AnswerStatus.ANSWERED, f"BNS Query '{query}' failed with status {resp.status}"
    assert resp.short_answer is not None
    assert len(resp.details) > 0

    retrieved_sections = [d.section for d in resp.details]
    assert any(any(exp in s for exp in expected_secs) for s in retrieved_sections), (
        f"Query '{query}' expected one of {expected_secs} but retrieved: {retrieved_sections}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("query", OUT_OF_SCOPE_QUESTIONS)
async def test_bns_out_of_scope(query: str):
    service = AskService()
    resp = await service.answer_question(query)

    assert resp.status in (
        AnswerStatus.NOT_COVERED_YET,
        AnswerStatus.INSUFFICIENT_EVIDENCE,
        AnswerStatus.OUT_OF_SCOPE,
    ), f"Query '{query}' should not be answered; got status {resp.status}"
    assert resp.short_answer is None
