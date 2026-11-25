package com.legalassistant.ui.components

import android.content.Intent
import android.net.Uri
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.legalassistant.data.model.AnswerStatus
import com.legalassistant.data.model.FeedbackType
import com.legalassistant.data.model.LegalResponse
import com.legalassistant.data.model.SourceDetail
import com.legalassistant.ui.theme.LocalStatusColors
import com.legalassistant.ui.theme.StatuteQuoteStyle

@Composable
fun AnswerCard(
    response: LegalResponse,
    isDetailedMode: Boolean,
    onToggleDetailMode: (Boolean) -> Unit,
    isDetailsExpanded: Boolean,
    onToggleDetailsExpanded: () -> Unit,
    currentFeedback: FeedbackType,
    onFeedbackSelected: (FeedbackType) -> Unit,
    onClarificationOptionSelected: (String) -> Unit = {},
    onViewCoverageSelected: () -> Unit = {},
    onRetrySelected: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val statusColors = LocalStatusColors.current

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = statusColors.surfaceContainerLowest),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header: Status Badge & Date
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                StatusBadge(status = response.status)

                if (!response.lastVerified.isNullOrBlank()) {
                    Text(
                        text = "Verified ${response.lastVerified}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // BRANCH BY STATUS
            when (response.status) {
                AnswerStatus.ANSWERED -> {
                    AnsweredContent(
                        response = response,
                        isDetailedMode = isDetailedMode,
                        onToggleDetailMode = onToggleDetailMode,
                        isDetailsExpanded = isDetailsExpanded,
                        onToggleDetailsExpanded = onToggleDetailsExpanded,
                        currentFeedback = currentFeedback,
                        onFeedbackSelected = onFeedbackSelected
                    )
                }
                AnswerStatus.NEEDS_CLARIFICATION -> {
                    NeedsClarificationContent(
                        response = response,
                        onOptionSelected = onClarificationOptionSelected
                    )
                }
                AnswerStatus.NOT_COVERED_YET -> {
                    NotCoveredContent(
                        response = response,
                        onViewCoverage = onViewCoverageSelected
                    )
                }
                AnswerStatus.INSUFFICIENT_EVIDENCE -> {
                    InsufficientEvidenceContent(
                        response = response,
                        onViewCoverage = onViewCoverageSelected
                    )
                }
                AnswerStatus.OUT_OF_SCOPE -> {
                    OutOfScopeContent(
                        response = response,
                        onViewCoverage = onViewCoverageSelected
                    )
                }
                AnswerStatus.ERROR -> {
                    ErrorContent(
                        response = response,
                        onRetry = onRetrySelected
                    )
                }
            }

            // Mandatory Persistent Disclaimer
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = statusColors.surfaceContainerLow,
                shape = RoundedCornerShape(8.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Gavel,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = response.disclaimer,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
private fun AnsweredContent(
    response: LegalResponse,
    isDetailedMode: Boolean,
    onToggleDetailMode: (Boolean) -> Unit,
    isDetailsExpanded: Boolean,
    onToggleDetailsExpanded: () -> Unit,
    currentFeedback: FeedbackType,
    onFeedbackSelected: (FeedbackType) -> Unit
) {
    val statusColors = LocalStatusColors.current

    // Simple / Detailed Toggle (minimum 48dp touch target)
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = statusColors.surfaceContainerLow,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        modifier = Modifier.height(48.dp)
    ) {
        Row(
            modifier = Modifier.padding(4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .clickable { onToggleDetailMode(false) },
                shape = RoundedCornerShape(20.dp),
                color = if (!isDetailedMode) MaterialTheme.colorScheme.primary else Color.Transparent
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = "Simple Plain Language",
                        style = MaterialTheme.typography.labelMedium,
                        color = if (!isDetailedMode) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface
                    )
                }
            }

            Spacer(modifier = Modifier.width(4.dp))

            Surface(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .clickable { onToggleDetailMode(true) },
                shape = RoundedCornerShape(20.dp),
                color = if (isDetailedMode) MaterialTheme.colorScheme.primary else Color.Transparent
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = "Detailed Legal Analysis",
                        style = MaterialTheme.typography.labelMedium,
                        color = if (isDetailedMode) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        }
    }

    // Main Answer Summary Text
    val summaryText = if (!isDetailedMode) {
        response.shortAnswer?.simple ?: "No plain language summary provided."
    } else {
        response.shortAnswer?.detailed ?: response.shortAnswer?.simple ?: "No detailed analysis provided."
    }

    Text(
        text = summaryText,
        style = MaterialTheme.typography.bodyLarge,
        color = MaterialTheme.colorScheme.onSurface,
        lineHeight = 28.sp
    )

    // Key points (if available)
    if (response.keyPoints.isNotEmpty()) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                text = "Key Statutory Points:",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary
            )
            response.keyPoints.forEach { point ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Top
                ) {
                    Text(
                        text = "• ",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = point,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        }
    }

    // LAYER 2: Expandable Official Sources & Verbatim Quotes
    if (response.details.isNotEmpty()) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onToggleDetailsExpanded() }
                .semantics {
                    contentDescription = if (isDetailsExpanded) "Collapse official sources and citations" else "Expand official sources and citations"
                },
            shape = RoundedCornerShape(12.dp),
            color = statusColors.surfaceContainerLow,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.MenuBook,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = "Verified Sources & Exact Quotes (${response.details.size})",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
                Icon(
                    imageVector = if (isDetailsExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
            }
        }

        AnimatedVisibility(
            visible = isDetailsExpanded,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                response.details.forEach { detail ->
                    SourceDetailItem(detail = detail)
                }
            }
        }
    }

    // Related Landmark Judgments
    if (response.relatedJudgments.isNotEmpty()) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                text = "Relevant Landmark Judgments:",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary
            )
            response.relatedJudgments.forEach { j ->
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = statusColors.surfaceContainerLow,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = j.displayTitle,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        if (j.displayCitation.isNotBlank()) {
                            Text(
                                text = "Citation: ${j.displayCitation}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        if (!j.holding.isNullOrBlank()) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = j.holding,
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                }
            }
        }
    }

    // Feedback Row (48dp buttons)
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.End,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "Was this helpful?",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.width(8.dp))

        IconButton(
            onClick = { onFeedbackSelected(FeedbackType.HELPFUL) },
            modifier = Modifier.size(48.dp)
        ) {
            Icon(
                imageVector = if (currentFeedback == FeedbackType.HELPFUL) Icons.Filled.ThumbUp else Icons.Outlined.ThumbUp,
                contentDescription = "Mark as helpful",
                tint = if (currentFeedback == FeedbackType.HELPFUL) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        IconButton(
            onClick = { onFeedbackSelected(FeedbackType.WRONG) },
            modifier = Modifier.size(48.dp)
        ) {
            Icon(
                imageVector = if (currentFeedback == FeedbackType.WRONG) Icons.Filled.ThumbDown else Icons.Outlined.ThumbDown,
                contentDescription = "Report inaccurate",
                tint = if (currentFeedback == FeedbackType.WRONG) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun SourceDetailItem(detail: SourceDetail) {
    val context = LocalContext.current
    val statusColors = LocalStatusColors.current

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = statusColors.surfaceContainerLow),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Law Title & Section Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = detail.law,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )

                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Text(
                        text = detail.section,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }

            // Old Equivalent tag if available
            if (!detail.oldEquivalent.isNullOrBlank()) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = statusColors.surfaceContainerHigh
                ) {
                    Text(
                        text = "Prior Code Equivalent: ${detail.oldEquivalent}",
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Supported Claim
            if (detail.claim.isNotBlank()) {
                Text(
                    text = "Grounded Principle: ${detail.claim}",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium
                )
            }

            // Verbatim Quote in Noto Serif styling with 4dp left border
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = statusColors.surfaceContainerLowest,
                shape = RoundedCornerShape(topEnd = 8.dp, bottomEnd = 8.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            ) {
                Row(modifier = Modifier.height(IntrinsicSize.Min)) {
                    Box(
                        modifier = Modifier
                            .width(4.dp)
                            .fillMaxHeight()
                            .background(statusColors.answered)
                    )
                    Text(
                        text = "\"${detail.quote}\"",
                        style = StatuteQuoteStyle,
                        modifier = Modifier.padding(12.dp),
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }

            // Location and Source Link Button (min 48dp clickable target)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = detail.location.ifBlank { detail.sourceTitle },
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.weight(1f)
                )

                if (detail.sourceUrl.isNotBlank()) {
                    TextButton(
                        onClick = {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(detail.sourceUrl))
                            context.startActivity(intent)
                        },
                        modifier = Modifier.height(48.dp)
                    ) {
                        Icon(imageVector = Icons.Default.OpenInNew, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(text = "Official Source", style = MaterialTheme.typography.labelMedium)
                    }
                }
            }
        }
    }
}

@Composable
private fun NeedsClarificationContent(
    response: LegalResponse,
    onOptionSelected: (String) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            text = response.clarificationQuestion ?: "Your legal question has multiple possible interpretations under Indian law. Please select which scenario applies:",
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.Medium
        )

        // Options chips (min 48dp height)
        if (response.clarificationOptions.isNotEmpty()) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                response.clarificationOptions.forEach { opt ->
                    OutlinedButton(
                        onClick = { onOptionSelected(opt) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(24.dp)
                    ) {
                        Text(
                            text = opt,
                            style = MaterialTheme.typography.labelLarge
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun NotCoveredContent(
    response: LegalResponse,
    onViewCoverage: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            text = "Statutory Domain Not Yet Indexed",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = "NyayaSahayak only answers questions grounded in verified official sources currently in the corpus (Constitution Parts III, IV, IVA; BNSS 2023; BNS 2023; Consumer Protection Act 2019; RTI Act 2005).",
            style = MaterialTheme.typography.bodyMedium
        )

        if (!response.uncoveredArea.isNullOrBlank()) {
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = MaterialTheme.colorScheme.secondaryContainer
            ) {
                Text(
                    text = "Requested Domain: ${response.uncoveredArea}",
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
            }
        }

        Button(
            onClick = onViewCoverage,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(imageVector = Icons.Default.List, contentDescription = null)
            Spacer(modifier = Modifier.width(8.dp))
            Text(text = "View Covered Laws & Sections")
        }
    }
}

@Composable
private fun InsufficientEvidenceContent(
    response: LegalResponse,
    onViewCoverage: () -> Unit
) {
    val statusColors = LocalStatusColors.current

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            text = "Insufficient Official Evidence",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.error
        )

        Text(
            text = "The system refused to generate an answer because no verified passages in the approved legal corpus directly support this query. The system does not speculate.",
            style = MaterialTheme.typography.bodyMedium
        )

        // Show related sources if available
        if (response.relatedSources.isNotEmpty()) {
            Text(
                text = "Closest Related Official Provisions (For Reference Only):",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary
            )

            response.relatedSources.forEach { s ->
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = statusColors.surfaceContainerLow,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(text = "${s.law} — ${s.section}", fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(text = s.quote, style = StatuteQuoteStyle, maxLines = 3)
                    }
                }
            }
        }

        OutlinedButton(
            onClick = onViewCoverage,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(text = "Check Indexed Statutes & Sections")
        }
    }
}

@Composable
private fun OutOfScopeContent(
    response: LegalResponse,
    onViewCoverage: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            text = "Outside Indian Legal Scope",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = "This query falls outside the scope of Indian central statutory law. NyayaSahayak is strictly dedicated to Indian constitutional, criminal procedure, penal, consumer protection, and transparency statutes.",
            style = MaterialTheme.typography.bodyMedium
        )

        OutlinedButton(
            onClick = onViewCoverage,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(text = "Explore Available Legal Topics")
        }
    }
}

@Composable
private fun ErrorContent(
    response: LegalResponse,
    onRetry: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            text = "Unable to Complete Legal Verification",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.error
        )

        Text(
            text = response.shortAnswer?.simple ?: "A communication or validation failure occurred while communicating with the verified legal knowledge backend.",
            style = MaterialTheme.typography.bodyMedium
        )

        Button(
            onClick = onRetry,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(imageVector = Icons.Default.Refresh, contentDescription = null)
            Spacer(modifier = Modifier.width(8.dp))
            Text(text = "Retry Question")
        }
    }
}
