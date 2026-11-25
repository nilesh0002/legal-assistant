"""
Parser for the Consumer Protection Act, 2019 (Act No. 35 of 2019).
Extracts selected key sections directly from official Gazette PDF (data/raw/cpa_2019.pdf)
preserving sub-clauses, provisos, and explanations.
"""

import json
import re
from pathlib import Path
import pypdf

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PDF = BASE_DIR / "data" / "raw" / "cpa_2019.pdf"
OUT_JSON = BASE_DIR / "data" / "processed" / "cpa_chunks.json"
SOURCE_URL = "https://egazette.gov.in/WriteReadData/2019/210422.pdf"

CPA_TARGETS = [
    {"section": "2", "title": "Definitions (Consumer, Defect, Deficiency, Unfair Trade Practice)", "chapter": "Chapter I", "chapter_title": "Preliminary"},
    {"section": "10", "title": "Establishment of Central Consumer Protection Authority", "chapter": "Chapter III", "chapter_title": "Central Consumer Protection Authority"},
    {"section": "18", "title": "Powers and functions of Central Authority", "chapter": "Chapter III", "chapter_title": "Central Consumer Protection Authority"},
    {"section": "20", "title": "Power of Central Authority to recall goods, etc.", "chapter": "Chapter III", "chapter_title": "Central Consumer Protection Authority"},
    {"section": "21", "title": "Power of Central Authority to issue directions and penalties against false or misleading advertisements", "chapter": "Chapter III", "chapter_title": "Central Consumer Protection Authority"},
    {"section": "28", "title": "Establishment of District Consumer Disputes Redressal Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "34", "title": "Jurisdiction of District Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "35", "title": "Manner in which complaint shall be made", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "38", "title": "Procedure on admission of complaint", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "39", "title": "Findings of District Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "41", "title": "Appeal against order of District Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "47", "title": "Jurisdiction of State Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "51", "title": "Appeal to National Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "58", "title": "Jurisdiction of National Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "67", "title": "Appeal against order of National Commission", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "69", "title": "Limitation period for filing complaint", "chapter": "Chapter IV", "chapter_title": "Consumer Disputes Redressal Commission"},
    {"section": "74", "title": "Establishment of consumer mediation cell", "chapter": "Chapter V", "chapter_title": "Mediation"},
    {"section": "82", "title": "Application of Chapter on Product Liability", "chapter": "Chapter VI", "chapter_title": "Product Liability"},
    {"section": "83", "title": "Product liability action", "chapter": "Chapter VI", "chapter_title": "Product Liability"},
    {"section": "84", "title": "Liability of product manufacturer", "chapter": "Chapter VI", "chapter_title": "Product Liability"},
    {"section": "85", "title": "Liability of product service provider", "chapter": "Chapter VI", "chapter_title": "Product Liability"},
    {"section": "86", "title": "Liability of product sellers", "chapter": "Chapter VI", "chapter_title": "Product Liability"},
    {"section": "87", "title": "Exceptions to product liability action", "chapter": "Chapter VI", "chapter_title": "Product Liability"},
    {"section": "88", "title": "Penalty for non-compliance of direction of Central Authority", "chapter": "Chapter VII", "chapter_title": "Offences and Penalties"},
    {"section": "89", "title": "Punishment for false or misleading advertisement", "chapter": "Chapter VII", "chapter_title": "Offences and Penalties"},
    {"section": "90", "title": "Punishment for manufacturing for sale or storing, selling or distributing or importing products containing adulterant", "chapter": "Chapter VII", "chapter_title": "Offences and Penalties"},
    {"section": "91", "title": "Punishment for manufacturing for sale or storing or selling or distributing or importing spurious goods", "chapter": "Chapter VII", "chapter_title": "Offences and Penalties"},
]


def clean_page(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if "THE GAZETTE OF INDIA EXTRAORDINARY" in s or re.match(r"^SEC\.\s*\d+\]$", s):
            continue
        if re.match(r"^\d+$", s):
            continue
        cleaned.append(s)
    return "\n".join(cleaned)


def normalize_text(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_cpa():
    if not RAW_PDF.exists():
        raise FileNotFoundError(f"Missing {RAW_PDF}")

    reader = pypdf.PdfReader(str(RAW_PDF))
    chunks = []

    for target in CPA_TARGETS:
        sec = target["section"]
        next_sec = str(int(sec) + 1)
        start_pat = re.compile(r"(?m)^\s*" + re.escape(sec) + r"\.\s+")
        end_pat = re.compile(r"(?m)^\s*" + re.escape(next_sec) + r"\.\s+")

        found_start_page = None
        for p in range(len(reader.pages)):
            t = reader.pages[p].extract_text() or ""
            if start_pat.search(t):
                found_start_page = p
                break

        if found_start_page is None:
            print(f"Warning: Could not find CPA Section {sec}")
            continue

        pages_text = []
        max_span = 7 if sec == "2" else 4
        for p in range(found_start_page, min(found_start_page + max_span, len(reader.pages))):
            raw = reader.pages[p].extract_text() or ""
            pages_text.append(clean_page(raw))
        combined = "\n".join(pages_text)

        m_start = start_pat.search(combined)
        if not m_start:
            continue
        sub = combined[m_start.start():]
        m_end = end_pat.search(sub)
        body = sub[:m_end.start()].strip() if m_end else sub.strip()

        clean_norm = normalize_text(body)
        # Keep definitions section concise if huge (max ~3500 chars keeping consumer, defect, deficiency)
        if sec == "2" and len(clean_norm) > 3500:
            clean_norm = clean_norm[:3500]

        chunks.append({
            "chunk_id": f"cpa-sec-{sec}",
            "source_id": "cpa-2019",
            "law": "Consumer Protection Act, 2019",
            "part": target["chapter"],
            "part_title": target["chapter_title"],
            "subheading": target["chapter_title"],
            "section": f"Section {sec}",
            "title": f"Section {sec}: {target['title']}",
            "text": clean_norm,
            "location": f"CPA 2019, Section {sec}, Page {found_start_page + 1}",
            "source_url": SOURCE_URL,
        })

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Successfully processed {len(chunks)} CPA 2019 sections -> {OUT_JSON}")
    return chunks


if __name__ == "__main__":
    parse_cpa()
