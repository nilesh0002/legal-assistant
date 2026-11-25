"""
Production Ingestion Pipeline: Parse official BNS 2023 PDF.
Extracts comprehensive sections on:
- Chapter III: General Exceptions (Sec 14, 20, 22, 34, 37)
- Chapter V: Offences Against Women & Children (Sec 63, 64, 69, 74, 75, 76, 77, 78, 84, 85)
- Chapter VI: Offences Affecting the Human Body (Sec 100, 101, 103, 105, 106, 114, 115, 117, 126, 127, 137, 140)
- Chapter VII: Offences Against the State (Sec 152)
- Chapter XI: Offences Against the Public Tranquillity (Sec 189, 191, 194, 196)
- Chapter XVII: Offences Against Property (Sec 303, 307, 308, 310, 314, 316, 318, 324, 329, 331)
- Chapter XIX: Criminal Intimidation, Insult, Defamation (Sec 351, 356)
from official Gazette Act No. 45 of 2023.
"""

import json
import re
from pathlib import Path
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_BNS_PDF = BASE_DIR / "data" / "raw" / "bns_2023.pdf"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MAPPINGS_DIR = BASE_DIR / "data" / "mappings"

BNS_TARGETS = [
    # --- CHAPTER III: GENERAL EXCEPTIONS ---
    {
        "section": "14",
        "title": "Act done by a person bound, or by mistake of fact believing himself bound, by law",
        "chapter": "Chapter III",
        "chapter_title": "General Exceptions",
        "old_equivalent": "Section 76 IPC (needs human review)",
    },
    {
        "section": "20",
        "title": "Act of a child under seven years of age",
        "chapter": "Chapter III",
        "chapter_title": "General Exceptions",
        "old_equivalent": "Section 82 IPC (needs human review)",
    },
    {
        "section": "22",
        "title": "Act of a person of unsound mind",
        "chapter": "Chapter III",
        "chapter_title": "General Exceptions",
        "old_equivalent": "Section 84 IPC (needs human review)",
    },
    {
        "section": "34",
        "title": "Things done in private defence",
        "chapter": "Chapter III",
        "chapter_title": "Right of Private Defence",
        "old_equivalent": "Section 96 IPC (needs human review)",
    },
    {
        "section": "37",
        "title": "When the right of private defence of the body extends to causing death",
        "chapter": "Chapter III",
        "chapter_title": "Right of Private Defence",
        "old_equivalent": "Section 100 IPC (needs human review)",
    },
    # --- CHAPTER V: OFFENCES AGAINST WOMEN & CHILDREN ---
    {
        "section": "63",
        "title": "Rape",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 375 IPC (needs human review)",
    },
    {
        "section": "64",
        "title": "Punishment for rape",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 376 IPC (needs human review)",
    },
    {
        "section": "69",
        "title": "Sexual intercourse by employing deceitful means, etc.",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "New statutory offence (replaces judicial precedents on false promise of marriage)",
    },
    {
        "section": "74",
        "title": "Assault or use of criminal force to woman with intent to outrage her modesty",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 354 IPC (needs human review)",
    },
    {
        "section": "75",
        "title": "Sexual harassment",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 354A IPC (needs human review)",
    },
    {
        "section": "76",
        "title": "Assault or use of criminal force to woman with intent to disrobe",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 354B IPC (needs human review)",
    },
    {
        "section": "77",
        "title": "Voyeurism",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 354C IPC (needs human review)",
    },
    {
        "section": "78",
        "title": "Stalking",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 354D IPC (needs human review)",
    },
    {
        "section": "80",
        "title": "Dowry death",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 304B IPC (needs human review)",
    },
    {
        "section": "85",
        "title": "Husband or relative of husband of a woman subjecting her to cruelty",
        "chapter": "Chapter V",
        "chapter_title": "Offences Against Women and Children",
        "old_equivalent": "Section 498A IPC (needs human review)",
    },
    # --- CHAPTER VI: OFFENCES AFFECTING THE HUMAN BODY ---
    {
        "section": "100",
        "title": "Culpable homicide",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 299 IPC (needs human review)",
    },
    {
        "section": "101",
        "title": "Murder",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 300 IPC (needs human review)",
    },
    {
        "section": "103",
        "title": "Punishment for murder",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 302 IPC (needs human review)",
    },
    {
        "section": "105",
        "title": "Punishment for culpable homicide not amounting to murder",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 304 IPC (needs human review)",
    },
    {
        "section": "106",
        "title": "Causing death by negligence",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 304A IPC (needs human review)",
    },
    {
        "section": "114",
        "title": "Hurt",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 319 IPC (needs human review)",
    },
    {
        "section": "115",
        "title": "Voluntarily causing hurt",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Sections 321 and 323 IPC (needs human review)",
    },
    {
        "section": "116",
        "title": "Grievous hurt",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 320 IPC (needs human review)",
    },
    {
        "section": "117",
        "title": "Voluntarily causing grievous hurt",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 325 IPC (needs human review)",
    },
    {
        "section": "118",
        "title": "Voluntarily causing hurt or grievous hurt by dangerous weapons or means",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Sections 324 and 326 IPC (needs human review)",
    },
    {
        "section": "126",
        "title": "Wrongful restraint",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 339 IPC (needs human review)",
    },
    {
        "section": "127",
        "title": "Wrongful confinement",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 340 IPC (needs human review)",
    },
    {
        "section": "128",
        "title": "Force",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 349 IPC (needs human review)",
    },
    {
        "section": "129",
        "title": "Criminal force",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 350 IPC (needs human review)",
    },
    {
        "section": "130",
        "title": "Assault",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 351 IPC (needs human review)",
    },
    {
        "section": "131",
        "title": "Punishment for assault or criminal force otherwise than on grave provocation",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 352 IPC (needs human review)",
    },
    {
        "section": "137",
        "title": "Kidnapping",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 359 IPC (needs human review)",
    },
    {
        "section": "140",
        "title": "Kidnapping or abducting in order to murder or for ransom",
        "chapter": "Chapter VI",
        "chapter_title": "Offences Affecting the Human Body",
        "old_equivalent": "Section 364 IPC (needs human review)",
    },
    # --- CHAPTER VII: OFFENCES AGAINST THE STATE ---
    {
        "section": "152",
        "title": "Act endangering sovereignty, unity and integrity of India",
        "chapter": "Chapter VII",
        "chapter_title": "Offences Against the State",
        "old_equivalent": "Section 124A IPC (replaces sedition with sovereignty offences - needs human review)",
    },
    # --- CHAPTER XI: OFFENCES AGAINST THE PUBLIC TRANQUILLITY ---
    {
        "section": "189",
        "title": "Unlawful assembly",
        "chapter": "Chapter XI",
        "chapter_title": "Offences Against the Public Tranquillity",
        "old_equivalent": "Section 141 IPC (needs human review)",
    },
    {
        "section": "191",
        "title": "Rioting",
        "chapter": "Chapter XI",
        "chapter_title": "Offences Against the Public Tranquillity",
        "old_equivalent": "Section 146 IPC (needs human review)",
    },
    {
        "section": "194",
        "title": "Affray",
        "chapter": "Chapter XI",
        "chapter_title": "Offences Against the Public Tranquillity",
        "old_equivalent": "Section 159 IPC (needs human review)",
    },
    {
        "section": "196",
        "title": "Promoting enmity between different groups on grounds of religion, race, place of birth, residence, language, etc.",
        "chapter": "Chapter XI",
        "chapter_title": "Offences Against the Public Tranquillity",
        "old_equivalent": "Section 153A IPC (needs human review)",
    },
    # --- CHAPTER XVII: OFFENCES AGAINST PROPERTY ---
    {
        "section": "303",
        "title": "Theft and punishment for theft",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 378 and 379 IPC (needs human review)",
    },
    {
        "section": "307",
        "title": "Extortion",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 383 and 384 IPC (needs human review)",
    },
    {
        "section": "308",
        "title": "Robbery",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Section 390 IPC (needs human review)",
    },
    {
        "section": "310",
        "title": "Dacoity",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Section 391 IPC (needs human review)",
    },
    {
        "section": "314",
        "title": "Dishonest misappropriation of property",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Section 403 IPC (needs human review)",
    },
    {
        "section": "316",
        "title": "Criminal breach of trust",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 405 and 406 IPC (needs human review)",
    },
    {
        "section": "318",
        "title": "Cheating",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 415 and 420 IPC (needs human review)",
    },
    {
        "section": "324",
        "title": "Mischief",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 425 and 426 IPC (needs human review)",
    },
    {
        "section": "329",
        "title": "Criminal trespass and house-trespass",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 441 and 442 IPC (needs human review)",
    },
    {
        "section": "331",
        "title": "Lurking house-trespass and house-breaking",
        "chapter": "Chapter XVII",
        "chapter_title": "Offences Against Property",
        "old_equivalent": "Sections 443 and 445 IPC (needs human review)",
    },
    # --- CHAPTER XIX: CRIMINAL INTIMIDATION, INSULT, DEFAMATION ---
    {
        "section": "351",
        "title": "Criminal intimidation",
        "chapter": "Chapter XIX",
        "chapter_title": "Criminal Intimidation, Insult, Annoyance, Defamation",
        "old_equivalent": "Sections 503 and 506 IPC (needs human review)",
    },
    {
        "section": "356",
        "title": "Defamation and punishment for defamation",
        "chapter": "Chapter XIX",
        "chapter_title": "Criminal Intimidation, Insult, Annoyance, Defamation",
        "old_equivalent": "Sections 499 and 500 IPC (needs human review)",
    },
]


