package com.legalassistant.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import com.legalassistant.data.model.AnswerStatus
import com.legalassistant.ui.AppScreen
import com.legalassistant.ui.LegalChatViewModel
import com.legalassistant.ui.components.AnswerCard
import com.legalassistant.ui.components.ErrorCard
import com.legalassistant.ui.components.InsufficientEvidenceCard
import com.legalassistant.ui.components.OutOfScopeCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: LegalChatViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    val scrollState = rememberScrollState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Legal Consultation", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = { viewModel.navigateTo(AppScreen.HOME) }) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                }
            )
        },
        bottomBar = {
            Surface(
                tonalElevation = 3.dp,
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
                        placeholder = { Text("Ask another question...") },
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
                        colors = IconButtonDefaults.filledIconButtonColors()
                    ) {
                        Icon(imageVector = Icons.Filled.Send, contentDescription = "Send")
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

            // User Question Bubble
            if (uiState.query.isNotBlank()) {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.primaryContainer,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(
                            text = "Question",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = uiState.query,
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }

            // Loading State
            if (uiState.isLoading) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator()
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "Searching verified statutes & validating text...",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            // Error State
            if (!uiState.isLoading && uiState.errorMessage != null && uiState.currentAnswer == null) {
                ErrorCard(
                    errorMessage = uiState.errorMessage ?: "Network error",
                    onRetry = { viewModel.askQuestion() }
                )
            }

            // Response State
            if (!uiState.isLoading && uiState.currentAnswer != null) {
                val resp = uiState.currentAnswer!!
                when (resp.status) {
                    AnswerStatus.ANSWERED -> {
                        AnswerCard(
                            response = resp,
                            isDetailedMode = uiState.isDetailedMode,
                            onToggleDetailMode = { viewModel.toggleDetailMode(it) },
                            isDetailsExpanded = uiState.isDetailsExpanded,
                            onToggleDetailsExpanded = { viewModel.toggleDetailsExpanded() },
                            currentFeedback = uiState.currentFeedback,
                            onFeedbackSelected = { viewModel.setFeedback(it) }
                        )
                    }
                    AnswerStatus.INSUFFICIENT_EVIDENCE -> {
                        InsufficientEvidenceCard(response = resp)
                    }
                    AnswerStatus.OUT_OF_SCOPE -> {
                        OutOfScopeCard(response = resp)
                    }
                    AnswerStatus.ERROR -> {
                        ErrorCard(
                            errorMessage = resp.keyPoints.firstOrNull() ?: "An error occurred",
                            onRetry = { viewModel.askQuestion() }
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}
