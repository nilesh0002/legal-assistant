"""
Test that Pydantic models serialize correctly.

These tests run without any external service — they just check
that the data shapes defined in schemas.py work as expected.
"""

import pytest
from app.models.schemas import (
    AnswerStatus,
    LegalResponse,
    ShortAnswer,
    SourceDetail,
    RelatedJudgment,
    QuestionRequest,
)


def test_legal_response_answered():
    """A fully populated 'answered' response should serialize cleanly."""
    resp = LegalResponse(
        status=AnswerStatus.ANSWERED,
        question="What is Article 21?",
        short_answer=ShortAnswer(
            simple="Article 21 protects your right to life and personal liberty.",
            detailed="Article 21 of the Constitution of India states: "
                     "\"No person shall be deprived of his life or personal "
                     "liberty except according to procedure established by law.\"",
        ),
        key_points=[
            "Guarantees right to life and personal liberty",
            "Protection against arbitrary state action",
        ],
        details=[
            SourceDetail(
                claim="Article 21 protects right to life",
                law="Constitution of India",
                section="Article 21",
                quote="PLACEHOLDER — exact quote to be added in M1",
                source_id="constitution-india",
                source_title="The Constitution of India",
                source_url="https://legislative.gov.in/constitution-of-india/",
                location="Part III, Article 21",
            )
        ],
        related_judgments=[
            RelatedJudgment(
                name="Maneka Gandhi v. Union of India",
                year=1978,
                source_id="judgment-maneka-gandhi",
            )
        ],
        last_verified="2024-01-15",
    )
    data = resp.model_dump()
    assert data["status"] == "answered"
    assert data["disclaimer"] == "General information, not legal advice."
    assert len(data["details"]) == 1
    assert len(data["related_judgments"]) == 1


def test_legal_response_insufficient_evidence():
    """An insufficient_evidence response has no answer body."""
    resp = LegalResponse(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        question="What is the punishment for jaywalking?",
    )
    data = resp.model_dump()
    assert data["status"] == "insufficient_evidence"
    assert data["short_answer"] is None
    assert data["key_points"] == []


def test_question_request_validation():
    """Questions must be between 3 and 1000 characters."""
    req = QuestionRequest(question="What is Article 14?")
    assert req.question == "What is Article 14?"

    with pytest.raises(Exception):
        QuestionRequest(question="Hi")


def test_old_equivalent_is_optional():
    """old_equivalent should be None when not applicable."""
    detail = SourceDetail(
        claim="Test",
        law="Constitution of India",
        section="Article 14",
        quote="PLACEHOLDER",
        source_id="constitution-india",
        source_title="The Constitution of India",
        source_url="https://legislative.gov.in/constitution-of-india/",
        location="Part III",
    )
    assert detail.old_equivalent is None
