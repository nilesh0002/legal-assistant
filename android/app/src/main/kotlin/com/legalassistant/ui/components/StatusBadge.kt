package com.legalassistant.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.legalassistant.data.model.AnswerStatus
import com.legalassistant.ui.theme.LocalStatusColors

@Composable
fun StatusBadge(
    status: AnswerStatus,
    modifier: Modifier = Modifier
) {
    val statusColors = LocalStatusColors.current

    val (bgColor, fgColor, icon, label) = when (status) {
        AnswerStatus.ANSWERED -> Quadruple(
            statusColors.answeredContainer,
            statusColors.onAnsweredContainer,
            Icons.Default.CheckCircle,
            "Answered with verified law"
        )
        AnswerStatus.NEEDS_CLARIFICATION -> Quadruple(
            statusColors.clarificationContainer,
            statusColors.onClarificationContainer,
            Icons.Default.HelpOutline,
            "Needs clarification"
        )
        AnswerStatus.NOT_COVERED_YET -> Quadruple(
            statusColors.notCoveredContainer,
            statusColors.onNotCoveredContainer,
            Icons.Default.Schedule,
            "Statute not covered yet"
        )
        AnswerStatus.INSUFFICIENT_EVIDENCE -> Quadruple(
            statusColors.insufficientContainer,
            statusColors.onInsufficientContainer,
            Icons.Default.SearchOff,
            "Insufficient official evidence"
        )
        AnswerStatus.OUT_OF_SCOPE -> Quadruple(
            statusColors.outOfScopeContainer,
            statusColors.onOutOfScopeContainer,
            Icons.Default.Block,
            "Outside Indian legal scope"
        )
        AnswerStatus.ERROR -> Quadruple(
            statusColors.errorContainer,
            statusColors.onErrorContainer,
            Icons.Default.Warning,
            "Verification error"
        )
    }

    Row(
        modifier = modifier
            .clip(RoundedCornerShape(20.dp))
            .background(bgColor)
            .padding(horizontal = 12.dp, vertical = 6.dp)
            .semantics { contentDescription = "Status: $label" },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = fgColor,
            modifier = Modifier.size(16.dp)
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold,
            color = fgColor
        )
    }
}

private data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)
