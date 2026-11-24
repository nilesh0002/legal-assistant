"""
M1 Tests: Verify Part III of Constitution corpus parsed from official PDF.
"""

import json
from pathlib import Path
import pytest
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
PART3_JSON = BASE_DIR / "data" / "processed" / "constitution_part3.json"
CHUNKS_JSON = BASE_DIR / "data" / "processed" / "constitution_chunks.json"
SOURCES_YAML = BASE_DIR / "data" / "sources.yaml"


def test_processed_files_exist():
    """Verify that parsed JSON files exist."""
    assert PART3_JSON.exists(), "constitution_part3.json must exist"
    assert CHUNKS_JSON.exists(), "constitution_chunks.json must exist"


def test_part3_article_count():
    """Part III must contain all 30 expected articles."""
    with open(PART3_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    assert len(articles) == 30, f"Expected 30 articles in Part III, found {len(articles)}"

    expected_articles = [
        "Article 12", "Article 13", "Article 14", "Article 15", "Article 16",
        "Article 17", "Article 18", "Article 19", "Article 20", "Article 21",
        "Article 21A", "Article 22", "Article 23", "Article 24", "Article 25",
        "Article 26", "Article 27", "Article 28", "Article 29", "Article 30",
        "Article 31", "Article 31A", "Article 31B", "Article 31C", "Article 31D",
        "Article 32", "Article 32A", "Article 33", "Article 34", "Article 35"
    ]
    extracted_names = [a["article"] for a in articles]
    for expected in expected_articles:
        assert expected in extracted_names, f"{expected} missing from parsed Part III"


def test_part3_schema_compliance():
    """Every chunk must have all required metadata and text fields."""
    with open(PART3_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    required_fields = [
        "chunk_id", "source_id", "law", "part", "part_title",
        "article", "title", "text", "location", "subheading"
    ]
    for art in articles:
        for field in required_fields:
            assert field in art, f"Missing field '{field}' in {art.get('chunk_id')}"
            assert art[field], f"Field '{field}' is empty in {art.get('chunk_id')}"
        assert art["source_id"] == "constitution-india"
        assert art["law"] == "Constitution of India"
        assert art["part"] == "Part III"


def test_exact_word_for_word_quotes():
    """
    Verify verbatim accuracy of landmark constitutional clauses
    directly against the extracted text.
    """
    with open(PART3_JSON, "r", encoding="utf-8") as f:
        articles_by_id = {a["chunk_id"]: a for a in json.load(f)}

    # Article 14: Equality before law
    art14 = articles_by_id["constitution-art-14"]
    assert "equality before the law or the equal protection of the laws" in art14["text"]

    # Article 21: Protection of life and personal liberty
    art21 = articles_by_id["constitution-art-21"]
    assert "No person shall be deprived of his life or personal liberty except according to procedure established by law" in art21["text"]

    # Article 17: Abolition of Untouchability
    art17 = articles_by_id["constitution-art-17"]
    assert "Untouchability" in art17["text"]
    assert "is abolished and its practice in any form is forbidden" in art17["text"]

    # Article 21A: Right to education
    art21a = articles_by_id["constitution-art-21a"]
    assert "free and compulsory education to all children of the age of six to fourteen years" in art21a["text"]

    # Article 32: Remedies for enforcement of rights
    art32 = articles_by_id["constitution-art-32"]
    assert "remedies for enforcement of rights" in art32["title"].lower()
    assert "Supreme Court" in art32["text"]


def test_preamble_in_chunks():
    """Verify Preamble chunk exists in constitution_chunks.json."""
    with open(CHUNKS_JSON, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    preamble_chunks = [c for c in chunks if c["chunk_id"] == "constitution-preamble"]
    assert len(preamble_chunks) == 1
    preamble = preamble_chunks[0]
    assert "WE, THE PEOPLE OF INDIA" in preamble["text"]
    assert "JUSTICE, social, economic and political" in preamble["text"]
    assert "LIBERTY of thought, expression, belief, faith and worship" in preamble["text"]
    assert "EQUALITY of status and of opportunity" in preamble["text"]


def test_sources_yaml_active():
    """Verify that constitution-india is active in data/sources.yaml."""
    with open(SOURCES_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sources = {s["id"]: s for s in data["sources"]}
    assert "constitution-india" in sources
    const = sources["constitution-india"]
    assert const["status"] == "active"
    assert const["retrieved"] is not None
    assert const["url"].endswith(".pdf")
