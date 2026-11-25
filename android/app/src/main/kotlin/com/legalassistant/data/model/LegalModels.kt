package com.legalassistant.data.model

import com.google.gson.annotations.SerializedName

/**
 * Answer status matching the Python backend enum AnswerStatus
 */
enum class AnswerStatus(val value: String) {
    @SerializedName("answered")
    ANSWERED("answered"),

    @SerializedName("needs_clarification")
    NEEDS_CLARIFICATION("needs_clarification"),

    @SerializedName("not_covered_yet")
    NOT_COVERED_YET("not_covered_yet"),

    @SerializedName("insufficient_evidence")
    INSUFFICIENT_EVIDENCE("insufficient_evidence"),

    @SerializedName("out_of_scope")
    OUT_OF_SCOPE("out_of_scope"),

    @SerializedName("error")
    ERROR("error");

    companion object {
        fun fromString(str: String?): AnswerStatus {
            return entries.firstOrNull { it.value.equals(str, ignoreCase = true) } ?: ERROR
        }
    }
}

/**
 * Layer 1 answer: plain explanation (simple) and full legal summary (detailed)
 */
data class ShortAnswer(
    @SerializedName("simple") val simple: String = "",
    @SerializedName("detailed") val detailed: String = ""
)

/**
 * Layer 2 source detail: verbatim quote, section, old law equivalent, and source link
 */
data class SourceDetail(
    @SerializedName("claim") val claim: String = "",
    @SerializedName("law") val law: String = "",
    @SerializedName("section") val section: String = "",
    @SerializedName("old_equivalent") val oldEquivalent: String? = null,
    @SerializedName("quote") val quote: String = "",
    @SerializedName("source_id") val sourceId: String = "",
    @SerializedName("source_title") val sourceTitle: String = "",
    @SerializedName("source_url") val sourceUrl: String = "",
    @SerializedName("location") val location: String = ""
)

/**
 * Landmark judgment citation
 */
data class RelatedJudgment(
    @SerializedName("name") val name: String? = null,
    @SerializedName("case_name") val caseName: String? = null,
    @SerializedName("year") val year: Any? = null,
    @SerializedName("citation") val citation: String? = null,
    @SerializedName("holding") val holding: String? = null,
    @SerializedName("source_id") val sourceId: String = ""
) {
    val displayTitle: String
        get() = caseName ?: name ?: "Landmark Judgment"

    val displayCitation: String
        get() = citation ?: year?.toString() ?: ""
}

/**
 * Conversation turn for follow-up questions
 */
data class ConversationTurn(
    @SerializedName("question") val question: String,
    @SerializedName("answer") val answer: String? = null
)

/**
 * Request payload sent to POST /ask
 */
data class QuestionRequest(
    @SerializedName("question") val question: String,
    @SerializedName("conversation_history") val conversationHistory: List<ConversationTurn>? = null
)

/**
 * Root legal response from POST /ask
 */
data class LegalResponse(
    @SerializedName("status") val status: AnswerStatus = AnswerStatus.ERROR,
    @SerializedName("question") val question: String = "",
    @SerializedName("short_answer") val shortAnswer: ShortAnswer? = null,
    @SerializedName("key_points") val keyPoints: List<String> = emptyList(),
    @SerializedName("details") val details: List<SourceDetail> = emptyList(),
    @SerializedName("related_sources") val relatedSources: List<SourceDetail> = emptyList(),
    @SerializedName("uncovered_area") val uncoveredArea: String? = null,
    @SerializedName("clarification_question") val clarificationQuestion: String? = null,
    @SerializedName("clarification_options") val clarificationOptions: List<String> = emptyList(),
    @SerializedName("related_judgments") val relatedJudgments: List<RelatedJudgment> = emptyList(),
    @SerializedName("last_verified") val lastVerified: String? = null,
    @SerializedName("disclaimer") val disclaimer: String = "General information, not legal advice."
)

/**
 * Coverage models for GET /coverage
 */
data class SectionInfo(
    @SerializedName("section") val section: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("old_equivalent") val oldEquivalent: String? = null
)

data class LawCoverage(
    @SerializedName("law") val law: String = "",
    @SerializedName("source_id") val sourceId: String = "",
    @SerializedName("coverage_note") val coverageNote: String = "",
    @SerializedName("last_verified") val lastVerified: String? = null,
    @SerializedName("sections") val sections: List<SectionInfo> = emptyList()
)

data class CoverageResponse(
    @SerializedName("note") val note: String = "",
    @SerializedName("total_chunks") val totalChunks: Int = 0,
    @SerializedName("laws") val laws: List<LawCoverage> = emptyList()
)

/**
 * Example questions returned by GET /examples
 */
data class ExamplesResponse(
    @SerializedName("examples") val examples: List<String> = emptyList()
)

/**
 * Feedback request payload sent to POST /feedback
 */
data class FeedbackRequest(
    @SerializedName("question") val question: String,
    @SerializedName("feedback") val feedback: String, // "helpful" or "wrong"
    @SerializedName("response_status") val responseStatus: String? = null,
    @SerializedName("comment") val comment: String? = null,
    @SerializedName("details") val details: Map<String, Any> = emptyMap()
)

data class FeedbackResponse(
    @SerializedName("status") val status: String = "received",
    @SerializedName("message") val message: String = ""
)

/**
 * Local feedback rating
 */
enum class FeedbackType {
    NONE, HELPFUL, WRONG
}

/**
 * Chat history record stored strictly on device
 */
data class ChatHistoryItem(
    val id: String = java.util.UUID.randomUUID().toString(),
    val timestamp: Long = System.currentTimeMillis(),
    val question: String,
    val response: LegalResponse,
    var feedback: FeedbackType = FeedbackType.NONE
)
