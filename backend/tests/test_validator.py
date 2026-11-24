"""
Unit tests for M5 Concrete Response Validator.
Tests citation integrity, quote verification, and support checks.
"""

import pytest
from app.models.schemas import (
    AnswerStatus,
    LegalResponse,
    RelatedJudgment,
    ShortAnswer,
    SourceDetail,
)
from app.retrieval.base import RetrievedChunk
from app.validation.validator import LegalResponseValidator


@pytest.fixture
def sample_chunks():
    return [
        RetrievedChunk(
            chunk_id="art-21",
            text="Protection of life and personal liberty.—No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            metadata={
                "article": "Article 21",
                "title": "Article 21: Protection of life and personal liberty",
                "location": "Part III, page 45",
            },
            source_id="constitution-india",
            score=0.95,
        )
    ]


@pytest.fixture
def approved_sources():
    return {
        "constitution-india": {
            "id": "constitution-india",
            "title": "The Constitution of India",
        }
    }


def test_validator_valid_response(sample_chunks, approved_sources):
    validator = LegalResponseValidator(sources_registry=approved_sources)

    resp = LegalResponse(
        status=AnswerStatus.ANSWERED,
        question="What is Article 21?",
        short_answer=ShortAnswer(
            simple="Under Article 21, no person shall be deprived of his life or personal liberty.",
            detailed="According to Article 21 of the Constitution of India, life and liberty are protected.",
        ),
        key_points=["Article 21 protects life and personal liberty."],
        details=[
            SourceDetail(
                claim="Article 21 provides protection of life",
                law="Constitution of India",
                section="Article 21",
                quote="No person shall be deprived of his life or personal liberty except according to procedure established by law",
                source_id="constitution-india",
                source_title="Article 21",
                source_url="https://example.com",
                location="Part III, page 45",
            )
        ],
        disclaimer="General information, not legal advice.",
    )

    res = validator.validate(resp, sample_chunks, approved_sources)
    assert res.is_valid, f"Expected valid response, got errors: {res.errors}"


def test_validator_rejects_fake_source_id(sample_chunks, approved_sources):
    validator = LegalResponseValidator(sources_registry=approved_sources)

    resp = LegalResponse(
        status=AnswerStatus.ANSWERED,
        question="What is Article 21?",
        short_answer=ShortAnswer(
            simple="Under Article 21, no person shall be deprived of his life.",
            detailed="Detailed text.",
        ),
        details=[
            SourceDetail(
                claim="Article 21 claim",
                law="Constitution of India",
                section="Article 21",
                quote="No person shall be deprived of his life or personal liberty",
                source_id="fake-source-id-123",
                source_title="Fake source",
                source_url="https://example.com",
                location="Part III, page 45",
            )
        ],
        disclaimer="General information, not legal advice.",
    )

    res = validator.validate(resp, sample_chunks, approved_sources)
    assert not res.is_valid
    assert any("fake-source-id-123" in err for err in res.errors)


def test_validator_rejects_hallucinated_quote(sample_chunks, approved_sources):
    validator = LegalResponseValidator(sources_registry=approved_sources)

    resp = LegalResponse(
        status=AnswerStatus.ANSWERED,
        question="What is Article 21?",
        short_answer=ShortAnswer(
            simple="Under Article 21, all citizens have a fundamental right to health and education.",
            detailed="Detailed text.",
        ),
        details=[
            SourceDetail(
                claim="Article 21 claim",
                law="Constitution of India",
                section="Article 21",
                quote="Every citizen has the right to free healthcare provided by the state",
                source_id="constitution-india",
                source_title="Article 21",
                source_url="https://example.com",
                location="Part III, page 45",
            )
        ],
        disclaimer="General information, not legal advice.",
    )

    res = validator.validate(resp, sample_chunks, approved_sources)
    assert not res.is_valid
    assert any("quote does not appear verbatim" in err for err in res.errors)


def test_validator_rejects_unsupported_article_number(sample_chunks, approved_sources):
    validator = LegalResponseValidator(sources_registry=approved_sources)

    # Response mentions Article 999 which is not in context
    resp = LegalResponse(
        status=AnswerStatus.ANSWERED,
        question="What is Article 21?",
        short_answer=ShortAnswer(
            simple="Under Article 999, the state shall protect trees.",
            detailed="Detailed text.",
        ),
        details=[
            SourceDetail(
                claim="Article 21 claim",
                law="Constitution of India",
                section="Article 21",
                quote="No person shall be deprived of his life or personal liberty except according to procedure established by law",
                source_id="constitution-india",
                source_title="Article 21",
                source_url="https://example.com",
                location="Part III, page 45",
            )
        ],
        disclaimer="General information, not legal advice.",
    )

    res = validator.validate(resp, sample_chunks, approved_sources)
    assert not res.is_valid
    assert any("Article 999 is mentioned in answer but absent" in err for err in res.errors)
