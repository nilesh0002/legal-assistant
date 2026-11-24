package com.legalassistant.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.legalassistant.data.api.ApiService
import com.legalassistant.data.api.RetrofitClient
import com.legalassistant.data.model.AnswerStatus
import com.legalassistant.data.model.ChatHistoryItem
import com.legalassistant.data.model.FeedbackType
import com.legalassistant.data.model.LegalResponse
import com.legalassistant.data.model.QuestionRequest
import com.legalassistant.data.repository.LocalHistoryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class AppScreen {
    HOME, CHAT, ABOUT
}

data class LegalUiState(
    val currentScreen: AppScreen = AppScreen.HOME,
    val query: String = "",
    val isLoading: Boolean = false,
    val currentAnswer: LegalResponse? = null,
    val isDetailedMode: Boolean = false, // false = Simple, true = Detailed
    val isDetailsExpanded: Boolean = false,
    val errorMessage: String? = null,
    val isBackendConnected: Boolean = true,
    val currentFeedback: FeedbackType = FeedbackType.NONE,
    val baseUrl: String = RetrofitClient.getBaseUrl()
)

class LegalChatViewModel(
    private val apiService: ApiService = RetrofitClient.apiService,
    private val historyRepository: LocalHistoryRepository? = null
) : ViewModel() {

    private var currentApiService: ApiService = apiService

    private val _uiState = MutableStateFlow(LegalUiState())
    val uiState: StateFlow<LegalUiState> = _uiState.asStateFlow()

    val history = historyRepository?.history ?: MutableStateFlow(emptyList())

    init {
        checkHealth()
    }

    fun navigateTo(screen: AppScreen) {
        _uiState.value = _uiState.value.copy(currentScreen = screen)
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

    fun setFeedback(feedback: FeedbackType) {
        _uiState.value = _uiState.value.copy(currentFeedback = feedback)
        val current = _uiState.value.currentAnswer ?: return
        val currentHistory = historyRepository?.history?.value ?: return
        val item = currentHistory.firstOrNull { it.question == current.question }
        if (item != null) {
            historyRepository.updateFeedback(item.id, feedback)
        }
    }

    fun updateBaseUrl(url: String) {
        RetrofitClient.updateBaseUrl(url)
        currentApiService = RetrofitClient.apiService
        _uiState.value = _uiState.value.copy(baseUrl = url)
        checkHealth()
    }

    fun checkHealth() {
        viewModelScope.launch {
            try {
                val resp = currentApiService.healthCheck()
                val isConnected = resp.status.equals("healthy", ignoreCase = true) || resp.status.equals("ok", ignoreCase = true)
                _uiState.value = _uiState.value.copy(isBackendConnected = isConnected)
            } catch (e: Exception) {
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
            currentAnswer = null,
            isDetailsExpanded = false,
            currentFeedback = FeedbackType.NONE,
            currentScreen = AppScreen.CHAT
        )

        viewModelScope.launch {
            try {
                val response = currentApiService.askQuestion(QuestionRequest(question = q))
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    currentAnswer = response,
                    errorMessage = null
                )
                // Persist to local history
                historyRepository?.addItem(
                    ChatHistoryItem(
                        question = q,
                        response = response,
                        feedback = FeedbackType.NONE
                    )
                )
            } catch (e: Exception) {
                val errorResp = LegalResponse(
                    status = AnswerStatus.ERROR,
                    question = q,
                    keyPoints = listOf("Unable to connect to legal knowledge service. ${e.localizedMessage ?: "Check network connection."}"),
                    disclaimer = "General information, not legal advice."
                )
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    currentAnswer = errorResp,
                    errorMessage = e.localizedMessage ?: "Network error"
                )
            }
        }
    }

    fun loadFromHistory(item: ChatHistoryItem) {
        _uiState.value = _uiState.value.copy(
            query = item.question,
            currentAnswer = item.response,
            currentFeedback = item.feedback,
            isDetailedMode = false,
            isDetailsExpanded = false,
            errorMessage = null,
            currentScreen = AppScreen.CHAT
        )
    }

    fun clearHistory() {
        historyRepository?.clearHistory()
    }
}