def clean_bns_page(text: str) -> str:
    lines = text.splitlines()
    body_lines = []
    for line in lines:
        s = line.strip()
        if not s or re.match(r"^\d{1,3}$", s):
            continue
        if "EXTRAORDINARY" in s or "PART II" in s or "BHARATIYA NYAYA SANHITA" in s:
            continue
        body_lines.append(line)
    return "\n".join(body_lines)


def normalize_legal_text(raw_text: str) -> str:
    text = re.sub(r"[ \t]*\n[ \t]*", " ", raw_text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = re.sub(r"\s*(\((?:\d+[A-Z]?|[a-z]+)\))\s*", r"\n\1 ", text)
    text = re.sub(r"\s*(Provided (?:further )?that)\s*", r"\n\1 ", text)
    text = re.sub(r"\s*(Explanation\s*[\d\.]*—)\s*", r"\n\1 ", text)
    text = re.sub(r"\s*(Illustration\s*[\d\.]*—|\(a\)|\(b\)|\(c\))\s*", r"\n\1 ", text)
    return text.strip()


def parse_bns():
    if not RAW_BNS_PDF.exists():
        raise FileNotFoundError(f"Raw BNS PDF not found at {RAW_BNS_PDF}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(RAW_BNS_PDF)

    chunks = []
    ipc_mapping = {}

    for target in BNS_TARGETS:
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
            print(f"Warning: Could not find start page for BNS Section {sec}")
            continue

        pages_text = []
        for p in range(found_start_page, min(found_start_page + 6, len(reader.pages))):
            raw = reader.pages[p].extract_text() or ""
            pages_text.append(clean_bns_page(raw))
        combined = "\n".join(pages_text)

        m_start = start_pat.search(combined)
        if not m_start:
            print(f"Warning: Start pattern not matched in combined text for BNS Section {sec}")
            continue

        sub = combined[m_start.start():]
        m_end = end_pat.search(sub)
        body = sub[:m_end.start()].strip() if m_end else sub.strip()

        clean_norm = normalize_legal_text(body)
        location_page = found_start_page + 1

        chunk_data = {
            "chunk_id": f"bns-sec-{sec}",
            "source_id": "bns-2023",
            "law": "Bharatiya Nyaya Sanhita, 2023",
            "part": target["chapter"],
            "part_title": target["chapter_title"],
            "subheading": target["chapter_title"],
            "section": f"Section {sec}",
            "title": f"Section {sec}: {target['title']}",
            "text": clean_norm,
            "old_equivalent": target["old_equivalent"],
            "location": f"BNS 2023, Section {sec}, Page {location_page}",
        }
        chunks.append(chunk_data)

        ipc_mapping[f"BNS Section {sec}"] = {
            "title": target["title"],
            "old_ipc_equivalent": target["old_equivalent"],
            "review_status": "needs human review",
            "source": "Gazette of India Act No. 45 of 2023",
        }

    out_path = PROCESSED_DIR / "bns_chunks.json"
    out_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully processed {len(chunks)} BNS sections -> {out_path}")

    mapping_path = MAPPINGS_DIR / "ipc_to_bns.json"
    mapping_path.write_text(json.dumps(ipc_mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully generated IPC-to-BNS mapping -> {mapping_path}")

    return chunks


if __name__ == "__main__":
    parse_bns()
