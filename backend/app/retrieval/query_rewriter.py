"""
Query Understanding & Lay-to-Legal Reformulation.
Rewrites ordinary citizen phrasing into legal statutory search terms,
and resolves follow-up conversational turns.
Uses LLM-based rewriting when a real LLM is available, with rule-based fallback.
Strictly uses question text; never injects external legal facts into answers.
"""

from abc import ABC, abstractmethod
import json
import re
from typing import List, Optional


# Lay Phrasing to Statutory Legal Search Term Concepts (Search Hints Only)
LEGAL_CONCEPT_REWRITES = [
    (
        r"\b(?:without\s+(?:a\s+)?warrant|arrest\s+without\s+warrant)\b",
        "when police may arrest without warrant cognizable offence credible information",
        "arrest without warrant procedure of arrest",
    ),
    (
        r"\b(?:bailable\s+offences?|bailable\s+cases?)\b",
        "in what cases bail to be taken bailable offence discharge on bail",
        "procedure for bail in bailable offences",
    ),
    (
        r"\b(?:medical\s+examination|medical\s+checkup|examined\s+by\s+doctor)\b",
        "examination of accused by medical practitioner examination of arrested person",
        "medical officer examination of person arrested",
    ),
    (
        r"\b(?:enter(?:\s+my)?\s+house|enter(?:\s+a)?\s+home|inside\s+house|break\s+in)\b",
        "search of place entered by person sought to be arrested entry without warrant",
        "ingress to place entered search of closed place",
    ),
    (
        r"\b(?:at\s+night|after\s+sunset|before\s+sunrise|night\s+arrest)\b",
        "arrest of woman after sunset and before sunrise exceptional circumstances prior permission of magistrate",
        "arrest of female woman police officer sunset sunrise",
    ),
    (
        r"\b(?:woman|female|lady|girl)\s+(?:arrest|detain|custody)\b",
        "arrest of female woman police officer oral intimation submission to custody sunset sunrise",
        "search of arrested female woman medical examination",
    ),
    (
        r"\b(?:how\s+long|maximum\s+time|custody\s+limit|time\s+limit)\b",
        "twenty-four hours detention production before magistrate without delay",
        "procedure when investigation cannot be completed in twenty-four hours police custody judicial custody",
    ),
    (
        r"\b(?:anticipatory\s+bail|advance\s+bail|apprehending\s+arrest|fear\s+of\s+arrest)\b",
        "direction for grant of bail to person apprehending arrest High Court Court of Session",
        "anticipatory bail non-bailable offence",
    ),
    (
        r"\b(?:bail|get\s+bail|bail\s+procedure|process\s+for\s+bail|processor\s+for\s+bail)\b",
        "in what cases bail to be taken bailable offence non-bailable offence",
        "maximum period for which undertrial prisoner can be detained bail and bonds",
    ),
    (
        r"\b(?:police\s+beat|torture|handcuff|custodial\s+violence|police\s+force)\b",
        "no unnecessary restraint health and safety of arrested person",
        "use handcuff nature and gravity of offence medical examination",
    ),
    (
        r"\b(?:lawyer|advocate|consult\s+lawyer|meet\s+lawyer)\b",
        "right of arrested person to meet an advocate of his choice during interrogation",
        "advocate choice interrogation",
    ),
    (
        r"\b(?:inform\s+family|call\s+relative|inform\s+friend|nominated\s+person)\b",
        "obligation of person making arrest to inform nominated person about arrest",
        "grounds of arrest right to bail inform relative designated police officer",
    ),
    (
        r"\b(?:phone|mobile|video|record|recording|camera|electronic)\b",
        "recording of search and seizure through audio-video electronic means",
        "seizure of property summons to produce document or thing",
    ),
    (
        r"(?<!without\s)(?<!without\sa\s)\b(?:warrant|summons|court\s+order)\b",
        "form of summons summons how served form of warrant of arrest and duration",
        "warrant of arrest bailable warrant direction security",
    ),
    (
        r"\b(?:slap(?:ped|ping)?|punch(?:ed|ing)?|hit(?:ting)?|push(?:ed|ing)?|shov(?:e|ed|ing)|beat(?:ing)?|hurt(?:ing)?|assault(?:ed|ing)?|kick(?:ed|ing)?)\b",
        "hurt voluntarily causing hurt bodily pain criminal force assault",
        "punishment for assault or criminal force without consent",
    ),
    (
        r"\b(?:weapon|knife|stick|rod|stone|blade|acid|sharp)\b",
        "voluntarily causing hurt or grievous hurt by dangerous weapons or means",
        "grievous hurt dangerous weapon punishment",
    ),
    (
        r"\b(?:threat(?:en|ened|ening)?|intimidat(?:e|ed|ing)|scare|blackmail)\b",
        "criminal intimidation threatens another with injury to person reputation or property",
        "extortion putting person in fear of injury",
    ),
    (
        r"\b(?:fight(?:ing)?|quarrel|brawl|scuffle|neighbour)\b",
        "affray two or more persons fighting in a public place disturbing public peace",
        "voluntarily causing hurt assault criminal force",
    ),
    (
        r"\b(?:steal|stolen|theft|pickpocket|snatch(?:ed|ing)?)\b",
        "theft intending to take dishonestly movable property out of possession without consent",
        "robbery snatching extortion",
    ),
    (
        r"\b(?:cheat(?:ed|ing)?|scam(?:med)?|fraud|duped|fake\s+promise)\b",
        "cheating deceiving fraudulently or dishonestly inducing delivery of property",
        "criminal breach of trust dishonest misappropriation",
    ),
    (
        r"\b(?:defam(?:e|ed|ing|ation)|rumour|slander|libel|insult)\b",
        "defamation imputation harming reputation of person",
        "criminal intimidation insult",
    ),
    (
        r"\b(?:trespass|broke\s+into|broken\s+into|unlawful\s+entry)\b",
        "criminal trespass house-trespass lurking house-breaking",
        "offence against property",
    ),
    (
        r"\b(?:defective|faulty|damaged|refund|misleading\s+ad|consumer|shopkeeper|seller)\b",
        "consumer complaint unfair trade practice product liability manufacturer defect",
        "District Commission limitation period consumer protection",
    ),
    (
        r"\b(?:rti|right\s+to\s+information|public\s+information\s+officer|pio|government\s+records?)\b",
        "right to information request disposal thirty days public information officer",
        "exemption from disclosure penalty on public information officer",
    ),
]


