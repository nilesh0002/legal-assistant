package com.legalassistant.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.outlined.QuestionAnswer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import com.legalassistant.data.model.FeedbackType
import com.legalassistant.ui.AppScreen
import com.legalassistant.ui.LegalChatViewModel
import com.legalassistant.ui.components.AnswerCard
import com.legalassistant.ui.components.FeedbackBottomSheet
import com.legalassistant.ui.components.LoadingSkeleton
import com.legalassistant.ui.theme.LocalStatusColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: LegalChatViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    val statusColors = LocalStatusColors.current
    val scrollState = rememberScrollState()
    val snackbarHostState = remember { SnackbarHostState() }

    var showFeedbackSheet by remember { mutableStateOf(false) }
    var selectedFeedbackRating by remember { mutableStateOf(FeedbackType.HELPFUL) }

    // Observe feedback submission
    LaunchedEffect(uiState.feedbackSubmissionSuccess) {
        if (uiState.feedbackSubmissionSuccess == true) {
            snackbarHostState.showSnackbar("Thank you! Feedback recorded in review queue.")
        } else if (uiState.feedbackSubmissionSuccess == false) {
            snackbarHostState.showSnackbar("Could not submit feedback to server.")
        }
    }

    if (showFeedbackSheet) {
        FeedbackBottomSheet(
            initialRating = selectedFeedbackRating,
            onDismiss = { showFeedbackSheet = false },
            onSubmit = { rating, comment ->
                viewModel.submitFeedback(rating, comment)
            }
        )
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text("Legal Consultation", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(
                        onClick = { viewModel.navigateTo(AppScreen.HOME) },
                        modifier = Modifier.size(48.dp)
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back to Home"
                        )
                    }
                },
                actions = {
                    IconButton(
                        onClick = { viewModel.navigateTo(AppScreen.COVERAGE) },
                        modifier = Modifier.size(48.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Outlined.QuestionAnswer,
                            contentDescription = "View covered statutes"
                        )
                    }
                }
            )
        },
        bottomBar = {
            Surface(
                tonalElevation = 3.dp,
                color = MaterialTheme.colorScheme.surface,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .padding(horizontal = 12.dp, vertical = 8.dp)
                        .navigationBarsPadding()
                        .imePadding(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = uiState.query,
                        onValueChange = { viewModel.onQueryChange(it) },
                        placeholder = { Text("Ask a follow-up or new question...") },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(24.dp),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                        keyboardActions = KeyboardActions(onSearch = { viewModel.askQuestion() })
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    IconButton(
                        onClick = { viewModel.askQuestion() },
                        enabled = uiState.query.isNotBlank() && !uiState.isLoading,
                        modifier = Modifier.size(48.dp),
                        colors = IconButtonDefaults.filledIconButtonColors()
                    ) {
                        Icon(imageVector = Icons.Filled.Send, contentDescription = "Send legal question")
                    }
                }
            }
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Spacer(modifier = Modifier.height(4.dp))

            // User Question Card
            if (uiState.query.isNotBlank()) {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.primaryContainer,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "QUESTION SUBMITTED",
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = uiState.query,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }

            // Error Message Card
            if (uiState.errorMessage != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.error)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "Connection / Server Alert",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                        Text(
                            text = uiState.errorMessage ?: "Unknown error",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                        Button(
                            onClick = { viewModel.retryLastQuestion() },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                        ) {
                            Icon(imageVector = Icons.Default.Refresh, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Retry Question")
                        }
                    }
                }
            }

            // Loading Skeleton
            if (uiState.isLoading) {
                LoadingSkeleton()
            }

            // Answer Content Card
            if (!uiState.isLoading && uiState.currentAnswer != null) {
                AnswerCard(
                    response = uiState.currentAnswer!!,
                    isDetailedMode = uiState.isDetailedMode,
                    onToggleDetailMode = { viewModel.toggleDetailMode(it) },
                    isDetailsExpanded = uiState.isDetailsExpanded,
                    onToggleDetailsExpanded = { viewModel.toggleDetailsExpanded() },
                    currentFeedback = uiState.currentFeedback,
                    onFeedbackSelected = { rating ->
                        selectedFeedbackRating = rating
                        showFeedbackSheet = true
                    },
                    onClarificationOptionSelected = { option ->
                        viewModel.askQuestion(option)
                    },
                    onViewCoverageSelected = {
                        viewModel.navigateTo(AppScreen.COVERAGE)
                    },
                    onRetrySelected = {
                        viewModel.retryLastQuestion()
                    }
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}
