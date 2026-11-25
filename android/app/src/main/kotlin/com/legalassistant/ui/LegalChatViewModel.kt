package com.legalassistant.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.legalassistant.data.api.ApiService
import com.legalassistant.data.api.RateLimitException
import com.legalassistant.data.api.RetrofitClient
import com.legalassistant.data.model.AnswerStatus
import com.legalassistant.data.model.ChatHistoryItem
import com.legalassistant.data.model.ConversationTurn
import com.legalassistant.data.model.CoverageResponse
import com.legalassistant.data.model.FeedbackRequest
import com.legalassistant.data.model.FeedbackType
import com.legalassistant.data.model.LegalResponse
import com.legalassistant.data.model.QuestionRequest
import com.legalassistant.data.repository.LocalHistoryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

enum class AppScreen {
    WELCOME, HOME, CHAT, HISTORY, COVERAGE, ABOUT
}

data class LegalUiState(
    val currentScreen: AppScreen = AppScreen.HOME,
    val query: String = "",
    val isLoading: Boolean = false,
    val currentAnswer: LegalResponse? = null,
    val lastFailedQuery: String? = null,
    val isDetailedMode: Boolean = false, // false = Simple, true = Detailed
    val isDetailsExpanded: Boolean = false,
    val errorMessage: String? = null,
    val isBackendConnected: Boolean = true,
    val currentFeedback: FeedbackType = FeedbackType.NONE,
    val baseUrl: String = RetrofitClient.getBaseUrl(),
    val coverage: CoverageResponse? = null,
    val isLoadingCoverage: Boolean = false,
    val coverageError: String? = null,
    val exampleQuestions: List<String> = listOf(
        "What does Article 21 of the Indian Constitution protect?",
        "Can police enter my house without a warrant under BNSS?",
        "What is the maximum time police can detain someone without a Magistrate?",
        "Can women be arrested after sunset and before sunrise?",
        "How does a person apply for anticipatory bail under Section 482?",
        "What is the limitation period for filing a consumer complaint under Section 69?"
    ),
    val feedbackSubmissionSuccess: Boolean? = null
)

