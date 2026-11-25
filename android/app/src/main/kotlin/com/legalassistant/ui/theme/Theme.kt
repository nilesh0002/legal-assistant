package com.legalassistant.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

@Immutable
data class StatusColors(
    val answered: Color,
    val onAnswered: Color,
    val answeredContainer: Color,
    val onAnsweredContainer: Color,
    val clarification: Color,
    val onClarification: Color,
    val clarificationContainer: Color,
    val onClarificationContainer: Color,
    val notCovered: Color,
    val onNotCovered: Color,
    val notCoveredContainer: Color,
    val onNotCoveredContainer: Color,
    val insufficient: Color,
    val onInsufficient: Color,
    val insufficientContainer: Color,
    val onInsufficientContainer: Color,
    val outOfScope: Color,
    val onOutOfScope: Color,
    val outOfScopeContainer: Color,
    val onOutOfScopeContainer: Color,
    val error: Color,
    val onError: Color,
    val errorContainer: Color,
    val onErrorContainer: Color,
    val surfaceContainerLowest: Color,
    val surfaceContainerLow: Color,
    val surfaceContainer: Color,
    val surfaceContainerHigh: Color,
    val accent: Color
)

val LocalStatusColors = staticCompositionLocalOf {
    StatusColors(
        answered = LightAnswered,
        onAnswered = LightOnAnswered,
        answeredContainer = LightAnsweredContainer,
        onAnsweredContainer = LightOnAnsweredContainer,
        clarification = LightClarification,
        onClarification = LightOnClarification,
        clarificationContainer = LightClarificationContainer,
        onClarificationContainer = LightOnClarificationContainer,
        notCovered = LightNotCovered,
        onNotCovered = LightOnNotCovered,
        notCoveredContainer = LightNotCoveredContainer,
        onNotCoveredContainer = LightOnNotCoveredContainer,
        insufficient = LightInsufficient,
        onInsufficient = LightOnInsufficient,
        insufficientContainer = LightInsufficientContainer,
        onInsufficientContainer = LightOnInsufficientContainer,
        outOfScope = LightOutOfScope,
        onOutOfScope = LightOnOutOfScope,
        outOfScopeContainer = LightOutOfScopeContainer,
        onOutOfScopeContainer = LightOnOutOfScopeContainer,
        error = LightError,
        onError = LightOnError,
        errorContainer = LightErrorContainer,
        onErrorContainer = LightOnErrorContainer,
        surfaceContainerLowest = LightSurfaceContainerLowest,
        surfaceContainerLow = LightSurfaceContainerLow,
        surfaceContainer = LightSurfaceContainer,
        surfaceContainerHigh = LightSurfaceContainerHigh,
        accent = Accent
    )
}

private val LightColorScheme: ColorScheme = lightColorScheme(
    primary = LightPrimary,
    onPrimary = LightOnPrimary,
    primaryContainer = LightPrimaryContainer,
    onPrimaryContainer = LightOnPrimaryContainer,
    secondary = LightSecondary,
    onSecondary = LightOnSecondary,
    secondaryContainer = LightSecondaryContainer,
    onSecondaryContainer = LightOnSecondaryContainer,
    background = LightBackground,
    onBackground = LightOnBackground,
    surface = LightSurface,
    onSurface = LightOnSurface,
    surfaceVariant = LightSurfaceContainerHigh,
    onSurfaceVariant = LightOnSurfaceVariant,
    outline = LightOutline,
    outlineVariant = LightOutlineVariant,
    error = LightError,
    onError = LightOnError,
    errorContainer = LightErrorContainer,
    onErrorContainer = LightOnErrorContainer
)

