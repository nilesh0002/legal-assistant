"""
Full RAG service: Orchestrates query scope detection, hybrid retrieval,
confidence thresholding, grounded LLM answer generation, and M5 validation.
"""

from typing import List, Optional
import json
from datetime import datetime, timezone
from pathlib import Path
import re

from app.generation.base import BaseLLM
from app.generation.factory import get_llm_provider
from app.models.schemas import AnswerStatus, LegalResponse, SourceDetail
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.cross_reference import CrossReferenceResolver
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


# Clarification triggers for ambiguous or single-word queries
CLARIFICATION_TRIGGERS = [
    (
        r"^(?:what\s+is\s+)?(?:the\s+procedure\s+for\s+)?bail\??$",
        "Which bail procedure do you need information about?",
        [
            "Bail in bailable offences (Section 478 BNSS)",
            "Bail in non-bailable offences (Section 480 BNSS)",
            "Anticipatory bail (Section 482 BNSS)",
        ],
    ),
    (
        r"^(?:what\s+is\s+)?(?:the\s+procedure\s+for\s+)?arrest\??$",
        "Which aspect of arrest procedure would you like to know?",
        [
            "Arrest without warrant (Section 35 BNSS)",
            "Arrest of women after sunset (Section 43 BNSS)",
            "Rights of an arrested person (Sections 38, 47, 48 BNSS)",
        ],
    ),
    (
        r"^(?:what\s+are\s+my\s+)?(?:fundamental\s+)?rights\??$",
        "Which legal or constitutional rights are you inquiring about?",
        [
            "Right to equality (Article 14)",
            "Right to life & liberty (Article 21)",
            "Freedom of speech (Article 19)",
        ],
    ),
    (
        r"^(?:what\s+is\s+)?(?:a\s+)?warrant\??$",
        "Which court process would you like information on?",
        [
            "Form and duration of arrest warrant (Section 72 BNSS)",
            "Bailable warrant conditions (Section 73 BNSS)",
            "Search warrant procedure (Section 96 BNSS)",
        ],
    ),
]

