"""
M5 Concrete Response Validator.
Enforces code-level source accuracy, citation integrity, verbatim quotes,
and grounded support checks before any response is delivered to the user.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from app.models.schemas import AnswerStatus, LegalResponse
from app.retrieval.base import RetrievedChunk
from app.validation.base import BaseValidator, ValidationResult

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def load_approved_sources(sources_path: Optional[Path] = None) -> dict:
    """Load sources.yaml and return dict keyed by source id."""
    path = sources_path or (BASE_DIR / "data" / "sources.yaml")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    sources = data.get("sources", [])
    return {s["id"]: s for s in sources if isinstance(s, dict) and "id" in s}


def load_section_mappings(mappings_dir: Optional[Path] = None) -> Dict[str, set]:
    """
    Load crpc_to_bnss.yaml and ipc_to_bns.yaml to map sections bidirectionally.
    Returns dict mapping section number string (e.g. '479') to set of equivalent section numbers (e.g. {'479', '436A'}).
    """
    map_dir = mappings_dir or (BASE_DIR / "data" / "mappings")
    equiv_map: Dict[str, set] = {}
    if not map_dir.exists():
        return equiv_map

    for yml in map_dir.glob("*.yaml"):
        try:
            with open(yml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            mappings = data.get("mappings", [])
            for m in mappings:
                for sec_entry in m.get("sections", []):
                    old_sec_str = str(sec_entry.get("old_section", ""))
                    new_sec_str = str(sec_entry.get("new_section", ""))
                    old_nums = re.findall(r"\b(\d+[A-Z]?)\b", old_sec_str)
                    new_nums = re.findall(r"\b(\d+[A-Z]?)\b", new_sec_str)
                    all_nums = {n.upper() for n in old_nums + new_nums}
                    for n in all_nums:
                        if n not in equiv_map:
                            equiv_map[n] = set()
                        equiv_map[n].update(all_nums)
        except Exception:
            pass
    return equiv_map


def normalize_whitespace(text: str) -> str:
    """Normalize any sequence of whitespace chars to a single space."""
    return " ".join(text.strip().split())


class LegalResponseValidator(BaseValidator):
    """
    Validates legal responses against retrieved context and sources.yaml.
    """

    def __init__(
        self,
        sources_registry: Optional[dict] = None,
        section_mappings: Optional[dict] = None,
    ):
        self.approved_sources = (
            sources_registry
            if sources_registry is not None
            else load_approved_sources()
        )
        self.section_mappings = (
            section_mappings
            if section_mappings is not None
            else load_section_mappings()
        )

    def validate(
        self,
        response: LegalResponse,
        context_chunks: List[RetrievedChunk],
        approved_sources: Optional[dict] = None,
    ) -> ValidationResult:
        sources_to_check = approved_sources or self.approved_sources
        errors: List[str] = []
        warnings: List[str] = []

        # If answer is not ANSWERED (e.g., out_of_scope or insufficient_evidence),
        # minimal validation applies
        if response.status != AnswerStatus.ANSWERED:
            if not response.disclaimer:
                errors.append("Disclaimer is mandatory.")
            return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

        # 1. Structure validation
        if not response.short_answer:
            errors.append("Answer marked as ANSWERED but short_answer is missing.")
            return ValidationResult(is_valid=False, errors=errors)

        if not response.disclaimer:
            errors.append("Disclaimer is mandatory.")

        if not response.details:
            errors.append("Answer marked as ANSWERED but source details list is empty.")
            return ValidationResult(is_valid=False, errors=errors)

        # Build context lookup
        context_texts = [normalize_whitespace(c.text) for c in context_chunks]
        all_context_combined = " ".join(context_texts)
        all_context_meta = [c.metadata for c in context_chunks]

        # 2. Citation Validator
        # Every source_id must exist in sources.yaml and in context_chunks
        retrieved_source_ids = {c.source_id for c in context_chunks}
        retrieved_locations = {
            c.metadata.get("location", "").strip() for c in context_chunks if c.metadata.get("location")
        }

        for i, detail in enumerate(response.details):
            # Check source_id in sources.yaml
            if detail.source_id not in sources_to_check:
                errors.append(
                    f"Detail [{i}]: source_id '{detail.source_id}' is not in approved sources.yaml."
                )

            # Check source_id in retrieved chunks
            if detail.source_id not in retrieved_source_ids:
                errors.append(
                    f"Detail [{i}]: source_id '{detail.source_id}' was not present in retrieved context."
                )

            # Check location if provided
            if detail.location and detail.location not in retrieved_locations:
                # Also accept if location is substring of any retrieved location
                if not any(detail.location in loc for loc in retrieved_locations):
                    warnings.append(
                        f"Detail [{i}]: location '{detail.location}' not strictly matching retrieved chunk locations."
                    )

            # 3. Quote Validator
            # Every quote must appear word-for-word in the source chunk (whitespace-normalized)
            if not detail.quote or len(detail.quote.strip()) < 5:
                errors.append(f"Detail [{i}]: quote is missing or too short.")
            else:
                norm_quote = normalize_whitespace(detail.quote).rstrip(".")
                quote_found = False
                for c_text in context_texts:
                    if norm_quote.lower() in c_text.lower():
                        quote_found = True
                        break
                if not quote_found:
                    errors.append(
                        f"Detail [{i}]: quote does not appear verbatim in any retrieved chunk: '{detail.quote[:60]}...'"
                    )

        # 4. Support Check
        # Check all sentences in short_answer and key_points
        all_output_text = " ".join([
            response.short_answer.simple or "",
            response.short_answer.detailed or "",
            " ".join(response.key_points or []),
        ])

        # Check: No article numbers mentioned that do not exist in retrieved text or metadata
        mentioned_articles = set(re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", all_output_text, re.IGNORECASE))
        context_articles = set()
        for meta in all_context_meta:
            for val in meta.values():
                if isinstance(val, str):
                    for m in re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", val, re.IGNORECASE):
                        context_articles.add(m.upper())
                    for m in re.findall(r"^\s*(\d+[A-Z]?)\s*$", val):
                        context_articles.add(m.upper())
        for m in re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", all_context_combined, re.IGNORECASE):
            context_articles.add(m.upper())

        for art in mentioned_articles:
            if art.upper() not in context_articles:
                errors.append(
                    f"Support check failed: Article {art} is mentioned in answer but absent from retrieved text/metadata."
                )

        # Check: No section numbers mentioned that do not exist in retrieved text or metadata
        mentioned_sections = set(re.findall(r"\bSection\s+(\d+[A-Z]?)\b", all_output_text, re.IGNORECASE))
        context_sections = set()
        for meta in all_context_meta:
            for val in meta.values():
                if isinstance(val, str):
                    for sec in re.findall(r"\bSection\s+(\d+[A-Z]?)\b", val, re.IGNORECASE):
                        context_sections.add(sec.upper())
                    for sec in re.findall(r"^\s*(\d+[A-Z]?)\s*$", val):
                        context_sections.add(sec.upper())
        for m in re.findall(r"\bSection\s+(\d+[A-Z]?)\b", all_context_combined, re.IGNORECASE):
            context_sections.add(m.upper())

        # Expand sections with statutory mappings (e.g. CrPC Section 436A <-> BNSS Section 479)
        if hasattr(self, "section_mappings") and self.section_mappings:
            mapped_expansion = set()
            for sec in list(context_sections):
                if sec in self.section_mappings:
                    mapped_expansion.update(self.section_mappings[sec])
            context_sections.update(mapped_expansion)

        for sec in mentioned_sections:
            if sec.upper() not in context_sections:
                errors.append(
                    f"Support check failed: Section {sec} is mentioned in answer but absent from retrieved text/metadata."
                )

        # Check: Case names mentioned in related_judgments must be in sources.yaml
        for rj in response.related_judgments:
            if rj.source_id not in sources_to_check:
                errors.append(
                    f"Judgment source_id '{rj.source_id}' is not in approved sources.yaml."
                )

        # Check: Check question alignment for specific articles/sections queried
        # If question asks specifically for e.g. "Article 999", it must be in context
        query_articles = re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", response.question, re.IGNORECASE)
        for q_art in query_articles:
            if q_art.upper() not in context_articles:
                errors.append(
                    f"Question specifically asks for Article {q_art}, which is not in retrieved context."
                )

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
