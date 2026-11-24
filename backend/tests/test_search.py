"""
M3 Tests: Hybrid Search retrieval benchmark and API endpoint tests.

Target: 20 test questions, correct source in top 5 at least 90% of the time.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.retrieval.hybrid import HybridRetriever

# 20 diverse legal test queries covering Part III of the Indian Constitution
BENCHMARK_20_QUESTIONS = [
    {
        "query": "protection of life and personal liberty except procedure established by law",
        "expected_article": "Article 21",
        "expected_id": "constitution-art-21",
    },
    {
        "query": "equality before the law and equal protection of laws",
        "expected_article": "Article 14",
        "expected_id": "constitution-art-14",
    },
    {
        "query": "abolition of untouchability and prohibition of its practice",
        "expected_article": "Article 17",
        "expected_id": "constitution-art-17",
    },
    {
        "query": "free and compulsory education to all children aged 6 to 14",
        "expected_article": "Article 21A",
        "expected_id": "constitution-art-21a",
    },
    {
        "query": "freedom of speech and expression and right to assemble peacefully without arms",
        "expected_article": "Article 19",
        "expected_id": "constitution-art-19",
    },
    {
        "query": "writs of habeas corpus, mandamus, prohibition, and certiorari by Supreme Court",
        "expected_article": "Article 32",
        "expected_id": "constitution-art-32",
    },
    {
        "query": "prohibition of discrimination on grounds only of religion, race, caste, sex or place of birth",
        "expected_article": "Article 15",
        "expected_id": "constitution-art-15",
    },
    {
        "query": "prohibition of traffic in human beings and forced labour begar",
        "expected_article": "Article 23",
        "expected_id": "constitution-art-23",
    },
    {
        "query": "protection against arrest and preventive detention grounds of arrest",
        "expected_article": "Article 22",
        "expected_id": "constitution-art-22",
    },
    {
        "query": "freedom of conscience and free profession practice and propagation of religion",
        "expected_article": "Article 25",
        "expected_id": "constitution-art-25",
    },
    {
        "query": "equality of opportunity in matters of public employment under the State",
        "expected_article": "Article 16",
        "expected_id": "constitution-art-16",
    },
    {
        "query": "prohibition of employment of children below the age of fourteen years in factories",
        "expected_article": "Article 24",
        "expected_id": "constitution-art-24",
    },
    {
        "query": "protection in respect of conviction for offences double jeopardy self-incrimination",
        "expected_article": "Article 20",
        "expected_id": "constitution-art-20",
    },
    {
        "query": "abolition of titles no citizen shall accept any title from foreign State",
        "expected_article": "Article 18",
        "expected_id": "constitution-art-18",
    },
    {
        "query": "freedom to manage religious affairs establish institutions for religious purposes",
        "expected_article": "Article 26",
        "expected_id": "constitution-art-26",
    },
    {
        "query": "freedom as to payment of taxes for promotion of any particular religion",
        "expected_article": "Article 27",
        "expected_id": "constitution-art-27",
    },
    {
        "query": "protection of interests of minorities conserving language script or culture",
        "expected_article": "Article 29",
        "expected_id": "constitution-art-29",
    },
    {
        "query": "right of minorities to establish and administer educational institutions",
        "expected_article": "Article 30",
        "expected_id": "constitution-art-30",
    },
    {
        "query": "laws inconsistent with or in derogation of fundamental rights shall be void",
        "expected_article": "Article 13",
        "expected_id": "constitution-art-13",
    },
    {
        "query": "definition of the State includes Government and Parliament of India",
        "expected_article": "Article 12",
        "expected_id": "constitution-art-12",
    },
]


@pytest.mark.asyncio
async def test_20_benchmark_questions_top5_accuracy():
    """
    Evaluate hybrid search across 20 benchmark questions.
    Target: correct source in top 5 at least 90% of the time (>= 18 / 20).
    """
    retriever = HybridRetriever()
    correct_count = 0
    results_summary = []

    for item in BENCHMARK_20_QUESTIONS:
        query = item["query"]
        expected_id = item["expected_id"]
        expected_art = item["expected_article"]

        results = await retriever.search(query=query, top_k=5)
        retrieved_ids = [r.chunk_id for r in results]

        is_hit = expected_id in retrieved_ids
        rank = retrieved_ids.index(expected_id) + 1 if is_hit else -1

        if is_hit:
            correct_count += 1

        results_summary.append((expected_art, is_hit, rank, query[:50]))

    accuracy = (correct_count / len(BENCHMARK_20_QUESTIONS)) * 100.0
    print(f"\n[Hybrid Search Benchmark] Accuracy: {correct_count}/{len(BENCHMARK_20_QUESTIONS)} ({accuracy:.1f}%)")
    for art, hit, rank, q in results_summary:
        status_sym = f"RANK {rank}" if hit else "MISS"
        print(f"  [{status_sym:>6}] {art}: '{q}...'")

    assert accuracy >= 90.0, f"Expected at least 90% top-5 accuracy, achieved {accuracy:.1f}%"


BENCHMARK_15_ARREST_BAIL_QUESTIONS = [
    {
        "query": "when can police arrest a person without warrant under Section 35 BNSS",
        "expected_section": "Section 35",
        "expected_id": "bnss-sec-35",
    },
    {
        "query": "notice of appearance before police officer in cognizable offences punishable up to seven years",
        "expected_section": "Section 35",
        "expected_id": "bnss-sec-35",
    },
    {
        "query": "person arrested without warrant to be informed of grounds of arrest forthwith",
        "expected_section": "Section 47",
        "expected_id": "bnss-sec-47",
    },
    {
        "query": "police officer shall inform arrested person of right to be released on bail for bailable offence",
        "expected_section": "Section 47",
        "expected_id": "bnss-sec-47",
    },
    {
        "query": "obligation of police officer to inform relative or friend about arrest and place of custody",
        "expected_section": "Section 48",
        "expected_id": "bnss-sec-48",
    },
    {
        "query": "arrested person to be taken before Magistrate having jurisdiction without unnecessary delay",
        "expected_section": "Section 57",
        "expected_id": "bnss-sec-57",
    },
    {
        "query": "police officer taking person arrested without warrant before officer in charge of police station",
        "expected_section": "Section 57",
        "expected_id": "bnss-sec-57",
    },
    {
        "query": "person arrested not to be detained in custody more than twenty-four hours without Magistrate order",
        "expected_section": "Section 58",
        "expected_id": "bnss-sec-58",
    },
    {
        "query": "twenty-four hours maximum detention limit exclusive of journey time from place of arrest",
        "expected_section": "Section 58",
        "expected_id": "bnss-sec-58",
    },
    {
        "query": "in what cases bail to be taken when person other than accused of non-bailable offence is arrested",
        "expected_section": "Section 478",
        "expected_id": "bnss-sec-478",
    },
    {
        "query": "release on bail of indigent person unable to give bail within a week without sureties",
        "expected_section": "Section 478",
        "expected_id": "bnss-sec-478",
    },
    {
        "query": "maximum period for which undertrial prisoner can be detained in custody during investigation or trial",
        "expected_section": "Section 479",
        "expected_id": "bnss-sec-479",
    },
    {
        "query": "first-time offender undertrial release on bond after undergoing detention for one-third of maximum imprisonment",
        "expected_section": "Section 479",
        "expected_id": "bnss-sec-479",
    },
    {
        "query": "when bail may be taken in case of non-bailable offence by court other than High Court or Sessions",
        "expected_section": "Section 480",
        "expected_id": "bnss-sec-480",
    },
    {
        "query": "direction for grant of bail to person apprehending arrest anticipatory bail High Court or Court of Session",
        "expected_section": "Section 482",
        "expected_id": "bnss-sec-482",
    },
]


@pytest.mark.asyncio
async def test_15_arrest_and_bail_questions_top5_accuracy():
    """
    Evaluate hybrid search across 15 arrest and bail questions under BNSS 2023.
    Target: correct section in top 5 at least 90% of the time (>= 14 / 15).
    """
    retriever = HybridRetriever()
    correct_count = 0
    results_summary = []

    for item in BENCHMARK_15_ARREST_BAIL_QUESTIONS:
        query = item["query"]
        expected_id = item["expected_id"]
        expected_sec = item["expected_section"]

        results = await retriever.search(query=query, top_k=5)
        retrieved_ids = [r.chunk_id for r in results]

        is_hit = expected_id in retrieved_ids
        rank = retrieved_ids.index(expected_id) + 1 if is_hit else -1

        if is_hit:
            correct_count += 1

        results_summary.append((expected_sec, is_hit, rank, query[:50]))

    accuracy = (correct_count / len(BENCHMARK_15_ARREST_BAIL_QUESTIONS)) * 100.0
    print(f"\n[BNSS Arrest & Bail Benchmark] Accuracy: {correct_count}/{len(BENCHMARK_15_ARREST_BAIL_QUESTIONS)} ({accuracy:.1f}%)")
    for sec, hit, rank, q in results_summary:
        status_sym = f"RANK {rank}" if hit else "MISS"
        print(f"  [{status_sym:>6}] {sec}: '{q}...'")

    assert accuracy >= 90.0, f"Expected at least 90% top-5 accuracy, achieved {accuracy:.1f}%"


@pytest.mark.asyncio
async def test_api_post_search():
    """Test POST /search endpoint returns valid JSON structure with scores."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/search",
            json={"query": "right to education for children", "top_k": 3},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "right to education for children"
    assert data["total_results"] > 0
    top = data["results"][0]
    assert top["chunk_id"] == "constitution-art-21a"
    assert "Article 21A" in top["article"]
    assert top["score"] > 0.0
    assert "text" in top
    assert "source_id" in top


@pytest.mark.asyncio
async def test_api_get_search():
    """Test GET /search convenience endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/search?q=untouchability&top_k=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    assert data["results"][0]["chunk_id"] == "constitution-art-17"


@pytest.mark.asyncio
async def test_search_min_score_filter():
    """Results below min_score threshold should be filtered out."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A threshold of 0.99 will filter out all but near-exact rank 1 matches
        response = await client.post(
            "/search",
            json={"query": "right to life", "top_k": 5, "min_score": 0.95},
        )

    assert response.status_code == 200
    data = response.json()
    for item in data["results"]:
        assert item["score"] >= 0.95