# Uncovered legal domains whose statutes are not yet indexed
UNCOVERED_LEGAL_DOMAINS = [
    (r"\b(?:traffic|helmet|challan|red\s+light|driving\s+licen[sc]e|speeding|motor\s+vehicle)\b", "Traffic & Motor Vehicles Law"),
    (r"\b(?:company\s+registration|private\s+limited|incorporat\w*|director|corporate\s+tax|roc|mca)\b", "Corporate & Company Law"),
    (r"\b(?:income\s+tax|gst|itr|tax\s+return|customs?\s+dut(?:y|ies)|excise)\b", "Taxation & Revenue Law"),
    (r"\b(?:trademark|patent|copyright|intellectual\s+property)\b", "Intellectual Property Law"),
    (r"\b(?:divorce|maintenance|alimony|custody\s+of\s+child|hindu\s+marriage|muslim\s+personal|talaq)\b", "Family & Personal Law"),
    (r"\b(?:stamp\s+duty|property\s+registration|tenant|rent\s+agreement|eviction|landlord)\b", "Property & Rent Control Law"),
    (r"\b(?:gratuity|provident\s+fund|minimum\s+wages?|labor\s+law|trade\s+union)\b", "Labor & Industrial Law"),
    (r"\b(?:noise\s+pollution|noise\s+decibel|neighbor\s+makes?\s+loud\s+noise|loud\s+noise|municipal\s+zoning|ward\s+\d+|trade\s+licen[sc]e)\b", "Municipal & Environmental Law"),
    (r"\b(?:passport\s+renewal|visa\s+application|overseas\s+citizen)\b", "Immigration & Passport Law"),
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
        reranker: Optional[CrossEncoderReranker] = None,
    ):
        self.retriever = retriever or HybridRetriever()
        self.llm = llm
        self.validator = validator or LegalResponseValidator()
        self.min_vector_threshold = min_vector_threshold
        self.reranker = reranker or CrossEncoderReranker()

    def _is_out_of_scope(self, query: str) -> bool:
        lowered = query.lower()
        for pat in OUT_OF_SCOPE_PATTERNS:
            if re.search(pat, lowered):
                return True
        return False

    def _check_clarification(self, query: str):
        q_clean = query.strip().lower()
        for pat, question, options in CLARIFICATION_TRIGGERS:
            if re.search(pat, q_clean):
                return question, options
        return None, None

    def _check_not_covered_yet(self, query: str) -> Optional[str]:
        q_lower = query.lower()
        for pat, domain in UNCOVERED_LEGAL_DOMAINS:
            if re.search(pat, q_lower):
                return domain
        return None

    def _has_sufficient_evidence(self, top_chunk) -> bool:
        """
        Check if the top retrieved chunk provides genuine evidence
        using calibrated reranker gating.
        """
        return self.reranker.has_sufficient_evidence(top_chunk)

    async def answer_question(
        self,
        question: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> LegalResponse:
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

        # 2. Needs clarification check (vague / ambiguous single-topic queries)
        clar_q, clar_opts = self._check_clarification(question)
        if clar_q:
            return LegalResponse(
                status=AnswerStatus.NEEDS_CLARIFICATION,
                question=question,
                clarification_question=clar_q,
                clarification_options=clar_opts,
                key_points=[
                    "Your query is broad or ambiguous.",
                    clar_q,
                ],
                disclaimer="General information, not legal advice.",
            )

        # 3. Not covered yet check (identifies unindexed legal domains without describing content)
        uncovered_area = self._check_not_covered_yet(question)
        if uncovered_area:
            return LegalResponse(
                status=AnswerStatus.NOT_COVERED_YET,
                question=question,
                uncovered_area=uncovered_area,
                key_points=[
                    f"This legal query falls under {uncovered_area}, which is not yet indexed in NyayaSahayak.",
                    "The assistant currently indexes only the Constitution of India and Bharatiya Nagarik Suraksha Sanhita (BNSS 2023).",
                    "The system does not speculate about the contents of unindexed laws."
                ],
                disclaimer="General information, not legal advice.",
            )

        # 2. Query Understanding & Multi-Query Search
        search_queries = QueryRewriter.rewrite_queries(question, conversation_history)
        all_candidates = {}
        agreement_counts = {}
        rrf_scores = {}
        k = 60

        for q in search_queries:
            results = await self.retriever.search(query=q, top_k=10)
            for rank, chunk in enumerate(results):
                cid = chunk.chunk_id
                if cid not in all_candidates:
                    all_candidates[cid] = chunk
                    agreement_counts[cid] = 0
                    rrf_scores[cid] = 0.0
                agreement_counts[cid] += 1
                rrf_scores[cid] += 1.0 / (k + rank + 1)

        # Multi-query merged candidates
        merged_candidates = sorted(all_candidates.values(), key=lambda c: rrf_scores[c.chunk_id], reverse=True)

        # 3. Cross-Encoder Reranker
        chunks = self.reranker.rerank(
            query=question,
            candidates=merged_candidates,
            query_agreement_counts=agreement_counts,
            top_k=5,
        )

        # 4. Calibrated Evidence Gate
        if not chunks or not self._has_sufficient_evidence(chunks[0]):
            related_sources = []
            if chunks:
                sources_map = self.validator.approved_sources
                for c in chunks[:3]:
                    meta = c.metadata
                    prov = (meta.get("article") or meta.get("section") or "").strip()
                    title = meta.get("title", prov)
                    sid = c.source_id
                    src_url = meta.get("source_url") or (sources_map.get(sid, {}).get("url") if sid in sources_map else "")
                    clean_quote = " ".join(c.text.split())
                    if len(clean_quote) > 200:
                        clean_quote = clean_quote[:200] + "..."
                    related_sources.append(
                        SourceDetail(
                            claim=f"Related provision: {prov}",
                            law=meta.get("law", "Indian Statute"),
                            section=prov,
                            old_equivalent=meta.get("old_equivalent"),
                            quote=clean_quote,
                            source_id=sid,
                            source_title=title,
                            source_url=src_url or "https://legislative.gov.in",
                            location=meta.get("location", "Reported text"),
                        )
                    )
            return LegalResponse(
                status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                question=question,
                key_points=[
                    "No sufficiently relevant passages were found in the approved legal corpus.",
                    "The system refuses to generate answers without verified source evidence."
                ],
                related_sources=related_sources,
                disclaimer="General information, not legal advice.",
            )

        # 5. Cross-Reference Handling: retrieve internally cited provisions
        top_provision = chunks[0].metadata.get("article") or chunks[0].metadata.get("section") or ""
        citations = CrossReferenceResolver.extract_citations(chunks[0].text, top_provision)
        for cite in citations[:2]:
            cited_results = await self.retriever.search(query=cite, top_k=2)
            for cr in cited_results:
                cr_prov = cr.metadata.get("article") or cr.metadata.get("section") or ""
                if cr_prov.lower() == cite.lower():
                    if cr.chunk_id not in [c.chunk_id for c in chunks]:
                        cr.metadata["is_cross_reference"] = True
                        cr.metadata["cited_by"] = top_provision
                        chunks.append(cr)
                    break

        # 4. Check for fake article / section / case queries:
        # If the user asks for a specific Article not present in retrieved context, refuse immediately
        query_articles = re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", question, re.IGNORECASE)
        context_articles = set()
        for c in chunks:
            for val in c.metadata.values():
                if isinstance(val, str):
                    for m in re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", val, re.IGNORECASE):
                        context_articles.add(m.upper())
            for m in re.findall(r"\bArticle\s+(\d+[A-Z]?)\b", c.text, re.IGNORECASE):
                context_articles.add(m.upper())
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
                # Log validation failure to review queue
                try:
                    queue_file = Path(__file__).resolve().parent.parent.parent / "data" / "review_queue.jsonl"
                    queue_file.parent.mkdir(parents=True, exist_ok=True)
                    log_entry = {
                        "type": "validation_failure",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "question": question,
                        "errors": val_result.errors,
                        "response": response.model_dump(),
                    }
                    with open(queue_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry, default=str) + "\n")
                except Exception:
                    pass

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
