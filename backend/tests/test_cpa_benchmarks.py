"""
Phase 6 Tests: 15 Benchmark Questions + 5 Out-of-Scope Questions for Consumer Protection Act 2019.
Verifies grounded retrieval and answering for consumer rights, commissions, and product liability.
"""

import pytest
from app.generation.service import AskService
from app.models.schemas import AnswerStatus

BENCHMARK_CPA_QUESTIONS = [
    ("What is the definition of consumer under Section 2 of Consumer Protection Act 2019?", ["Section 2"]),
    ("What are the powers of the Central Consumer Protection Authority under Section 18?", ["Section 18"]),
    ("Can the Central Authority recall unsafe goods under Section 20 of CPA 2019?", ["Section 20"]),
    ("What penalties can be imposed for misleading advertisements under Section 21 of CPA?", ["Section 21"]),
    ("What is the pecuniary jurisdiction of the District Commission under Section 34 of CPA 2019?", ["Section 34"]),
    ("What is the manner in which a consumer complaint shall be made under Section 35 of CPA?", ["Section 35"]),
    ("What procedure is followed upon admission of a complaint under Section 38 of CPA?", ["Section 38"]),
    ("What orders can the District Commission pass under Section 39 of Consumer Protection Act?", ["Section 39"]),
    ("What is the limitation period for filing an appeal to the State Commission under Section 41?", ["Section 41"]),
    ("What is the jurisdiction of the State Consumer Commission under Section 47 of CPA 2019?", ["Section 47"]),
    ("What is the appellate jurisdiction of the National Commission under Section 51 of CPA?", ["Section 51"]),
    ("What is the jurisdiction of the National Consumer Disputes Redressal Commission under Section 58?", ["Section 58"]),
    ("What is the limitation period for filing a complaint under Section 69 of Consumer Protection Act?", ["Section 69"]),
    ("Can a consumer dispute be referred to mediation under Section 74 of CPA 2019?", ["Section 74"]),
    ("What are the grounds for product liability action against a manufacturer under Section 84 of CPA?", ["Section 84", "Section 83"]),
]

OUT_OF_SCOPE_CPA_QUESTIONS = [
    "What is the penalty for not having motor vehicle insurance?",
    "How to register a trademark for a consumer brand?",
    "What is the capital gains tax rate on selling gold jewellery?",
    "How to file for divorce by mutual consent in family court?",
    "What is the legal punishment for cyber hacking under Section 66?",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_secs", BENCHMARK_CPA_QUESTIONS)
async def test_cpa_benchmarks(query: str, expected_secs):
    service = AskService()
    resp = await service.answer_question(query)

    assert resp.status == AnswerStatus.ANSWERED, f"CPA Query '{query}' failed with status {resp.status}"
    assert resp.short_answer is not None
    assert len(resp.details) > 0

    retrieved_sections = [d.section for d in resp.details]
    assert any(any(exp in s for exp in expected_secs) for s in retrieved_sections), (
        f"Query '{query}' expected one of {expected_secs} but retrieved: {retrieved_sections}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("query", OUT_OF_SCOPE_CPA_QUESTIONS)
async def test_cpa_out_of_scope(query: str):
    service = AskService()
    resp = await service.answer_question(query)
    assert resp.status in (
        AnswerStatus.NOT_COVERED_YET,
        AnswerStatus.INSUFFICIENT_EVIDENCE,
        AnswerStatus.OUT_OF_SCOPE,
    ), f"Out-of-scope query '{query}' was unexpectedly answered with status {resp.status}"