class LegalChatViewModel(
    private val apiService: ApiService = RetrofitClient.apiService,
    private val historyRepository: LocalHistoryRepository? = null
) : ViewModel() {

    private var currentApiService: ApiService = apiService

    private val _uiState = MutableStateFlow(
        LegalUiState(
            currentScreen = if (historyRepository?.hasAcceptedDisclaimer() == true) AppScreen.HOME else AppScreen.WELCOME,
            baseUrl = historyRepository?.getSavedBaseUrl() ?: RetrofitClient.getBaseUrl()
        )
    )
    val uiState: StateFlow<LegalUiState> = _uiState.asStateFlow()

    val history = historyRepository?.history ?: MutableStateFlow(emptyList())

    init {
        val savedUrl = historyRepository?.getSavedBaseUrl()
        if (!savedUrl.isNullOrBlank()) {
            RetrofitClient.updateBaseUrl(savedUrl)
            currentApiService = RetrofitClient.apiService
        }
        checkHealth()
        loadExampleQuestions()
    }

    fun acceptDisclaimer() {
        historyRepository?.setDisclaimerAccepted(true)
        _uiState.value = _uiState.value.copy(currentScreen = AppScreen.HOME)
    }

    fun navigateTo(screen: AppScreen) {
        _uiState.value = _uiState.value.copy(currentScreen = screen)
        if (screen == AppScreen.COVERAGE && _uiState.value.coverage == null) {
            loadCoverage()
        }
    }

    fun onQueryChange(newQuery: String) {
        _uiState.value = _uiState.value.copy(query = newQuery)
    }

    fun toggleDetailMode(detailed: Boolean) {
        _uiState.value = _uiState.value.copy(isDetailedMode = detailed)
    }

    fun toggleDetailsExpanded() {
        _uiState.value = _uiState.value.copy(isDetailsExpanded = !_uiState.value.isDetailsExpanded)
    }

    fun loadCoverage() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingCoverage = true, coverageError = null)
            try {
                val resp = currentApiService.getCoverage()
                _uiState.value = _uiState.value.copy(
                    coverage = resp,
                    isLoadingCoverage = false
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoadingCoverage = false,
                    coverageError = "Unable to fetch statutory coverage. Tap to retry."
                )
            }
        }
    }

    private fun loadExampleQuestions() {
        viewModelScope.launch {
            try {
                val resp = currentApiService.getExamples()
                if (resp.examples.isNotEmpty()) {
                    _uiState.value = _uiState.value.copy(exampleQuestions = resp.examples)
                }
            } catch (_: Exception) {
                // Keep default examples
            }
        }
    }

    fun updateBaseUrl(url: String): Boolean {
        if (!RetrofitClient.isValidUrl(url)) {
            return false
        }
        RetrofitClient.updateBaseUrl(url)
        historyRepository?.saveBaseUrl(url)
        currentApiService = RetrofitClient.apiService
        _uiState.value = _uiState.value.copy(baseUrl = RetrofitClient.getBaseUrl())
        checkHealth()
        return true
    }

    fun checkHealth() {
        viewModelScope.launch {
            try {
                val resp = currentApiService.healthCheck()
                val isConnected = resp.status.equals("healthy", ignoreCase = true) ||
                        resp.status.equals("ok", ignoreCase = true)
                _uiState.value = _uiState.value.copy(isBackendConnected = isConnected)
            } catch (_: Exception) {
                _uiState.value = _uiState.value.copy(isBackendConnected = false)
            }
        }
    }

    fun askQuestion(customQuestion: String? = null) {
        val q = (customQuestion ?: _uiState.value.query).trim()
        if (q.isBlank()) return

        _uiState.value = _uiState.value.copy(
            query = q,
            isLoading = true,
            errorMessage = null,
            lastFailedQuery = null,
            currentScreen = AppScreen.CHAT,
            currentAnswer = null,
            currentFeedback = FeedbackType.NONE,
            feedbackSubmissionSuccess = null
        )

        viewModelScope.launch {
            try {
                // Build conversation history for follow-ups (max 2 turns)
                val recentHistory = historyRepository?.history?.value?.take(2)?.reversed()?.map {
                    ConversationTurn(
                        question = it.question,
                        answer = it.response.shortAnswer?.simple ?: it.response.shortAnswer?.detailed
                    )
                }

                val req = QuestionRequest(
                    question = q,
                    conversationHistory = recentHistory
                )

                val response = currentApiService.askQuestion(req)

                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    currentAnswer = response,
                    isBackendConnected = true
                )

                // Save to local history
                historyRepository?.addItem(
                    ChatHistoryItem(
                        question = q,
                        response = response
                    )
                )
            } catch (e: RateLimitException) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    lastFailedQuery = q,
                    errorMessage = "Server rate limit reached (HTTP 429). Please wait a moment and tap Retry."
                )
            } catch (e: SocketTimeoutException) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    lastFailedQuery = q,
                    errorMessage = "The legal knowledge server timed out. The server may be waking up from sleep. Tap Retry to try again."
                )
            } catch (e: UnknownHostException) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    lastFailedQuery = q,
                    isBackendConnected = false,
                    errorMessage = "Unable to reach server. Please check your network connection or backend URL in About/Settings."
                )
            } catch (e: ConnectException) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    lastFailedQuery = q,
                    isBackendConnected = false,
                    errorMessage = "Could not connect to backend server. Make sure the backend server is running."
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    lastFailedQuery = q,
                    errorMessage = "An unexpected error occurred: ${e.localizedMessage ?: "Unknown error"}. Tap Retry."
                )
            }
        }
    }

    fun retryLastQuestion() {
        val q = _uiState.value.lastFailedQuery ?: _uiState.value.query
        if (q.isNotBlank()) {
            askQuestion(q)
        }
    }

    fun submitFeedback(rating: FeedbackType, comment: String? = null) {
        val current = _uiState.value.currentAnswer ?: return
        _uiState.value = _uiState.value.copy(currentFeedback = rating)

        val feedbackStr = if (rating == FeedbackType.HELPFUL) "helpful" else "wrong"

        viewModelScope.launch {
            try {
                val req = FeedbackRequest(
                    question = current.question,
                    feedback = feedbackStr,
                    responseStatus = current.status.value,
                    comment = comment?.trim()
                )
                currentApiService.submitFeedback(req)
                _uiState.value = _uiState.value.copy(feedbackSubmissionSuccess = true)

                // Update local repository item
                val currentHistory = historyRepository?.history?.value
                val item = currentHistory?.firstOrNull { it.question == current.question }
                if (item != null) {
                    historyRepository.updateFeedback(item.id, rating)
                }
            } catch (_: Exception) {
                _uiState.value = _uiState.value.copy(feedbackSubmissionSuccess = false)
            }
        }
    }

    fun selectHistoryItem(item: ChatHistoryItem) {
        _uiState.value = _uiState.value.copy(
            query = item.question,
            currentAnswer = item.response,
            currentFeedback = item.feedback,
            currentScreen = AppScreen.CHAT,
            errorMessage = null,
            isLoading = false
        )
    }

    fun clearHistory() {
        historyRepository?.clearHistory()
    }
}
