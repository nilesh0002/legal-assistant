package com.legalassistant.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.legalassistant.ui.theme.LocalStatusColors

@Composable
fun LoadingSkeleton(
    modifier: Modifier = Modifier
) {
    val statusColors = LocalStatusColors.current

    val infiniteTransition = rememberInfiniteTransition(label = "skeleton_pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.75f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 800, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha_pulse"
    )

    val placeholderColor = statusColors.surfaceContainerHigh.copy(alpha = alpha)

    Card(
        modifier = modifier
            .fillMaxWidth()
            .semantics { contentDescription = "Searching approved legal corpus and verifying statutory evidence" },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = statusColors.surfaceContainerLowest)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Pulse Status Badge Skeleton
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(width = 180.dp, height = 28.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(placeholderColor)
                )
            }

            // Searching text
            Text(
                text = "Retrieving verified passages from official Indian statutes...",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.Medium
            )

            // Paragraph Line Skeletons
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.95f)
                    .height(18.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(placeholderColor)
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.85f)
                    .height(18.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(placeholderColor)
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.65f)
                    .height(18.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(placeholderColor)
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Card quote skeleton
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(80.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(statusColors.surfaceContainerLow.copy(alpha = alpha))
            )
        }
    }
}
