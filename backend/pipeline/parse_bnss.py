"""
Production Ingestion Pipeline: Parse official BNSS 2023 PDF.
Extracts comprehensive sections on:
- Full Arrest Procedure (Chapter V: Sections 35 to 62)
- Summons and Warrants (Chapter VI: Sections 63, 64, 70, 72, 73, 84)
- Search and Seizure (Chapter VII: Sections 94, 96, 103, 105, 106, 107)
- Police Custody Limits and Remand (Chapter XIV: Section 187)
- Bail, Anticipatory Bail and Bonds (Chapter XXXV: Sections 478, 479, 480, 482, 483)
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
    # --- CHAPTER V: ARREST OF PERSONS ---
    {
        "section": "35",
        "title": "When police may arrest without warrant",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 41 CrPC",
    },
    {
        "section": "36",
        "title": "Procedure of arrest and duties of officer making arrest",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 41B CrPC",
    },
    {
        "section": "37",
        "title": "Designated police officer",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 41C CrPC",
    },
    {
        "section": "38",
        "title": "Right of arrested person to meet an advocate of his choice during interrogation",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 41D CrPC",
    },
    {
        "section": "39",
        "title": "Arrest on refusal to give name and residence",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 42 CrPC",
    },
    {
        "section": "40",
        "title": "Arrest by private person and procedure on such arrest",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 43 CrPC",
    },
    {
        "section": "41",
        "title": "Arrest by Magistrate",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 44 CrPC",
    },
    {
        "section": "42",
        "title": "Protection of members of Armed Forces from arrest",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 45 CrPC",
    },
    {
        "section": "43",
        "title": "Arrest how made and arrest of women",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 46 CrPC",
    },
    {
        "section": "44",
        "title": "Search of place entered by person sought to be arrested",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 47 CrPC",
    },
    {
        "section": "45",
        "title": "Pursuit of offenders into other jurisdictions",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 48 CrPC",
    },
    {
        "section": "46",
        "title": "No unnecessary restraint",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 49 CrPC",
    },
    {
        "section": "47",
        "title": "Person arrested to be informed of grounds of arrest and of right to bail",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 50 CrPC",
    },
    {
        "section": "48",
        "title": "Obligation of person making arrest to inform about arrest, etc., to nominated person",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 50A CrPC",
    },
    {
        "section": "49",
        "title": "Search of arrested person",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 51 CrPC",
    },
    {
        "section": "50",
        "title": "Power to seize offensive weapons",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 52 CrPC",
    },
    {
        "section": "51",
        "title": "Examination of accused by medical practitioner at request of police officer",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 53 CrPC",
    },
    {
        "section": "52",
        "title": "Examination of person accused of rape by medical practitioner",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 53A CrPC",
    },
    {
        "section": "53",
        "title": "Examination of arrested person by medical officer",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 54 CrPC",
    },
    {
        "section": "54",
        "title": "Identification of person arrested",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 54A CrPC",
    },
    {
        "section": "55",
        "title": "When police officer may depute subordinate to arrest without warrant",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 55 CrPC",
    },
    {
        "section": "56",
        "title": "Health and safety of accused",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 55A CrPC",
    },
    {
        "section": "57",
        "title": "Person arrested to be taken before Magistrate or officer in charge of police station without delay",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 56 CrPC",
    },
    {
        "section": "58",
        "title": "Person arrested not to be detained more than twenty-four hours",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 57 CrPC",
    },
    {
        "section": "59",
        "title": "Police to report apprehensions",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 58 CrPC",
    },
    {
        "section": "60",
        "title": "Discharge of person apprehended",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 59 CrPC",
    },
    {
        "section": "61",
        "title": "Power, on escape, to pursue and retake",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 60 CrPC",
    },
    {
        "section": "62",
        "title": "Arrest to be made strictly according to Sanhita",
        "chapter": "Chapter V",
        "chapter_title": "Arrest of Persons",
        "old_equivalent": "Section 60A CrPC",
    },

    # --- CHAPTER VI: PROCESSES TO COMPEL APPEARANCE (SUMMONS AND WARRANTS) ---
    {
        "section": "63",
        "title": "Form of summons",
        "chapter": "Chapter VI",
        "chapter_title": "Processes to Compel Appearance",
        "old_equivalent": "Section 61 CrPC",
    },
    {
        "section": "64",
        "title": "Summons how served",
        "chapter": "Chapter VI",
        "chapter_title": "Processes to Compel Appearance",
        "old_equivalent": "Section 62 CrPC",
    },
    {
        "section": "70",
        "title": "Proof of service in such cases and when serving officer not present",
        "chapter": "Chapter VI",
        "chapter_title": "Processes to Compel Appearance",
        "old_equivalent": "Section 68 CrPC",
    },
    {
        "section": "72",
        "title": "Form of warrant of arrest and duration",
        "chapter": "Chapter VI",
        "chapter_title": "Processes to Compel Appearance",
        "old_equivalent": "Section 70 CrPC",
    },
    {
        "section": "73",
        "title": "Power to direct security to be taken (Bailable warrant)",
        "chapter": "Chapter VI",
        "chapter_title": "Processes to Compel Appearance",
        "old_equivalent": "Section 71 CrPC",
    },
    {
        "section": "84",
        "title": "Proclamation for person absconding",
        "chapter": "Chapter VI",
        "chapter_title": "Processes to Compel Appearance",
        "old_equivalent": "Section 82 CrPC",
    },

    # --- CHAPTER VII: PROCESSES TO COMPEL PRODUCTION OF THINGS (SEARCH AND SEIZURE) ---
    {
        "section": "94",
        "title": "Summons to produce document or other thing",
        "chapter": "Chapter VII",
        "chapter_title": "Processes to Compel the Production of Things",
        "old_equivalent": "Section 91 CrPC",
    },
    {
        "section": "96",
        "title": "When search-warrant may be issued",
        "chapter": "Chapter VII",
        "chapter_title": "Processes to Compel the Production of Things",
        "old_equivalent": "Section 93 CrPC",
    },
    {
        "section": "103",
        "title": "Search of closed place",
        "chapter": "Chapter VII",
        "chapter_title": "Processes to Compel the Production of Things",
        "old_equivalent": "Section 100 CrPC",
    },
    {
        "section": "105",
        "title": "Recording of search and seizure through audio-video electronic means",
        "chapter": "Chapter VII",
        "chapter_title": "Processes to Compel the Production of Things",
        "old_equivalent": "New Provision in BNSS 2023",
    },
    {
        "section": "106",
        "title": "Summary disposal of certain seized property",
        "chapter": "Chapter VII",
        "chapter_title": "Processes to Compel the Production of Things",
        "old_equivalent": "New Provision in BNSS 2023",
    },
    {
        "section": "107",
        "title": "Attachment, forfeiture or restoration of property",
        "chapter": "Chapter VII",
        "chapter_title": "Processes to Compel the Production of Things",
        "old_equivalent": "Section 105D CrPC",
    },

    # --- CHAPTER XIV: INFORMATION TO POLICE AND POWERS TO INVESTIGATE (CUSTODY LIMITS) ---
    {
        "section": "187",
        "title": "Procedure when investigation cannot be completed in twenty-four hours (Police & Judicial Custody Limits)",
        "chapter": "Chapter XIV",
        "chapter_title": "Information to the Police and Their Powers to Investigate",
        "old_equivalent": "Section 167 CrPC",
    },

    # --- CHAPTER XXXV: PROVISIONS AS TO BAIL AND BONDS ---
    {
        "section": "478",
        "title": "In what cases bail to be taken",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "old_equivalent": "Section 436 CrPC",
    },
    {
        "section": "479",
        "title": "Maximum period for which undertrial prisoner can be detained",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "old_equivalent": "Section 436A CrPC",
    },
    {
        "section": "480",
        "title": "When bail may be taken in case of non-bailable offence",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "old_equivalent": "Section 437 CrPC",
    },
    {
        "section": "482",
        "title": "Direction for grant of bail to person apprehending arrest (Anticipatory bail)",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "old_equivalent": "Section 438 CrPC",
    },
    {
        "section": "483",
        "title": "Special powers of High Court or Court of Session regarding bail",
        "chapter": "Chapter XXXV",
        "chapter_title": "Provisions as to Bail and Bonds",
        "old_equivalent": "Section 439 CrPC",
    },
]


def clean_bnss_page(text: str) -> str:
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
    text = re.sub(r"\s*(Explanation\s*[\d\.]*—)\s*", r"\n\1 ", text)
    return text.strip()


def parse_bnss():
    if not RAW_BNSS_PDF.exists():
        raise FileNotFoundError(f"Raw BNSS PDF not found at {RAW_BNSS_PDF}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(RAW_BNSS_PDF)

    chunks = []
    for target in BNSS_TARGETS:
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
            print(f"Warning: Could not find start page for Section {sec}")
            continue

        pages_text = []
        for p in range(found_start_page, min(found_start_page + 6, len(reader.pages))):
            raw = reader.pages[p].extract_text() or ""
            pages_text.append(clean_bnss_page(raw))
        combined = "\n".join(pages_text)

        m_start = start_pat.search(combined)
        if not m_start:
            print(f"Warning: Start pattern not matched in combined text for Section {sec}")
            continue

        sub = combined[m_start.start():]
        m_end = end_pat.search(sub)
        body = sub[:m_end.start()].strip() if m_end else sub.strip()

        clean_norm = normalize_legal_text(body)
        location_page = found_start_page + 1

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
            "location": f"BNSS 2023, Section {sec}, Page {location_page}",
        })

    out_path = PROCESSED_DIR / "bnss_chunks.json"
    out_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully processed {len(chunks)} BNSS sections -> {out_path}")
    return chunks


if __name__ == "__main__":
    parse_bnss()
