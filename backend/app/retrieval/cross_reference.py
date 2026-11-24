"""
Cross-Reference Resolver for Legal Provisions.
Extracts internal statutory cross-references (e.g. 'under section 35', 'Article 13')
from retrieved text and retrieves cited provisions to guarantee context completeness.
"""

import re
from typing import List, Optional
from app.retrieval.base import RetrievedChunk


class CrossReferenceResolver:
    """
    Identifies and resolves cross-statutory citations in legal provisions.
    """

    @classmethod
    def extract_citations(cls, text: str, current_provision: str = "") -> List[str]:
        """
        Extracts cited Section or Article numbers from passage text.
        Excludes the passage's own section to avoid self-reference.
        """
        citations: List[str] = []
        curr_clean = current_provision.strip().lower()

        # Match Section \d+ and Article \d+
        sec_matches = re.findall(r"\bsection\s+(\d+[A-Z]?)\b", text, re.IGNORECASE)
        art_matches = re.findall(r"\barticle\s+(\d+[A-Z]?)\b", text, re.IGNORECASE)

        for s in sec_matches:
            formatted = f"Section {s}"
            if formatted.lower() != curr_clean and formatted not in citations:
                citations.append(formatted)

        for a in art_matches:
            formatted = f"Article {a}"
            if formatted.lower() != curr_clean and formatted not in citations:
                citations.append(formatted)

        return citations
