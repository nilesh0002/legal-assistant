package com.legalassistant

import com.legalassistant.data.api.ApiService
import com.legalassistant.data.api.HealthResponse
import com.legalassistant.data.model.*
import com.legalassistant.ui.AppScreen
import com.legalassistant.ui.LegalChatViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class LegalChatViewModelTest {

    private val testDispatcher = StandardTestDispatcher()

    private val fakeApiService = object : ApiService {
        override suspend fun healthCheck(): HealthResponse {
            return HealthResponse(status = "ok", service = "legal-assistant", version = "0.1.0", timestamp = "2026-11-24T10:00:00Z")
        }

        override suspend fun askQuestion(request: QuestionRequest): LegalResponse {
            return LegalResponse(
                status = AnswerStatus.ANSWERED,
                question = request.question,
                shortAnswer = ShortAnswer(
                    simple = "Under Article 21, life and liberty are protected.",
                    detailed = "According to Article 21, no person shall be deprived of his life."
                ),
                keyPoints = listOf("Protects life and personal liberty"),
                details = listOf(
                    SourceDetail(
                        claim = "Article 21 provides protection",
                        law = "Constitution of India",
                        section = "Article 21",
                        quote = "No person shall be deprived of his life",
                        sourceId = "constitution-india",
                        sourceTitle = "Article 21",
                        sourceUrl = "https://example.com",
                        location = "Part III, Article 21"
                    )
                ),
                lastVerified = "2026-11-22",
                disclaimer = "General information, not legal advice."
            )
        }
    }

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testInitialState() = runTest {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(AppScreen.HOME, state.currentScreen)
        assertEquals("", state.query)
        assertFalse(state.isDetailedMode)
        assertFalse(state.isDetailsExpanded)
        assertTrue(state.isBackendConnected)
    }

    @Test
    fun testNavigation() {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)

        viewModel.navigateTo(AppScreen.CHAT)
        assertEquals(AppScreen.CHAT, viewModel.uiState.value.currentScreen)

        viewModel.navigateTo(AppScreen.ABOUT)
        assertEquals(AppScreen.ABOUT, viewModel.uiState.value.currentScreen)

        viewModel.navigateTo(AppScreen.HOME)
        assertEquals(AppScreen.HOME, viewModel.uiState.value.currentScreen)
    }

    @Test
    fun testToggleDetailMode() {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)

        assertFalse(viewModel.uiState.value.isDetailedMode)

        viewModel.toggleDetailMode(true)
        assertTrue(viewModel.uiState.value.isDetailedMode)

        viewModel.toggleDetailMode(false)
        assertFalse(viewModel.uiState.value.isDetailedMode)
    }

    @Test
    fun testToggleDetailsAccordion() {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)

        assertFalse(viewModel.uiState.value.isDetailsExpanded)

        viewModel.toggleDetailsExpanded()
        assertTrue(viewModel.uiState.value.isDetailsExpanded)

        viewModel.toggleDetailsExpanded()
        assertFalse(viewModel.uiState.value.isDetailsExpanded)
    }

    @Test
    fun testAskQuestionSuccess() = runTest {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.onQueryChange("What is Article 21?")
        viewModel.askQuestion()

        // Advances coroutine execution
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(AppScreen.CHAT, state.currentScreen)
        assertFalse(state.isLoading)
        assertNotNull(state.currentAnswer)
        assertEquals(AnswerStatus.ANSWERED, state.currentAnswer!!.status)
        assertEquals("Article 21", state.currentAnswer!!.details[0].section)
        assertEquals("2026-11-22", state.currentAnswer!!.lastVerified)
    }

    @Test
    fun testFeedbackUpdate() {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)

        assertEquals(FeedbackType.NONE, viewModel.uiState.value.currentFeedback)

        viewModel.setFeedback(FeedbackType.HELPFUL)
        assertEquals(FeedbackType.HELPFUL, viewModel.uiState.value.currentFeedback)

        viewModel.setFeedback(FeedbackType.WRONG)
        assertEquals(FeedbackType.WRONG, viewModel.uiState.value.currentFeedback)
    }
}
