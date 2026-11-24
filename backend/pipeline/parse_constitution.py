"""
Production Ingestion Pipeline: Parse official Constitution of India PDF.
Extracts Preamble, Part III (Fundamental Rights), Part IV (DPSP),
and Part IVA (Fundamental Duties).
"""

import json
import re
from pathlib import Path
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PDF = BASE_DIR / "data" / "raw" / "constitution_of_india.pdf"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

TARGET_PART3_ARTICLES = [
    "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "21A", "22", "23", "24", "25", "26", "27", "28",
    "29", "30", "31", "31A", "31B", "31C", "31D", "32", "32A",
    "33", "34", "35"
]

SUBHEADINGS_PART3 = {
    "12": "General",
    "13": "General",
    "14": "Right to Equality",
    "15": "Right to Equality",
    "16": "Right to Equality",
    "17": "Right to Equality",
    "18": "Right to Equality",
    "19": "Right to Freedom",
    "20": "Right to Freedom",
    "21": "Right to Freedom",
    "21A": "Right to Freedom",
    "22": "Right to Freedom",
    "23": "Right against Exploitation",
    "24": "Right against Exploitation",
    "25": "Right to Freedom of Religion",
    "26": "Right to Freedom of Religion",
    "27": "Right to Freedom of Religion",
    "28": "Right to Freedom of Religion",
    "29": "Cultural and Educational Rights",
    "30": "Cultural and Educational Rights",
    "31": "Right to Property (Repealed)",
    "31A": "Saving of Certain Laws",
    "31B": "Saving of Certain Laws",
    "31C": "Saving of Certain Laws",
    "31D": "Saving of Certain Laws (Repealed)",
    "32": "Right to Constitutional Remedies",
    "32A": "Right to Constitutional Remedies (Repealed)",
    "33": "Right to Constitutional Remedies",
    "34": "Right to Constitutional Remedies",
    "35": "Right to Constitutional Remedies",
}

TARGET_PART4_ARTICLES = [
    "36", "37", "38", "39", "39A", "40", "41", "42", "43", "43A",
    "43B", "44", "45", "46", "47", "48", "48A", "49", "50", "51"
]


