"""
Query Understanding & Lay-to-Legal Reformulation.
Rewrites ordinary citizen phrasing into legal statutory search terms,
and resolves follow-up conversational turns.
Strictly uses question text; never injects external legal facts into answers.
"""

import re
from typing import List, Optional


# Lay Phrasing to Statutory Legal Search Term Concepts
LEGAL_CONCEPT_REWRITES = [
    (
        r"\b(?:without\s+(?:a\s+)?warrant|arrest\s+without\s+warrant)\b",
        "when police may arrest without warrant cognizable offence credible information Section 35",
        "arrest without warrant procedure of arrest",
    ),
    (
        r"\b(?:bailable\s+offences?|bailable\s+cases?)\b",
        "in what cases bail to be taken bailable offence discharge on bail Section 478",
        "procedure for bail in bailable offences",
    ),
    (
        r"\b(?:medical\s+examination|medical\s+checkup|examined\s+by\s+doctor)\b",
        "examination of accused by medical practitioner examination of arrested person Section 51 Section 53",
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
        r"\b(?:police\s+beat|torture|handcuff|beating|violence\b|force\b)",
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
]


class QueryRewriter:
    """
    Expands conversational and lay legal queries into targeted statutory search queries.
    """

    @classmethod
    def resolve_conversation(
        cls,
        question: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """
        Resolves follow-up queries using previous turns (last 2 max).
        e.g., 'what about at night?' -> 'When can police arrest without warrant at night?'
        """
        if not conversation_history:
            return question.strip()

        q_lower = question.strip().lower()
        is_followup = bool(re.match(r"^(?:what\s+about|and\s+for|how\s+about|and\s+if|what\s+if|can\s+they\s+also)\b", q_lower))

        if is_followup and len(conversation_history) > 0:
            last_turn = conversation_history[-1]
            last_q = last_turn.get("question", "") if isinstance(last_turn, dict) else ""
            if last_q:
                # Merge topic from last question with current modifier
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
        2. Legal statutory rewrite 1
        3. Legal statutory rewrite 2 (if concepts matched)
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
            # Add up to 2 distinct rewrites
            for r in matched_rewrites[:2]:
                if r not in queries:
                    queries.append(r)
        else:
            # Generic legal syntax rewrite
            queries.append(f"{resolved_q} Indian statutory law procedure rights")

        return queries
