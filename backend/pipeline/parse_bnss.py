"""
Production Ingestion Pipeline: Parse official BNSS 2023 PDF.
Extracts sections on:
- arrest without warrant (Section 35)
- rights of an arrested person (Section 47, Section 48)
- production before a magistrate / detention limits (Section 57, Section 58)
- bail (Section 478, Section 479, Section 480, Section 482)
from official Gazette Act No. 46 of 2023.
"""

import json
import re
from pathlib import Path
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_BNSS_PDF = BASE_DIR / "data" / "raw" / "bnss_2023.pdf"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

BNSS_TARGETS = [
    {
        "section": "35",
        "title": "When police may arrest without warrant",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "start_page": 12,
        "end_page": 14,
        "start_pat": r"(?m)^\s*35\.\s+",
        "end_pat": r"(?m)^\s*36\.\s+",
        "page_num": 13,
        "old_equivalent": "Section 41 CrPC",
    },
    {
        "section": "47",
        "title": "Person arrested to be informed of grounds of arrest and of right to bail",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "start_page": 16,
        "end_page": 16,
        "start_pat": r"(?m)^\s*47\.\s+",
        "end_pat": r"(?m)^\s*48\.\s+",
        "page_num": 17,
        "old_equivalent": "Section 50 CrPC",
    },
    {
        "section": "48",
        "title": "Obligation of person making arrest to inform about arrest, etc., to nominated person",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "start_page": 16,
        "end_page": 17,
        "start_pat": r"(?m)^\s*48\.\s+",
        "end_pat": r"(?m)^\s*49\.\s+",
        "page_num": 17,
        "old_equivalent": "Section 50A CrPC",
    },
    {
        "section": "57",
        "title": "Person arrested to be taken before Magistrate or officer in charge of police station",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "start_page": 18,
        "end_page": 18,
        "start_pat": r"(?m)^\s*57\.\s+",
        "end_pat": r"(?m)^\s*58\.\s+",
        "page_num": 19,
        "old_equivalent": "Section 56 CrPC",
    },
    {
        "section": "58",
        "title": "Person arrested not to be detained more than twenty-four hours",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "start_page": 18,
        "end_page": 18,
        "start_pat": r"(?m)^\s*58\.\s+",
        "end_pat": r"(?m)^\s*59\.\s+",
        "page_num": 19,
        "old_equivalent": "Section 57 CrPC",
    },
    {
        "section": "478",
        "title": "In what cases bail to be taken",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "start_page": 142,
        "end_page": 143,
        "start_pat": r"(?m)^\s*478\.\s+",
        "end_pat": r"(?m)^\s*479\.\s+",
        "page_num": 143,
        "old_equivalent": "Section 436 CrPC",
    },
    {
        "section": "479",
        "title": "Maximum period for which undertrial prisoner can be detained",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "start_page": 143,
        "end_page": 143,
        "start_pat": r"(?m)^\s*479\.\s+",
        "end_pat": r"(?m)^\s*480\.\s+",
        "page_num": 144,
        "old_equivalent": "Section 436A CrPC",
    },
    {
        "section": "480",
        "title": "When bail may be taken in case of non-bailable offence",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "start_page": 143,
        "end_page": 145,
        "start_pat": r"(?m)^\s*480\.\s+",
        "end_pat": r"(?m)^\s*481\.\s+",
        "page_num": 144,
        "old_equivalent": "Section 437 CrPC",
    },
    {
        "section": "482",
        "title": "Direction for grant of bail to person apprehending arrest",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "start_page": 145,
        "end_page": 146,
        "start_pat": r"(?m)^\s*482\.\s+",
        "end_pat": r"(?m)^\s*483\.\s+",
        "page_num": 146,
        "old_equivalent": "Section 438 CrPC",
    },
]


def clean_bnss_page(text: str) -> str:
    """Strip running page numbers, gazette headers, and side marginal keywords."""
    lines = text.splitlines()
    body_lines = []
    for line in lines:
        s = line.strip()
        if not s or re.match(r"^\d{1,3}$", s):
            continue
        if "EXTRAORDINARY" in s or "PART II" in s or "BHARATIYA NAGARIK" in s:
            continue
        body_lines.append(line)
    return "\n".join(body_lines)


def normalize_legal_text(raw_text: str) -> str:
    text = re.sub(r"[ \t]*\n[ \t]*", " ", raw_text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = re.sub(r"\s*(\((?:\d+[A-Z]?|[a-z]+)\))\s*", r"\n\1 ", text)
    text = re.sub(r"\s*(Provided (?:further )?that)\s*", r"\n\1 ", text)
    return text.strip()


def parse_bnss():
    if not RAW_BNSS_PDF.exists():
        raise FileNotFoundError(f"Raw BNSS PDF not found at {RAW_BNSS_PDF}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(RAW_BNSS_PDF)

    chunks = []
    for target in BNSS_TARGETS:
        sec = target["section"]
        start_p = target["start_page"]
        end_p = target["end_page"]

        pages_text = []
        for p in range(start_p, end_p + 1):
            raw = reader.pages[p].extract_text() or ""
            pages_text.append(clean_bnss_page(raw))
        combined = "\n".join(pages_text)

        m_start = re.search(target["start_pat"], combined)
        if not m_start:
            raise ValueError(f"Could not find start of BNSS Section {sec}")

        sub = combined[m_start.start():]
        m_end = re.search(target["end_pat"], sub)
        body = sub[:m_end.start()].strip() if m_end else sub.strip()

        # Remove section number prefix and marginal keyword noise from start of text
        clean_norm = normalize_legal_text(body)

        chunks.append({
            "chunk_id": f"bnss-sec-{sec}",
            "source_id": "bnss-2023",
            "law": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "part": target["chapter"],
            "part_title": target["chapter_title"],
            "subheading": target["chapter_title"],
            "section": f"Section {sec}",
            "title": f"Section {sec}: {target['title']}",
            "text": clean_norm,
            "old_equivalent": target["old_equivalent"],
            "location": f"BNSS 2023, Section {sec}, Page {target['page_num']}",
        })

    out_path = PROCESSED_DIR / "bnss_chunks.json"
    out_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully processed {len(chunks)} BNSS sections -> {out_path}")
    return chunks


if __name__ == "__main__":
    parse_bnss()
