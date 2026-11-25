"""
Parser for the Right to Information Act, 2005 (Act No. 22 of 2005).
Extracts selected key sections directly from official CIC PDF (data/raw/rti_2005.pdf)
preserving sub-clauses and provisos.
"""

import json
import re
from pathlib import Path
import pypdf

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PDF = BASE_DIR / "data" / "raw" / "rti_2005.pdf"
OUT_JSON = BASE_DIR / "data" / "processed" / "rti_chunks.json"
SOURCE_URL = "https://cic.gov.in/sites/default/files/RTI-Act_English.pdf"

RTI_TARGETS = [
    {"section": "2", "title": "Definitions (Information, Public Authority, Right to Information)", "chapter": "Chapter I", "chapter_title": "Preliminary"},
    {"section": "3", "title": "Right to information", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "4", "title": "Obligations of public authorities", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "5", "title": "Designation of Public Information Officers", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "6", "title": "Request for obtaining information", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "7", "title": "Disposal of request", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "8", "title": "Exemption from disclosure of information", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "9", "title": "Grounds for rejection to access in certain cases", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "10", "title": "Severability", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "11", "title": "Third party information", "chapter": "Chapter II", "chapter_title": "Right to Information and Obligations of Public Authorities"},
    {"section": "12", "title": "Constitution of Central Information Commission", "chapter": "Chapter III", "chapter_title": "The Central Information Commission"},
    {"section": "18", "title": "Powers and functions of Information Commissions", "chapter": "Chapter V", "chapter_title": "Powers and Functions of Information Commissions, Appeal and Penalties"},
    {"section": "19", "title": "Appeal", "chapter": "Chapter V", "chapter_title": "Powers and Functions of Information Commissions, Appeal and Penalties"},
    {"section": "20", "title": "Penalties", "chapter": "Chapter V", "chapter_title": "Powers and Functions of Information Commissions, Appeal and Penalties"},
    {"section": "22", "title": "Act to have overriding effect", "chapter": "Chapter VI", "chapter_title": "Miscellaneous"},
    {"section": "23", "title": "Bar of jurisdiction of courts", "chapter": "Chapter VI", "chapter_title": "Miscellaneous"},
    {"section": "24", "title": "Act not to apply to certain organisations", "chapter": "Chapter VI", "chapter_title": "Miscellaneous"},
]


def clean_page(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if "Right to Information Act, 2005" in s or re.match(r"^\d+$", s):
            continue
        if s.startswith("(Chapter "):
            continue
        cleaned.append(s)
    return "\n".join(cleaned)


def normalize_text(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_rti():
    if not RAW_PDF.exists():
        raise FileNotFoundError(f"Missing {RAW_PDF}")

    reader = pypdf.PdfReader(str(RAW_PDF))
    # Body starts at page index 5 (Page 6) after TOC
    body_pages = [(i + 1, clean_page(reader.pages[i].extract_text() or "")) for i in range(5, len(reader.pages))]
    full_text = "\n".join([t for _, t in body_pages])

    chunks = []
    for target in RTI_TARGETS:
        sec = target["section"]
        next_sec = str(int(sec) + 1)

        start_pat = re.compile(r"(?m)^\s*" + re.escape(sec) + r"\.\s+")
        end_pat = re.compile(r"(?m)^\s*" + re.escape(next_sec) + r"\.\s+")

        m_start = start_pat.search(full_text)
        if not m_start:
            # Try inline match if OCR merged previous line
            start_pat = re.compile(r"(?:\n|^|\s)" + re.escape(sec) + r"\.\s*\(?(?:1|[A-Z])")
            m_start = start_pat.search(full_text)
            if not m_start:
                print(f"Warning: Could not find RTI Section {sec}")
                continue

        sub = full_text[m_start.start():]
        m_end = end_pat.search(sub[10:])
        body = sub[:10 + m_end.start()].strip() if m_end else sub[:3500].strip()

        clean_norm = normalize_text(body)
        if len(clean_norm) > 3500:
            clean_norm = clean_norm[:3500]

        chunks.append({
            "chunk_id": f"rti-sec-{sec}",
            "source_id": "rti-2005",
            "law": "Right to Information Act, 2005",
            "part": target["chapter"],
            "part_title": target["chapter_title"],
            "subheading": target["chapter_title"],
            "section": f"Section {sec}",
            "title": f"Section {sec}: {target['title']}",
            "text": clean_norm,
            "location": f"RTI Act 2005, Section {sec}",
            "source_url": SOURCE_URL,
        })

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Successfully processed {len(chunks)} RTI Act 2005 sections -> {OUT_JSON}")
    return chunks


if __name__ == "__main__":
    parse_rti()
