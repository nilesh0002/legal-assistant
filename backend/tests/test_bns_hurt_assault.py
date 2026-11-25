"""
10 Lay-Wording Benchmark Questions for BNS Hurt, Assault, Criminal Force & Weapons,
plus Two-Step Arrest-for-Offence & Related-Sources verification.
"""

import pytest
from fastapi.testclient import TestClient

from app.generation.local_llm import LocalGroundedLLM
from app.generation.service import AskService
from app.main import app
from app.models.schemas import AnswerStatus

LAY_BNS_BENCHMARKS = [
    ("Can I get arrested for slapping my neighbour?", ["Section 115", "Section 131", "Section 130", "Section 129"]),
    ("What is the punishment for punching someone in anger?", ["Section 115", "Section 131"]),
    ("Is pushing someone without their consent a crime under BNS?", ["Section 129", "Section 131", "Section 128"]),
    ("Can someone be punished for threatening to beat me up?", ["Section 351", "Section 131", "Section 130"]),
    ("What happens if two neighbours fight in the street?", ["Section 194", "Section 115"]),
    ("What is the punishment for hurting someone with a sharp knife or weapon?", ["Section 118", "Section 117"]),
    ("What counts as grievous hurt under BNS?", ["Section 116", "Section 117"]),
    ("What is the difference between assault and criminal force?", ["Section 130", "Section 129", "Section 131"]),
    ("What is the punishment for voluntarily causing hurt?", ["Section 115"]),
    ("What does Section 118 of BNS say about dangerous weapons?", ["Section 118"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_secs", LAY_BNS_BENCHMARKS)
async def test_bns_hurt_assault_lay_benchmarks(query: str, expected_secs):
    svc = AskService(llm=LocalGroundedLLM())
    res = await svc.answer_question(query)

    assert res.status == AnswerStatus.ANSWERED, f"Query '{query}' failed with {res.status}"
    assert res.short_answer is not None
    assert len(res.details) > 0

    retrieved_secs = [d.section for d in res.details]
    assert any(any(exp in s for exp in expected_secs) for s in retrieved_secs), (
        f"Query '{query}' expected one of {expected_secs}, got {retrieved_secs}"
    )


@pytest.mark.asyncio
async def test_two_step_slapping_arrest_includes_bns_and_bnss():
    svc = AskService(llm=LocalGroundedLLM())
    res = await svc.answer_question("Can I get arrested for slapping my neighbour?")

    assert res.status == AnswerStatus.ANSWERED
    source_ids = [d.source_id for d in res.details]
    assert "bns-2023" in source_ids
    assert "bnss-2023" in source_ids
    # Must explicitly state classification is not in the indexed text (no guessing from memory)
    assert "does not state" in res.short_answer.simple.lower() or "does not include" in res.short_answer.detailed.lower()


@pytest.mark.asyncio
async def test_insufficient_evidence_returns_related_sources():
    svc = AskService(llm=LocalGroundedLLM())
    res = await svc.answer_question("What is the procedure for registering a private limited company in India?")
    assert res.status in (AnswerStatus.INSUFFICIENT_EVIDENCE, AnswerStatus.NOT_COVERED_YET)
    if res.status == AnswerStatus.INSUFFICIENT_EVIDENCE:
        assert 1 <= len(res.related_sources) <= 3


def test_coverage_lists_new_bns_hurt_assault_sections():
    client = TestClient(app)
    resp = client.get("/coverage")
    assert resp.status_code == 200
    data = resp.json()
    bns_law = next((l for l in data["laws"] if "Nyaya Sanhita" in l["law"]), None)
    assert bns_law is not None
    secs = {s["section"] for s in bns_law["sections"]}
    for expected in ("Section 115", "Section 116", "Section 118", "Section 128", "Section 129", "Section 130", "Section 131"):
        assert expected in secs, f"{expected} missing from /coverage"
