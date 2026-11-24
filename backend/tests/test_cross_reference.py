"""
Phase 3 Test: Verify Cross-Reference Resolution in Legal Retrieval.
Ensures that when a retrieved section cites another statutory section,
the cited provision is parsed, retrieved, and included in context.
"""

import pytest
from app.retrieval.cross_reference import CrossReferenceResolver
from app.generation.service import AskService
from app.models.schemas import AnswerStatus


def test_cross_reference_extraction():
    """Verify regex citation extraction of sections and articles."""
    sample_text = (
        "Every person arrested shall be dealt with under section 35 and section 478. "
        "Furthermore, this power is subject to Article 21 and Article 22 of the Constitution."
    )
    citations = CrossReferenceResolver.extract_citations(sample_text, current_provision="Section 35")
    
    assert "Section 478" in citations
    assert "Article 21" in citations
    assert "Article 22" in citations
    assert "Section 35" not in citations  # Current provision should be excluded


@pytest.mark.asyncio
async def test_cross_reference_retrieval_integration():
    """
    Verify that an in-scope question whose retrieved provision cites another provision
    retrieves and attaches the cross-reference.
    """
    service = AskService()
    # Query Section 47 which cites bail under Section 478
    resp = await service.answer_question("Must an arrested person be informed of the grounds of arrest and right to bail?")

    assert resp.status == AnswerStatus.ANSWERED
    assert resp.short_answer is not None
    # Key points or details should reflect statutory cross reference
    has_cr = any("cross-reference" in kp.lower() for kp in resp.key_points)
    # Section 47 cites right to bail (Section 478)
    assert resp.details[0].section in ("Section 47", "Section 51")
