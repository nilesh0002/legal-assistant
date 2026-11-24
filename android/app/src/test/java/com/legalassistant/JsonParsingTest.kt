package com.legalassistant

import com.google.gson.Gson
import com.legalassistant.data.model.AnswerStatus
import com.legalassistant.data.model.LegalResponse
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
            "related_judgments": [],
            "last_verified": "2026-11-22",
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.ANSWERED, response.status)
        assertEquals("What is Article 21 of the Indian Constitution?", response.question)
        assertNotNull(response.shortAnswer)
        assertTrue(response.shortAnswer!!.simple.contains("No person shall be deprived of his life"))
        assertFalse(response.shortAnswer!!.simple.contains("citizens"))
        assertEquals(1, response.details.size)
        assertEquals("Article 21", response.details[0].section)
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
                "simple": "Under Section 35, police may arrest without warrant.",
                "detailed": "Detailed text from BNSS 2023."
            },
            "key_points": [
                "Previous Law Reference: Corresponding provision was Section 41 CrPC (needs human review)."
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
    fun testParseInsufficientEvidenceResponse() {
        val json = """
        {
            "status": "insufficient_evidence",
            "question": "What is the penalty for municipal zoning violation?",
            "short_answer": null,
            "key_points": [
                "No sufficiently relevant passages were found in the approved legal corpus.",
                "The system refuses to generate answers without verified source evidence."
            ],
            "details": [],
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.INSUFFICIENT_EVIDENCE, response.status)
        assertNull(response.shortAnswer)
        assertTrue(response.details.isEmpty())
        assertEquals(2, response.keyPoints.size)
    }

    @Test
    fun testParseOutOfScopeResponse() {
        val json = """
        {
            "status": "out_of_scope",
            "question": "What is the recipe for butter chicken?",
            "short_answer": null,
            "key_points": [
                "This assistant only answers questions regarding the Constitution of India and BNSS."
            ],
            "details": [],
            "disclaimer": "General information, not legal advice."
        }
        """.trimIndent()

        val response = gson.fromJson(json, LegalResponse::class.java)

        assertEquals(AnswerStatus.OUT_OF_SCOPE, response.status)
        assertNull(response.shortAnswer)
    }
}