def normalize_legal_text(raw_text: str) -> str:
    """
    Normalizes legal text extracted from PDF:
    - Removes line-wrap breaks inside sentences.
    - Preserves structural clauses on separate lines: (1), (2), (a), (b), etc.
    """
    text = re.sub(r"[ \t]*\n[ \t]*", " ", raw_text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = re.sub(r"\s*(\((?:\d+[A-Z]?|[a-z]+)\))\s*", r"\n\1 ", text)
    text = re.sub(r"\s*(Provided (?:further )?that)\s*", r"\n\1 ", text)
    return text.strip()


def parse_preamble(reader):
    """Extract and structure the Preamble (Page 32)."""
    text = reader.pages[31].extract_text() or ""
    idx = text.find("WE, THE PEOPLE OF INDIA")
    end_idx = text.find("THIS CONSTITUTION.")
    if idx != -1 and end_idx != -1:
        preamble_body = text[idx : end_idx + len("THIS CONSTITUTION.")].strip()
    else:
        preamble_body = text.strip()

    clean_preamble = re.sub(r"[ \t]*\n[ \t]*", " ", preamble_body)
    clean_preamble = re.sub(r"[ \t]+", " ", clean_preamble).strip()

    return {
        "chunk_id": "constitution-preamble",
        "source_id": "constitution-india",
        "law": "Constitution of India",
        "part": "Preamble",
        "part_title": "Preamble",
        "article": "Preamble",
        "title": "Preamble of the Constitution of India",
        "text": clean_preamble,
        "location": "Preamble, Page 32",
    }


def clean_page(text: str, excluded_headers: list) -> str:
    """Strip running headers, page numbers, and footnotes."""
    lines = text.splitlines()
    body_lines = []
    in_footnotes = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d{1,3}$", stripped):
            continue
        if "THE CONSTITUTION OF INDIA" in stripped:
            continue
        if any(h in stripped for h in excluded_headers):
            continue
        if re.match(r"^\(?Part\s+[A-Z]+[.—\-].*\)?$", stripped, re.IGNORECASE):
            continue
        if re.match(r"^\d+\.\s+(?:Subs\.|Ins\.|Added|Omitted|The words|Sub-clause|Certain words)", stripped):
            in_footnotes = True
        if not in_footnotes:
            body_lines.append(line)

    return "\n".join(body_lines)


def parse_part3(reader):
    """Parse Part III (Fundamental Rights, Articles 12-35) from pages 37 to 51."""
    full_body = []
    for p in range(36, 51):
        raw_txt = reader.pages[p].extract_text() or ""
        b = clean_page(raw_txt, ["PART III", "FUNDAMENTAL RIGHTS"])
        full_body.append(b)

    corpus = "\n".join(full_body)

    def replacer(m):
        art = m.group(1)
        return f"\n@@@ARTICLE_{art}@@@ {art}. "

    norm_corpus = re.sub(
        r"(?m)^(?:(?:\d+\[?)|\[)?\s*(12|13|14|15|16|17|18|19|20|21A|21|22|23|24|25|26|27|28|29|30|31A|31B|31C|31D|31|32A|32|33|34|35)\.\s+",
        replacer,
        corpus,
    )

    chunks = norm_corpus.split("@@@ARTICLE_")
    found_articles = {}

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        header_line = chunk.split("\n", 1)[0]
        art_id = header_line.split("@@@")[0].strip()
        rest = chunk.split("@@@", 1)[-1].strip()
        if art_id in TARGET_PART3_ARTICLES:
            found_articles[art_id] = rest

    articles = []
    for art_num in TARGET_PART3_ARTICLES:
        if art_num not in found_articles:
            raise ValueError(f"Missing required Article {art_num} in Part III parsing")

        full_raw_text = found_articles[art_num]
        normalized_text = normalize_legal_text(full_raw_text)

        first_line = normalized_text.splitlines()[0]
        title_match = re.search(r"^\d+[A-Z]?\.\s+([^—\n]+)—", first_line)
        if title_match:
            raw_title = title_match.group(1).replace("—", "").strip()
            raw_title = " ".join(raw_title.split())
        else:
            raw_title = f"Article {art_num}"

        subheading = SUBHEADINGS_PART3.get(art_num, "Fundamental Rights")

        articles.append({
            "chunk_id": f"constitution-art-{art_num.lower()}",
            "source_id": "constitution-india",
            "law": "Constitution of India",
            "part": "Part III",
            "part_title": "Fundamental Rights",
            "subheading": subheading,
            "article": f"Article {art_num}",
            "title": f"Article {art_num}: {raw_title}",
            "text": normalized_text,
            "location": f"Part III, Article {art_num}",
        })

    return articles


def parse_part4(reader):
    """Parse Part IV (Directive Principles of State Policy, Articles 36-51) from pages 52 to 55."""
    full_body = []
    for p in range(51, 55):
        raw_txt = reader.pages[p].extract_text() or ""
        b = clean_page(raw_txt, ["PART IV", "DIRECTIVE PRINCIPLES OF STATE POLICY"])
        full_body.append(b)

    corpus = "\n".join(full_body)

    def replacer(m):
        art = m.group(1)
        return f"\n@@@ARTICLE_{art}@@@ {art}. "

    norm_corpus = re.sub(
        r"(?m)^(?:(?:\d+\[?)|\[)?\s*(36|37|38|39A|39|40|41|42|43A|43B|43|44|45|46|47|48A|48|49|50|51)\.\s+",
        replacer,
        corpus,
    )

    chunks = norm_corpus.split("@@@ARTICLE_")
    found_articles = {}

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        header_line = chunk.split("\n", 1)[0]
        art_id = header_line.split("@@@")[0].strip()
        rest = chunk.split("@@@", 1)[-1].strip()
        if art_id in TARGET_PART4_ARTICLES:
            found_articles[art_id] = rest

    articles = []
    for art_num in TARGET_PART4_ARTICLES:
        if art_num not in found_articles:
            raise ValueError(f"Missing required Article {art_num} in Part IV parsing")

        full_raw_text = found_articles[art_num]
        normalized_text = normalize_legal_text(full_raw_text)

        first_line = normalized_text.splitlines()[0]
        title_match = re.search(r"^\d+[A-Z]?\.\s+([^—\n]+)—", first_line)
        if title_match:
            raw_title = title_match.group(1).replace("—", "").strip()
            raw_title = " ".join(raw_title.split())
        else:
            raw_title = f"Article {art_num}"

        articles.append({
            "chunk_id": f"constitution-art-{art_num.lower()}",
            "source_id": "constitution-india",
            "law": "Constitution of India",
            "part": "Part IV",
            "part_title": "Directive Principles of State Policy",
            "subheading": "Directive Principles of State Policy",
            "article": f"Article {art_num}",
            "title": f"Article {art_num}: {raw_title}",
            "text": normalized_text,
            "location": f"Part IV, Article {art_num}",
        })

    return articles


def parse_part4a(reader):
    """Parse Part IVA (Fundamental Duties, Article 51A) from page 56."""
    raw_txt = reader.pages[55].extract_text() or ""
    b = clean_page(raw_txt, ["PART IVA", "FUNDAMENTAL DUTIES"])
    normalized_text = normalize_legal_text(b)

    return [{
        "chunk_id": "constitution-art-51a",
        "source_id": "constitution-india",
        "law": "Constitution of India",
        "part": "Part IVA",
        "part_title": "Fundamental Duties",
        "subheading": "Fundamental Duties",
        "article": "Article 51A",
        "title": "Article 51A: Fundamental duties",
        "text": normalized_text,
        "location": "Part IVA, Article 51A",
    }]


def run_ingestion():
    if not RAW_PDF.exists():
        raise FileNotFoundError(f"Raw Constitution PDF not found at {RAW_PDF}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(RAW_PDF)

    preamble = parse_preamble(reader)
    part3_articles = parse_part3(reader)
    part4_articles = parse_part4(reader)
    part4a_articles = parse_part4a(reader)

    # Save individual components
    part3_path = PROCESSED_DIR / "constitution_part3.json"
    part3_path.write_text(json.dumps(part3_articles, indent=2, ensure_ascii=False), encoding="utf-8")

    part4_path = PROCESSED_DIR / "constitution_part4.json"
    part4_path.write_text(json.dumps(part4_articles, indent=2, ensure_ascii=False), encoding="utf-8")

    part4a_path = PROCESSED_DIR / "constitution_part4a.json"
    part4a_path.write_text(json.dumps(part4a_articles, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save complete merged Constitution set
    all_chunks = [preamble] + part3_articles + part4_articles + part4a_articles
    all_path = PROCESSED_DIR / "constitution_chunks.json"
    all_path.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Processed: Preamble (1), Part III ({len(part3_articles)}), Part IV ({len(part4_articles)}), Part IVA ({len(part4a_articles)})")
    print(f"Total Constitution Chunks: {len(all_chunks)} -> {all_path}")
    return all_chunks


if __name__ == "__main__":
    run_ingestion()
