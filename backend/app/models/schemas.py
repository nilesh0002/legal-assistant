"""
Pydantic models for the API request/response contract.

These match the BACKEND RESPONSE FORMAT from the project brief.
They are defined now (M0) so the Android app can build against
the shape immediately, even before the backend fills them in.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnswerStatus(str, Enum):
    """Every response carries exactly one of these statuses."""
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    OUT_OF_SCOPE = "out_of_scope"
    ERROR = "error"


class ShortAnswer(BaseModel):
    """Two-layer answer: plain language + detailed explanation."""
    simple: str = Field(..., description="Plain-language answer anyone can understand")
    detailed: str = Field(..., description="Detailed answer with legal terminology")


class SourceDetail(BaseModel):
    """One piece of evidence backing a claim in the answer."""
    claim: str = Field(..., description="The specific claim this evidence supports")
    law: str = Field(..., description="Name of the law (e.g. 'Constitution of India')")
    section: str = Field(..., description="Article or section number")
    old_equivalent: Optional[str] = Field(
        None, description="Old law equivalent (e.g. CrPC section for a BNSS section)"
    )
    quote: str = Field(..., description="Exact quote from the source — must match word-for-word")
    source_id: str = Field(..., description="ID from data/sources.yaml")
    source_title: str
    source_url: str
    location: str = Field(..., description="Where in the source (page, paragraph, etc.)")


class RelatedJudgment(BaseModel):
    """A landmark judgment related to the answer."""
    name: str = Field(..., description="Case name, e.g. 'Kesavananda Bharati v. State of Kerala'")
    year: int
    source_id: str = Field(..., description="Must exist in the approved corpus")


class QuestionRequest(BaseModel):
    """What the Android app sends to /ask."""
    question: str = Field(..., min_length=3, max_length=1000)


class SearchRequest(BaseModel):
    """Query parameter payload for /search."""
    query: str = Field(..., min_length=2, max_length=1000, description="Legal search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SearchResultItem(BaseModel):
    """A single retrieved legal document chunk."""
    chunk_id: str
    source_id: str
    score: float
    law: str
    article: str
    title: str
    text: str
    location: str
    subheading: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response returned by /search endpoint."""
    query: str
    total_results: int
    results: List[SearchResultItem]


class LegalResponse(BaseModel):
    """
    The full response returned by /ask.

    Every field is designed so the Android app can render two views:
    - Simple view: short_answer.simple + key_points + disclaimer
    - Detailed view: short_answer.detailed + details + related_judgments
    """
    status: AnswerStatus
    question: str
    short_answer: Optional[ShortAnswer] = None
    key_points: List[str] = Field(default_factory=list)
    details: List[SourceDetail] = Field(default_factory=list)
    related_judgments: List[RelatedJudgment] = Field(default_factory=list)
    last_verified: Optional[str] = Field(
        None, description="ISO date when sources were last checked"
    )
    disclaimer: str = "General information, not legal advice."
