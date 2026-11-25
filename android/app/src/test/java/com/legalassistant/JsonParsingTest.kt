package com.legalassistant

import com.google.gson.Gson
import com.legalassistant.data.model.*
import org.junit.Assert.*
import org.junit.Test

class JsonParsingTest {

    private val gson = Gson()

    @Test
    fun testParseAnsweredResponse() {
        val json = """
        {
            "status": "answered",
            "question": "What is Article 21 of the Indian Constitution?",
            "short_answer": {
                "simple": "Under Article 21 (Protection of life and personal liberty), the law provides that no person shall be deprived of his life or personal liberty except according to procedure established by law.",
                "detailed": "According to Article 21 of the Constitution of India (Part III, Fundamental Rights), the statutory text provides: \"No person shall be deprived of his life or personal liberty except according to procedure established by law.\""
            },
            "key_points": [
                "Provision: Article 21 (Protection of life and personal liberty) of the Constitution of India",
                "Category: Right to Freedom",
                "Operative text: No person shall be deprived of his life or personal liberty except according to procedure established by law."
            ],
            "details": [
                {
                    "claim": "Article 21 provides for protection of life and personal liberty",
                    "law": "Constitution of India",
                    "section": "Article 21",
                    "old_equivalent": null,
                    "quote": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                    "source_id": "constitution-india",
                    "source_title": "Article 21: Protection of life and personal liberty",
                    "source_url": "https://legislative.gov.in/static/uploads/2025/07/c9fe9c9b6840524844316f74bb1c556c.pdf",
                    "location": "Part III, Article 21"
                }
            ],
            "related_judgments": [
                {
                    "case_name": "Maneka Gandhi v. Union of India",
                    "citation": "1978 AIR 597",
                    "holding": "Procedure established by law must be fair, just, and reasonable.",
                    "source_id": "maneka-gandhi-1978"
                }
            ],
            "last_verified": "2026-11-22",
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.ANSWERED, response.status)
        assertEquals("What is Article 21 of the Indian Constitution?", response.question)
        assertNotNull(response.shortAnswer)
        assertTrue(response.shortAnswer!!.simple.contains("no person shall be deprived of his life", ignoreCase = true))
        assertEquals(1, response.details.size)
        assertEquals("Article 21", response.details[0].section)
        assertEquals(1, response.relatedJudgments.size)
        assertEquals("Maneka Gandhi v. Union of India", response.relatedJudgments[0].displayTitle)
        assertEquals("2026-11-22", response.lastVerified)
        assertEquals("General information, not legal advice.", response.disclaimer)
    }

    @Test
    fun testParseBnssResponseWithOldEquivalent() {
        val json = """
        {
            "status": "answered",
            "question": "When can police arrest without warrant under Section 35?",
            "short_answer": {
                "simple": "Under Section 35, police may arrest without warrant in cognizable cases.",
                "detailed": "Detailed text from BNSS 2023 Section 35."
            },
            "key_points": [
                "Previous Law Reference: Corresponding provision was Section 41 CrPC."
            ],
            "details": [
                {
                    "claim": "Section 35 provides for arrest without warrant",
                    "law": "Bharatiya Nagarik Suraksha Sanhita, 2023",
                    "section": "Section 35",
                    "old_equivalent": "Section 41 CrPC",
                    "quote": "Any police officer may without an order from a Magistrate and without a warrant, arrest any person",
                    "source_id": "bnss-2023",
                    "source_title": "Section 35: When police may arrest without warrant",
                    "source_url": "https://egazette.gov.in/WriteReadData/2023/250884.pdf",
                    "location": "BNSS 2023, Section 35, Page 13"
                }
            ],
            "last_verified": "2026-11-24",
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.ANSWERED, response.status)
        assertEquals("Section 41 CrPC", response.details[0].oldEquivalent)
        assertEquals("bnss-2023", response.details[0].sourceId)
        assertEquals("2026-11-24", response.lastVerified)
    }