class BaseQueryRewriter(ABC):
    """Interface for query rewriting implementations."""

    @abstractmethod
    def rewrite_queries(
        self,
        question: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> List[str]:
        pass


class QueryRewriter(BaseQueryRewriter):
    """
    Expands conversational and lay legal queries into targeted statutory search queries.
    Acts as deterministic rule-based fallback when no external LLM is available.
    """

    @classmethod
    def resolve_conversation(
        cls,
        question: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """
        Resolves follow-up queries using previous turns (last 2 max).
        """
        if not conversation_history:
            return question.strip()

        q_lower = question.strip().lower()
        is_followup = bool(re.match(r"^(?:what\s+about|and\s+for|how\s+about|and\s+if|what\s+if|can\s+they\s+also)\b", q_lower))

        if is_followup and len(conversation_history) > 0:
            last_turn = conversation_history[-1]
            last_q = last_turn.get("question", "") if isinstance(last_turn, dict) else ""
            if last_q:
                cleaned_base = re.sub(r"\?+$", "", last_q.strip())
                cleaned_followup = re.sub(r"^(?:what\s+about|and\s+for|how\s+about|and\s+if|what\s+if)\s+", "", q_lower).rstrip("?")
                return f"{cleaned_base} {cleaned_followup}?"

        return question.strip()

    @classmethod
    def rewrite_queries(
        cls,
        question: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> List[str]:
        """
        Produces 2 to 3 search queries:
        1. Resolved original question
        2. Legal statutory search hint 1
        3. Legal statutory search hint 2 (if concepts matched)
        """
        resolved_q = cls.resolve_conversation(question, conversation_history)
        queries = [resolved_q]

        matched_rewrites = []
        resolved_lower = resolved_q.lower()
        for pattern, r1, r2 in LEGAL_CONCEPT_REWRITES:
            if re.search(pattern, resolved_lower):
                matched_rewrites.append(r1)
                if r2:
                    matched_rewrites.append(r2)

        if matched_rewrites:
            for r in matched_rewrites[:2]:
                if r not in queries:
                    queries.append(r)

        return queries

    @classmethod
    async def rewrite_queries_async(
        cls,
        question: str,
        conversation_history: Optional[List[dict]] = None,
        llm=None,
    ) -> List[str]:
        """
        Uses an LLM to rewrite the lay question into 2-3 legal search queries
        when a real LLM is available (and not LocalGroundedLLM), falling back
        to rule-based search hints otherwise.
        Rewrites are used strictly for retrieval and never as answer content.
        """
        resolved_q = cls.resolve_conversation(question, conversation_history)
        if llm is not None and llm.__class__.__name__ != "LocalGroundedLLM":
            try:
                if hasattr(llm, "rewrite_search_queries"):
                    llm_queries = await llm.rewrite_search_queries(resolved_q)
                    if llm_queries and isinstance(llm_queries, list):
                        merged = [resolved_q] + [str(q).strip() for q in llm_queries if str(q).strip()]
                        return list(dict.fromkeys(merged))[:4]
            except Exception:
                pass

        return cls.rewrite_queries(question, conversation_history)
