package com.legalassistant

import com.legalassistant.data.api.ApiService
import com.legalassistant.data.api.HealthResponse
import com.legalassistant.data.api.RateLimitException
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
import java.net.SocketTimeoutException
import java.net.UnknownHostException

@OptIn(ExperimentalCoroutinesApi::class)
class LegalChatViewModelTest {

    private val testDispatcher = StandardTestDispatcher()

    private var shouldThrowRateLimit = false
    private var shouldThrowTimeout = false
    private var shouldThrowOffline = false

    private val fakeApiService = object : ApiService {
        override suspend fun healthCheck(): HealthResponse {
            return HealthResponse(
                status = "healthy",
                service = "Indian Legal Knowledge Assistant",
                version = "0.1.0",
                timestamp = "2026-11-25T10:00:00Z"
            )
        }

        override suspend fun askQuestion(request: QuestionRequest): LegalResponse {
            if (shouldThrowRateLimit) throw RateLimitException()
            if (shouldThrowTimeout) throw SocketTimeoutException("Connection timed out")
            if (shouldThrowOffline) throw UnknownHostException("No address associated with hostname")

            return LegalResponse(
                status = AnswerStatus.ANSWERED,
                question = request.question,
                shortAnswer = ShortAnswer(
                    simple = "Under Article 21, life and personal liberty are protected.",
                    detailed = "According to Article 21 of the Constitution of India, no person shall be deprived of his life or personal liberty except according to procedure established by law."
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
                        sourceUrl = "https://legislative.gov.in",
                        location = "Part III, Article 21"
                    )
                ),
                lastVerified = "2026-11-22",
                disclaimer = "General information, not legal advice."
            )
        }

        override suspend fun getCoverage(): CoverageResponse {
            return CoverageResponse(
                note = "Selected sections only",
                totalChunks = 186,
                laws = listOf(
                    LawCoverage(
                        law = "Constitution of India",
                        sourceId = "constitution-india",
                        coverageNote = "Selected sections only",
                        lastVerified = "2026-11-22",
                        sections = listOf(
                            SectionInfo(section = "Article 21", title = "Article 21: Protection of life")
                        )
                    )
                )
            )
        }

        override suspend fun getExamples(): ExamplesResponse {
            return ExamplesResponse(
                examples = listOf(
                    "What does Article 21 protect?",
                    "When can police arrest without warrant?"
                )
            )
        }

        override suspend fun submitFeedback(request: FeedbackRequest): FeedbackResponse {
            return FeedbackResponse(status = "received", message = "Feedback recorded")
        }
    }

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        shouldThrowRateLimit = false
        shouldThrowTimeout = false
        shouldThrowOffline = false
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testInitialStateAndDisclaimer() = runTest {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(AppScreen.WELCOME, state.currentScreen)
        assertEquals("", state.query)
        assertFalse(state.isDetailedMode)
        assertFalse(state.isDetailsExpanded)
        assertTrue(state.isBackendConnected)

        // Accept disclaimer -> navigates to Home
        viewModel.acceptDisclaimer()
        assertEquals(AppScreen.HOME, viewModel.uiState.value.currentScreen)
    }

    @Test
    fun testNavigationAcrossAllScreens() {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)

        viewModel.navigateTo(AppScreen.HOME)
        assertEquals(AppScreen.HOME, viewModel.uiState.value.currentScreen)

        viewModel.navigateTo(AppScreen.CHAT)
        assertEquals(AppScreen.CHAT, viewModel.uiState.value.currentScreen)

        viewModel.navigateTo(AppScreen.HISTORY)
        assertEquals(AppScreen.HISTORY, viewModel.uiState.value.currentScreen)

        viewModel.navigateTo(AppScreen.COVERAGE)
        assertEquals(AppScreen.COVERAGE, viewModel.uiState.value.currentScreen)

        viewModel.navigateTo(AppScreen.ABOUT)
        assertEquals(AppScreen.ABOUT, viewModel.uiState.value.currentScreen)
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
    fun testRateLimit429Handling() = runTest {
        shouldThrowRateLimit = true
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.askQuestion("Rate limit test query")
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNull(state.currentAnswer)
        assertNotNull(state.errorMessage)
        assertTrue(state.errorMessage!!.contains("429"))
        assertEquals("Rate limit test query", state.lastFailedQuery)
    }

    @Test
    fun testTimeoutHandling() = runTest {
        shouldThrowTimeout = true
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.askQuestion("Timeout test query")
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNull(state.currentAnswer)
        assertNotNull(state.errorMessage)
        assertTrue(state.errorMessage!!.contains("timed out", ignoreCase = true))
    }

    @Test
    fun testOfflineHandling() = runTest {
        shouldThrowOffline = true
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.askQuestion("Offline test query")
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertFalse(state.isBackendConnected)
        assertNotNull(state.errorMessage)
        assertTrue(state.errorMessage!!.contains("network connection", ignoreCase = true))
    }

    @Test
    fun testRetryLastQuestion() = runTest {
        shouldThrowTimeout = true
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.askQuestion("Retry query")
        testDispatcher.scheduler.advanceUntilIdle()

        assertTrue(viewModel.uiState.value.errorMessage != null)

        // Now backend recovers
        shouldThrowTimeout = false
        viewModel.retryLastQuestion()
        testDispatcher.scheduler.advanceUntilIdle()

        val state = viewModel.uiState.value
        assertNull(state.errorMessage)
        assertNotNull(state.currentAnswer)
        assertEquals(AnswerStatus.ANSWERED, state.currentAnswer!!.status)
    }

    @Test
    fun testSubmitFeedback() = runTest {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.askQuestion("Feedback test")
        testDispatcher.scheduler.advanceUntilIdle()

        viewModel.submitFeedback(FeedbackType.HELPFUL, "Very clear summary")
        testDispatcher.scheduler.advanceUntilIdle()

        assertEquals(FeedbackType.HELPFUL, viewModel.uiState.value.currentFeedback)
        assertEquals(true, viewModel.uiState.value.feedbackSubmissionSuccess)
    }

    @Test
    fun testLoadCoverage() = runTest {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)
        viewModel.loadCoverage()
        testDispatcher.scheduler.advanceUntilIdle()

        val coverage = viewModel.uiState.value.coverage
        assertNotNull(coverage)
        assertEquals(186, coverage!!.totalChunks)
        assertEquals(1, coverage.laws.size)
    }

    @Test
    fun testUpdateBaseUrl() {
        val viewModel = LegalChatViewModel(apiService = fakeApiService, historyRepository = null)

        val successHttp = viewModel.updateBaseUrl("http://192.168.1.100:8000")
        assertTrue(successHttp)
        assertEquals("http://192.168.1.100:8000/", viewModel.uiState.value.baseUrl)

        val invalid = viewModel.updateBaseUrl("ftp://badurl")
        assertFalse(invalid)
    }
}
