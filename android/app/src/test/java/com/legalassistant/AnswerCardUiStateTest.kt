package com.legalassistant

import com.legalassistant.data.model.*
import org.junit.Assert.*
import org.junit.Test

/**
 * UI State and Logic Tests for Answer Screen Components.
 * Tests that all 6 statuses, two-layer simple/detailed texts, verbatim quotes,
 * and clarification options conform to UI presentation requirements.
 */
class AnswerCardUiStateTest {

    @Test
    fun testAnsweredUiStateLayer1AndLayer2() {
        val response = LegalResponse(
            status = AnswerStatus.ANSWERED,
            question = "When can police arrest without warrant?",
            shortAnswer = ShortAnswer(
                simple = "Under Section 35 of BNSS, police may arrest without a warrant in cognizable offences.",
                detailed = "Section 35 of the Bharatiya Nagarik Suraksha Sanhita, 2023 enumerates circumstances where a police officer may arrest without an order from a Magistrate."
            ),
            keyPoints = listOf("Applies to cognizable offences punishable with imprisonment"),
            details = listOf(
                SourceDetail(
                    claim = "Section 35 provides for arrest without warrant",
                    law = "Bharatiya Nagarik Suraksha Sanhita, 2023",
                    section = "Section 35",
                    oldEquivalent = "Section 41 CrPC",
                    quote = "Any police officer may without an order from a Magistrate and without a warrant, arrest any person...",
                    sourceId = "bnss-2023",
                    sourceTitle = "Section 35: When police may arrest without warrant",
                    sourceUrl = "https://egazette.gov.in/WriteReadData/2023/250884.pdf",
                    location = "BNSS 2023, Page 13"
                )
            ),
            lastVerified = "2026-11-24",
            disclaimer = "General information, not legal advice."
        )

        // Verify Status
        assertEquals(AnswerStatus.ANSWERED, response.status)

        // Verify Layer 1 Simple vs Detailed
        assertNotNull(response.shortAnswer)
        assertTrue(response.shortAnswer!!.simple.contains("Section 35"))
        assertTrue(response.shortAnswer!!.detailed.contains("Bharatiya Nagarik Suraksha Sanhita"))

        // Verify Layer 2 Citations & Quotes
        assertEquals(1, response.details.size)
        val detail = response.details[0]
        assertEquals("Section 35", detail.section)
        assertEquals("Section 41 CrPC", detail.oldEquivalent)
        assertTrue(detail.quote.startsWith("Any police officer may"))
        assertEquals("https://egazette.gov.in/WriteReadData/2023/250884.pdf", detail.sourceUrl)
        assertEquals("2026-11-24", response.lastVerified)
    }

    @Test
    fun testNeedsClarificationUiStateOptions() {
        val response = LegalResponse(
            status = AnswerStatus.NEEDS_CLARIFICATION,
            question = "How to apply for bail?",
            clarificationQuestion = "Which bail procedure are you inquiring about?",
            clarificationOptions = listOf(
                "Bailable offences (Section 478 BNSS)",
                "Non-bailable offences (Section 480 BNSS)",
                "Anticipatory bail prior to arrest (Section 482 BNSS)"
            )
        )

        assertEquals(AnswerStatus.NEEDS_CLARIFICATION, response.status)
        assertEquals("Which bail procedure are you inquiring about?", response.clarificationQuestion)
        assertEquals(3, response.clarificationOptions.size)
        assertTrue(response.clarificationOptions.all { it.isNotBlank() })
    }

    @Test
    fun testNotCoveredYetUiState() {
        val response = LegalResponse(
            status = AnswerStatus.NOT_COVERED_YET,
            question = "What is the penalty for drunk driving?",
            uncoveredArea = "Motor Vehicles Act, 1988"
        )

        assertEquals(AnswerStatus.NOT_COVERED_YET, response.status)
        assertEquals("Motor Vehicles Act, 1988", response.uncoveredArea)
    }

    @Test
    fun testInsufficientEvidenceWithRelatedSources() {
        val response = LegalResponse(
            status = AnswerStatus.INSUFFICIENT_EVIDENCE,
            question = "Does Article 39(f) apply to private schools?",
            relatedSources = listOf(
                SourceDetail(
                    claim = "Article 37 declares Directive Principles non-enforceable by courts",
                    law = "Constitution of India",
                    section = "Article 37",
                    quote = "The provisions contained in this Part shall not be enforceable by any court",
                    sourceId = "constitution-india",
                    sourceTitle = "Article 37",
                    sourceUrl = "https://legislative.gov.in",
                    location = "Part IV, Article 37"
                )
            )
        )

        assertEquals(AnswerStatus.INSUFFICIENT_EVIDENCE, response.status)
        assertEquals(1, response.relatedSources.size)
        assertEquals("Article 37", response.relatedSources[0].section)
    }

    @Test
    fun testAnswerStatusFromStringAllCases() {
        assertEquals(AnswerStatus.ANSWERED, AnswerStatus.fromString("answered"))
        assertEquals(AnswerStatus.NEEDS_CLARIFICATION, AnswerStatus.fromString("needs_clarification"))
        assertEquals(AnswerStatus.NOT_COVERED_YET, AnswerStatus.fromString("not_covered_yet"))
        assertEquals(AnswerStatus.INSUFFICIENT_EVIDENCE, AnswerStatus.fromString("insufficient_evidence"))
        assertEquals(AnswerStatus.OUT_OF_SCOPE, AnswerStatus.fromString("out_of_scope"))
        assertEquals(AnswerStatus.ERROR, AnswerStatus.fromString("error"))
        assertEquals(AnswerStatus.ERROR, AnswerStatus.fromString("unknown_status_xyz"))
        assertEquals(AnswerStatus.ERROR, AnswerStatus.fromString(null))
    }
}
