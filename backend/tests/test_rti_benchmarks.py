"""
Phase 6 Tests: 15 Benchmark Questions + 5 Out-of-Scope Questions for Right to Information Act 2005.
Verifies grounded retrieval and answering for RTI requests, timelines, exemptions, and penalties.
"""

import pytest
from app.generation.service import AskService
from app.models.schemas import AnswerStatus

BENCHMARK_RTI_QUESTIONS = [
    ("What is the definition of information under Section 2 of the RTI Act 2005?", ["Section 2"]),
    ("Who has the right to information under Section 3 of the RTI Act?", ["Section 3"]),
    ("What are the proactive obligations of public authorities under Section 4 of RTI Act?", ["Section 4"]),
    ("How are Public Information Officers designated under Section 5 of the RTI Act?", ["Section 5"]),
    ("How does a citizen make a request for obtaining information under Section 6 of RTI Act?", ["Section 6"]),
    ("Within how many days must a Public Information Officer dispose of an RTI request under Section 7?", ["Section 7"]),
    ("What categories of information are exempt from disclosure under Section 8 of the RTI Act?", ["Section 8"]),
    ("On what grounds can access to information be rejected under Section 9 of the RTI Act?", ["Section 9"]),
    ("What does the doctrine of severability provide under Section 10 of RTI Act?", ["Section 10"]),
    ("How is third party information handled under Section 11 of the RTI Act?", ["Section 11"]),
    ("How is the Central Information Commission constituted under Section 12 of the RTI Act?", ["Section 12"]),
    ("What are the powers of the Information Commission to inquire into complaints under Section 18?", ["Section 18"]),
    ("What is the procedure and timeline for filing an appeal under Section 19 of RTI Act?", ["Section 19"]),
    ("What financial penalty can be imposed on a PIO under Section 20 of the RTI Act?", ["Section 20"]),
    ("Does the RTI Act override inconsistent provisions in other laws under Section 22?", ["Section 22"]),
]

OUT_OF_SCOPE_RTI_QUESTIONS = [
    "What is the penalty for driving a car without a valid fitness certificate?",
    "How does a private partnership firm register with the Registrar of Firms?",
    "What is the rate of GST on hotel accommodation?",
    "How to contest a will under the Indian Succession Act?",
    "What are the rights of an adopted child under Hindu law?",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_secs", BENCHMARK_RTI_QUESTIONS)
async def test_rti_benchmarks(query: str, expected_secs):
    service = AskService()
    resp = await service.answer_question(query)

    assert resp.status == AnswerStatus.ANSWERED, f"RTI Query '{query}' failed with status {resp.status}"
    assert resp.short_answer is not None
    assert len(resp.details) > 0

    retrieved_sections = [d.section for d in resp.details]
    assert any(any(exp in s for exp in expected_secs) for s in retrieved_sections), (
        f"Query '{query}' expected one of {expected_secs} but retrieved: {retrieved_sections}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("query", OUT_OF_SCOPE_RTI_QUESTIONS)
async def test_rti_out_of_scope(query: str):
    service = AskService()
    resp = await service.answer_question(query)
    assert resp.status in (
        AnswerStatus.NOT_COVERED_YET,
        AnswerStatus.INSUFFICIENT_EVIDENCE,
        AnswerStatus.OUT_OF_SCOPE,
    ), f"Out-of-scope query '{query}' was unexpectedly answered with status {resp.status}"
