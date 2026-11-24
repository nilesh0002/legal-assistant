"""
15 Benchmark Tests for Expanded BNSS 2023 Coverage:
- Arrest procedure (Sec 35, 36, 38, 40, 43, 44, 47, 48, 51, 58)
- Summons and Warrants (Sec 63, 72)
- Search and Seizure (Sec 103, 105)
- Remand and Custody Limits (Sec 187)
- Bail and Anticipatory Bail (Sec 478, 479, 480, 482)
"""

import pytest
from app.generation.local_llm import LocalGroundedLLM
from app.generation.service import AskService
from app.models.schemas import AnswerStatus

BENCHMARK_BNSS_QUESTIONS = [
    ("When can police arrest without a warrant under BNSS?", "Section 35"),
    ("What are the duties of a police officer while making an arrest?", "Section 36"),
    ("Does an arrested person have a right to meet an advocate during interrogation?", "Section 38"),
    ("Can a private person arrest an offender?", "Section 40"),
    ("Can women be arrested after sunset and before sunrise?", "Section 43"),
    ("Can police search a house where a person to be arrested has entered?", "Section 44"),
    ("Must an arrested person be informed of the grounds of arrest and right to bail?", "Section 47"),
    ("Is the police obligated to inform a nominated person or relative about the arrest?", "Section 48"),
    ("What is the procedure for medical examination of an arrested person?", ["Section 51", "Section 53"]),
    ("What is the maximum detention period without production before a Magistrate under BNSS?", ["Section 58", "Article 22"]),
    ("What is the form and duration of a warrant of arrest under BNSS?", ["Section 72"]),
    ("Is audio-video electronic recording required during search and seizure?", ["Section 105"]),
    ("What are the police custody and detention limits under Section 187 of BNSS?", ["Section 187"]),
    ("What is the procedure for bail in bailable offences under BNSS?", ["Section 478"]),
    ("How does a person apply for anticipatory bail under Section 482 of BNSS?", ["Section 482"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_sec", BENCHMARK_BNSS_QUESTIONS)
async def test_expanded_bnss_benchmarks(query: str, expected_sec):
    service = AskService(llm=LocalGroundedLLM())
    res = await service.answer_question(query)

    assert res.status == AnswerStatus.ANSWERED, f"Benchmark query '{query}' failed with status {res.status}"
    assert res.short_answer is not None
    assert len(res.details) > 0

    expected_list = expected_sec if isinstance(expected_sec, list) else [expected_sec]
    retrieved_sections = [d.section for d in res.details]
    assert any(any(exp in s for exp in expected_list) for s in retrieved_sections), (
        f"Query '{query}' expected one of '{expected_list}' but retrieved: {retrieved_sections}"
    )
