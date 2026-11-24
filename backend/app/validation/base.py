"""
Abstract validation interface.

The validator checks every answer BEFORE it reaches the user.
This is the code-level enforcement of Rule 1:
  "Never compromise source accuracy for answer fluency."

It is NOT enough to tell the LLM "only cite real sources" — LLMs
hallucinate.  This validator catches that.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from app.models.schemas import LegalResponse
from app.retrieval.base import RetrievedChunk


@dataclass
class ValidationResult:
    """Result of validating one LLM response."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)    # What failed
    warnings: List[str] = field(default_factory=list)  # Non-fatal issues


class BaseValidator(ABC):
    """
    Interface for response validators.

    Every validator checks that:
    1. Every source_id in the response exists in the approved corpus.
    2. Every quote appears word-for-word in the corresponding chunk.
    3. Every case name exists in the approved judgment list.
    4. Section/article numbers match the source text.

    If validation fails, the pipeline returns "insufficient_evidence"
    instead of the flawed answer.
    """

    @abstractmethod
    def validate(
        self,
        response: LegalResponse,
        context_chunks: List[RetrievedChunk],
        approved_sources: dict,
    ) -> ValidationResult:
        """
        Validate the LLM's response against the retrieved chunks
        and the approved source registry.
        """
        ...
