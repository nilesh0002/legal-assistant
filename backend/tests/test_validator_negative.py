"""
Negative tests for LegalResponseValidator:
Proves the validator catches hallucinated articles, sections, case names, years, time limits,
tampered quotes, and unapproved sources.
"""

import pytest
from app.models.schemas import AnswerStatus, LegalResponse, ShortAnswer, SourceDetail
from app.retrieval.base import RetrievedChunk
from app.validation.validator import LegalResponseValidator


def sample_retrieved_chunk():
    return RetrievedChunk(
        chunk_id="bnss-sec-35",
        source_id="bnss-2023",
        text="Any police officer may without an order from a Magistrate and without a warrant arrest any person who commits in the presence of a police officer a cognizable offence.",
        score=0.92,
        metadata={
            "law": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "section": "Section 35",
            "location": "BNSS 2023, Section 35, Page 12",
        }
    )


def build_valid_response():
    chunk = sample_retrieved_chunk()
    return LegalResponse(
        status=AnswerStatus.ANSWERED,
        question="When can police arrest without a warrant under Section 35?",
        short_answer=ShortAnswer(
            simple="Under Section 35, a police officer may arrest someone without a warrant for a cognizable offence.",
            detailed="According to Section 35, any police officer may without an order from a Magistrate and without a warrant arrest any person."
        ),
        key_points=["Arrest without warrant is permitted under Section 35 for cognizable offences."],
        details=[
            SourceDetail(
                claim="Section 35 allows arrest without warrant",
                law="Bharatiya Nagarik Suraksha Sanhita, 2023",
                section="Section 35",
                quote="Any police officer may without an order from a Magistrate and without a warrant arrest any person who commits in the presence of a police officer a cognizable offence.",
                source_id="bnss-2023",
                source_title="BNSS 2023",
                source_url="https://egazette.gov.in/WriteReadData/2023/250884.pdf",
                location="BNSS 2023, Section 35, Page 12"
            )
        ],
        disclaimer="General information, not legal advice."
    )


def test_validator_passes_valid_response():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    result = validator.validate(resp, [chunk])
    assert result.is_valid, f"Expected valid response to pass, got errors: {result.errors}"


def test_validator_catches_hallucinated_section():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Inject fake section number into simple answer
    resp.short_answer.simple = "Under Section 9999, the police can arrest anyone."
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("Section 9999" in err for err in result.errors)


def test_validator_catches_hallucinated_article():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Inject fake article number
    resp.short_answer.simple = "Under Article 777, personal liberty is protected."
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("Article 777" in err for err in result.errors)


def test_validator_catches_hallucinated_case_name():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Inject unverified case name
    resp.short_answer.detailed += " As held in Smith v. State of Wonderland, arrest requires cause."
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("Smith v. State" in err for err in result.errors)


def test_validator_catches_hallucinated_year():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Inject unverified year not in text or statute years
    resp.short_answer.detailed += " This was decided in 2049 by the bench."
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("2049" in err for err in result.errors)


def test_validator_catches_hallucinated_time_limit():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Inject time limit not in text
    resp.short_answer.simple += " The detention cannot exceed 99 days."
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("99 days" in err for err in result.errors)


def test_validator_catches_tampered_quote():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Tamper with verbatim quote
    resp.details[0].quote = "Police officers can always arrest anybody whenever they feel like it."
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("quote does not appear verbatim" in err for err in result.errors)


def test_validator_catches_unapproved_source_id():
    validator = LegalResponseValidator()
    chunk = sample_retrieved_chunk()
    resp = build_valid_response()
    # Use unapproved source id
    resp.details[0].source_id = "indian-kanoon-blog"
    result = validator.validate(resp, [chunk])
    assert not result.is_valid
    assert any("not in approved sources.yaml" in err for err in result.errors)
