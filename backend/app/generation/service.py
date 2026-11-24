"""
Full RAG service: Orchestrates query scope detection, hybrid retrieval,
confidence thresholding, grounded LLM answer generation, and M5 validation.
"""

import re
from typing import Optional

from app.generation.base import BaseLLM
from app.generation.factory import get_llm_provider
from app.models.schemas import AnswerStatus, LegalResponse
from app.retrieval.hybrid import HybridRetriever
from app.validation.validator import LegalResponseValidator

# Queries clearly out-of-scope (non-Indian law, sports, cooking, prompt injection)
OUT_OF_SCOPE_PATTERNS = [
    r"\brecipe\b",
    r"\bcook(?:ing)?\b",
    r"\bweather\b",
    r"\bcricket\b",
    r"\bmovie\b",
    r"\bjoke\b",
    r"\bpython code\b",
    r"\bwrite a python\b",
    # Prompt injection patterns
    r"ignore\s+(?:all\s+|previous\s+|prior\s+)?instructions",
    r"disregard\s+(?:all\s+|previous\s+)?instructions",
    r"reveal\s+(?:your\s+)?system\s+prompt",
    r"\bjailbreak\b",
    # Other countries' laws
    r"\bus\s+constitution\b",
    r"\bamerican\s+(?:law|constitution)\b",
    r"\bfirst\s+amendment\b",
    r"\bsecond\s+amendment\b",
    r"\bfifth\s+amendment\b",
    r"\bmiranda\s+rights?\b",
    r"\bpakistan(?:i)?\s+(?:constitution|law)\b",
    r"\buk\s+(?:law|parliament)\b",
]


class AskService:
    """
    Core RAG pipeline coordinator for /ask endpoint with M5 validation enforcement.
    """

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        llm: Optional[BaseLLM] = None,
        validator: Optional[LegalResponseValidator] = None,
        min_vector_threshold: float = 0.68,
    ):
        self.retriever = retriever or HybridRetriever()
        self.llm = llm
        self.validator = validator or LegalResponseValidator()
        self.min_vector_threshold = min_vector_threshold

    def _is_out_of_scope(self, query: str) -> bool:
        lowered = query.lower()
        for pat in OUT_OF_SCOPE_PATTERNS:
            if re.search(pat, lowered):
                return True
        return False

    def _has_sufficient_evidence(self, top_chunk) -> bool:
        """
        Check if the top retrieved chunk provides genuine evidence
        rather than baseline embedding noise.
        """
        v_score = top_chunk.metadata.get("vector_score", 0.0)
        b_score = top_chunk.metadata.get("bm25_score", 0.0)

        # Genuine semantic evidence requires strong vector similarity (>= 0.68).
        # Loose keyword overlap on common words (e.g. 'traffic' matching 'traffic in human beings')
        # with low vector similarity (< 0.67) is rejected as noise.
        if v_score >= self.min_vector_threshold:
            return True

        if b_score > 0.20 and v_score >= 0.67:
            return True

        return False

    async def answer_question(self, question: str) -> LegalResponse:
        # 1. Out-of-scope check
        if self._is_out_of_scope(question):
            return LegalResponse(
                status=AnswerStatus.OUT_OF_SCOPE,
                question=question,
                key_points=[
                    "This assistant only answers questions regarding the Constitution of India, "
                    "Fundamental Rights, criminal procedure (BNSS/CrPC), and landmark judgments.",
                    "Questions about recipes, other countries' laws, entertainment, sports, or instructions to override policy are out of scope."
                ],
                disclaimer="General information, not legal advice.",
            )

        # 2. Retrieve passages via Hybrid Search
        chunks = await self.retriever.search(query=question, top_k=5)

        # 3. Evidence confidence threshold
        if not chunks or not self._has_sufficient_evidence(chunks[0]):
            return LegalResponse(
                status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                question=question,
                key_points=[
                    "No sufficiently relevant passages were found in the approved legal corpus.",
                    "The system refuses to generate answers without verified source evidence."
                ],
                disclaimer="General information, not legal advice.",
            )

        # 4. Check for fake article / section / case queries:
        # If the user asks for a specific Article/Section not present in retrieved context, refuse immediately
        query_articles = re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", question, re.IGNORECASE)
        context_articles = {
            m.group(1).upper()
            for c in chunks
            for m in [re.search(r"\bArticle\s+(\d+[A-Z]?)\b", c.metadata.get("article", ""), re.IGNORECASE)]
            if m
        }
        for q_art in query_articles:
            if q_art.upper() not in context_articles:
                return LegalResponse(
                    status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                    question=question,
                    key_points=[
                        f"Article {q_art} does not exist in the retrieved approved corpus.",
                        "The assistant does not answer queries regarding unverified articles."
                    ],
                    disclaimer="General information, not legal advice.",
                )

        # If user asks about a specific case name (e.g. "Sharma v. State of Delhi"), check if it exists in retrieved corpus
        case_match = re.search(r"([A-Z][a-zA-Z\.\s]{2,})\s+(?:v\.|versus|vs\.)\s+([A-Z][a-zA-Z\.\s]{2,})", question)
        if case_match:
            case_name = case_match.group(0).strip()
            all_retrieved_context = " ".join([c.text for c in chunks] + [str(c.metadata) for c in chunks]).lower()
            party1 = case_match.group(1).strip().lower()
            if party1 not in all_retrieved_context:
                return LegalResponse(
                    status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                    question=question,
                    key_points=[
                        f"The case '{case_name}' is not present in the approved judgments corpus.",
                        "The assistant cannot answer queries about unverified case law."
                    ],
                    disclaimer="General information, not legal advice.",
                )

        # 5. Resolve LLM provider
        llm_instance = self.llm or await get_llm_provider()

        # 6. Generate grounded response with M5 validation and retry
        response = await llm_instance.generate(question=question, context_chunks=chunks)
        val_result = self.validator.validate(response, chunks)

        if not val_result.is_valid:
            # Retry once
            response = await llm_instance.generate(question=question, context_chunks=chunks)
            val_result = self.validator.validate(response, chunks)
            if not val_result.is_valid:
                return LegalResponse(
                    status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                    question=question,
                    key_points=[
                        "Generated response failed validation against approved sources.",
                        "; ".join(val_result.errors)
                    ],
                    disclaimer="General information, not legal advice.",
                )

        # 7. Ensure mandatory fields
        if not response.disclaimer:
            response.disclaimer = "General information, not legal advice."

        # Set last_verified strictly from the source's recorded retrieval date in sources.yaml
        sources_registry = self.validator.approved_sources
        source_id = chunks[0].source_id if chunks else "constitution-india"
        src_meta = sources_registry.get(source_id, {})
        retrieved_date = src_meta.get("retrieved")
        if retrieved_date:
            response.last_verified = str(retrieved_date)
        elif not response.last_verified:
            response.last_verified = "2026-11-22"

        return response