    @Test
    fun testParseNeedsClarificationResponse() {
        val json = """
        {
            "status": "needs_clarification",
            "question": "What is the procedure for bail?",
            "clarification_question": "Which type of bail procedure are you inquiring about?",
            "clarification_options": [
                "Bail in bailable offences (Section 478 BNSS)",
                "Bail in non-bailable offences (Section 480 BNSS)",
                "Anticipatory bail prior to arrest (Section 482 BNSS)"
            ],
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.NEEDS_CLARIFICATION, response.status)
        assertNotNull(response.clarificationQuestion)
        assertEquals(3, response.clarificationOptions.size)
        assertTrue(response.clarificationOptions[0].contains("478"))
    }

    @Test
    fun testParseNotCoveredYetResponse() {
        val json = """
        {
            "status": "not_covered_yet",
            "question": "What is the fine for driving without helmet?",
            "uncovered_area": "Motor Vehicles Act, 1988",
            "key_points": [
                "Motor vehicle offenses are not indexed yet."
            ],
            "details": [],
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.NOT_COVERED_YET, response.status)
        assertEquals("Motor Vehicles Act, 1988", response.uncoveredArea)
        assertTrue(response.details.isEmpty())
    }

    @Test
    fun testParseInsufficientEvidenceResponseWithRelatedSources() {
        val json = """
        {
            "status": "insufficient_evidence",
            "question": "Does maternity benefit apply to private companies under Directive Principles?",
            "related_sources": [
                {
                    "claim": "Article 37 specifies Directive Principles are not enforceable by courts",
                    "law": "Constitution of India",
                    "section": "Article 37",
                    "quote": "The provisions contained in this Part shall not be enforceable by any court",
                    "source_id": "constitution-india",
                    "source_title": "Article 37: Application of principles",
                    "source_url": "https://legislative.gov.in",
                    "location": "Part IV, Article 37"
                }
            ],
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.INSUFFICIENT_EVIDENCE, response.status)
        assertEquals(1, response.relatedSources.size)
        assertEquals("Article 37", response.relatedSources[0].section)
    }

    @Test
    fun testParseOutOfScopeResponse() {
        val json = """
        {
            "status": "out_of_scope",
            "question": "How to bake chocolate chip cookies?",
            "key_points": [
                "Query is outside the scope of Indian legal statutes."
            ],
            "details": [],
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.OUT_OF_SCOPE, response.status)
        assertNull(response.shortAnswer)
    }

    @Test
    fun testParseErrorResponse() {
        val json = """
        {
            "status": "error",
            "question": "Unknown crash test",
            "short_answer": {
                "simple": "An error occurred during verification",
                "detailed": "Detailed internal error"
            },
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.ERROR, response.status)
        assertEquals("An error occurred during verification", response.shortAnswer?.simple)
    }

    @Test
    fun testParseUnknownOrMissingFieldsWithoutCrashing() {
        // Backend returns extra unknown fields and omits several fields
        val json = """
        {
            "status": "answered",
            "question": "Test unknown fields",
            "unexpected_future_field_xyz": 12345,
            "another_random_field": {"foo": "bar"},
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.ANSWERED, response.status)
        assertEquals("Test unknown fields", response.question)
        assertNull(response.shortAnswer)
        assertTrue(response.details.isEmpty())
        assertTrue(response.keyPoints.isEmpty())
        assertEquals("General information, not legal advice.", response.disclaimer)
    }

    @Test
    fun testParseCoverageResponse() {
        val json = """
        {
            "note": "Selected sections only",
            "total_chunks": 186,
            "laws": [
                {
                    "law": "Constitution of India",
                    "source_id": "constitution-india",
                    "coverage_note": "Selected sections only",
                    "last_verified": "2026-11-22",
                    "sections": [
                        {
                            "section": "Article 21",
                            "title": "Article 21: Protection of life and personal liberty",
                            "old_equivalent": null
                        }
                    ]
                }
            ]
        }
        """.trimIndent()

        val coverage = gson.fromJson(json, CoverageResponse::class.java)

        assertEquals("Selected sections only", coverage.note)
        assertEquals(186, coverage.totalChunks)
        assertEquals(1, coverage.laws.size)
        assertEquals("Constitution of India", coverage.laws[0].law)
        assertEquals("Article 21", coverage.laws[0].sections[0].section)
    }

    @Test
    fun testParseFeedbackResponse() {
        val json = """
        {
            "status": "received",
            "message": "Feedback recorded in review queue"
        }
        """.trimIndent()

        val fb = gson.fromJson(json, FeedbackResponse::class.java)

        assertEquals("received", fb.status)
        assertEquals("Feedback recorded in review queue", fb.message)
    }
}