private val DarkColorScheme: ColorScheme = darkColorScheme(
    primary = DarkPrimary,
    onPrimary = DarkOnPrimary,
    primaryContainer = DarkPrimaryContainer,
    onPrimaryContainer = DarkOnPrimaryContainer,
    secondary = DarkSecondary,
    onSecondary = DarkOnSecondary,
    secondaryContainer = DarkSecondaryContainer,
    onSecondaryContainer = DarkOnSecondaryContainer,
    background = DarkBackground,
    onBackground = DarkOnBackground,
    surface = DarkSurface,
    onSurface = DarkOnSurface,
    surfaceVariant = DarkSurfaceContainerHigh,
    onSurfaceVariant = DarkOnSurfaceVariant,
    outline = DarkOutline,
    outlineVariant = DarkOutlineVariant,
    error = DarkError,
    onError = DarkOnError,
    errorContainer = DarkErrorContainer,
    onErrorContainer = DarkOnErrorContainer
)

@Composable
fun LegalAssistantTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val statusColors = if (darkTheme) {
        StatusColors(
            answered = DarkAnswered,
            onAnswered = DarkOnAnswered,
            answeredContainer = DarkAnsweredContainer,
            onAnsweredContainer = DarkOnAnsweredContainer,
            clarification = DarkClarification,
            onClarification = DarkOnClarification,
            clarificationContainer = DarkClarificationContainer,
            onClarificationContainer = DarkOnClarificationContainer,
            notCovered = DarkNotCovered,
            onNotCovered = DarkOnNotCovered,
            notCoveredContainer = DarkNotCoveredContainer,
            onNotCoveredContainer = DarkOnNotCoveredContainer,
            insufficient = DarkInsufficient,
            onInsufficient = DarkOnInsufficient,
            insufficientContainer = DarkInsufficientContainer,
            onInsufficientContainer = DarkOnInsufficientContainer,
            outOfScope = DarkOutOfScope,
            onOutOfScope = DarkOnOutOfScope,
            outOfScopeContainer = DarkOutOfScopeContainer,
            onOutOfScopeContainer = DarkOnOutOfScopeContainer,
            error = DarkError,
            onError = DarkOnError,
            errorContainer = DarkErrorContainer,
            onErrorContainer = DarkOnErrorContainer,
            surfaceContainerLowest = DarkSurfaceContainerLowest,
            surfaceContainerLow = DarkSurfaceContainerLow,
            surfaceContainer = DarkSurfaceContainer,
            surfaceContainerHigh = DarkSurfaceContainerHigh,
            accent = Accent
        )
    } else {
        StatusColors(
            answered = LightAnswered,
            onAnswered = LightOnAnswered,
            answeredContainer = LightAnsweredContainer,
            onAnsweredContainer = LightOnAnsweredContainer,
            clarification = LightClarification,
            onClarification = LightOnClarification,
            clarificationContainer = LightClarificationContainer,
            onClarificationContainer = LightOnClarificationContainer,
            notCovered = LightNotCovered,
            onNotCovered = LightOnNotCovered,
            notCoveredContainer = LightNotCoveredContainer,
            onNotCoveredContainer = LightOnNotCoveredContainer,
            insufficient = LightInsufficient,
            onInsufficient = LightOnInsufficient,
            insufficientContainer = LightInsufficientContainer,
            onInsufficientContainer = LightOnInsufficientContainer,
            outOfScope = LightOutOfScope,
            onOutOfScope = LightOnOutOfScope,
            outOfScopeContainer = LightOutOfScopeContainer,
            onOutOfScopeContainer = LightOnOutOfScopeContainer,
            error = LightError,
            onError = LightOnError,
            errorContainer = LightErrorContainer,
            onErrorContainer = LightOnErrorContainer,
            surfaceContainerLowest = LightSurfaceContainerLowest,
            surfaceContainerLow = LightSurfaceContainerLow,
            surfaceContainer = LightSurfaceContainer,
            surfaceContainerHigh = LightSurfaceContainerHigh,
            accent = Accent
        )
    }

    CompositionLocalProvider(LocalStatusColors provides statusColors) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = AppTypography,
            content = content
        )
    }
}
