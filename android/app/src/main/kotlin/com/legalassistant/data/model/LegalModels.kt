package com.legalassistant.data.model

import com.google.gson.annotations.SerializedName

/**
 * Request payload sent to POST /ask
 */
data class QuestionRequest(
    @SerializedName("question") val question: String
)

/**
 * Answer status matching the Python backend enum AnswerStatus
 */
enum class AnswerStatus(val value: String) {
    @SerializedName("answered")
    ANSWERED("answered"),

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
    @SerializedName("simple") val simple: String,
    @SerializedName("detailed") val detailed: String
)

/**
 * Layer 2 source detail: verbatim quote, section, old law equivalent, and source link
 */
data class SourceDetail(
    @SerializedName("claim") val claim: String,
    @SerializedName("law") val law: String,
    @SerializedName("section") val section: String,
    @SerializedName("old_equivalent") val oldEquivalent: String? = null,
    @SerializedName("quote") val quote: String,
    @SerializedName("source_id") val sourceId: String,
    @SerializedName("source_title") val sourceTitle: String,
    @SerializedName("source_url") val sourceUrl: String,
    @SerializedName("location") val location: String
)

/**
 * Landmark judgment citation
 */
data class RelatedJudgment(
    @SerializedName("case_name") val caseName: String,
    @SerializedName("citation") val citation: String,
    @SerializedName("holding") val holding: String,
    @SerializedName("source_id") val sourceId: String
)

/**
 * Root legal response from POST /ask
 */
data class LegalResponse(
    @SerializedName("status") val status: AnswerStatus,
    @SerializedName("question") val question: String,
    @SerializedName("short_answer") val shortAnswer: ShortAnswer? = null,
    @SerializedName("key_points") val keyPoints: List<String> = emptyList(),
    @SerializedName("details") val details: List<SourceDetail> = emptyList(),
    @SerializedName("related_judgments") val relatedJudgments: List<RelatedJudgment> = emptyList(),
    @SerializedName("last_verified") val lastVerified: String? = null,
    @SerializedName("disclaimer") val disclaimer: String = "General information, not legal advice."
)

/**
 * Local feedback rating
 */
enum class FeedbackType {
    NONE, HELPFUL, WRONG, REPORTED
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
