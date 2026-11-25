package com.legalassistant

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import com.legalassistant.data.repository.LocalHistoryRepository
import com.legalassistant.ui.AppScreen
import com.legalassistant.ui.LegalChatViewModel
import com.legalassistant.ui.screens.AboutScreen
import com.legalassistant.ui.screens.ChatScreen
import com.legalassistant.ui.screens.CoverageScreen
import com.legalassistant.ui.screens.HistoryScreen
import com.legalassistant.ui.screens.HomeScreen
import com.legalassistant.ui.screens.WelcomeScreen
import com.legalassistant.ui.theme.LegalAssistantTheme

/**
 * Single-activity app implementing Stitch civic design system.
 * Screens: Welcome (first launch only), Home, Chat, History, Coverage, About/Settings.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val historyRepository = LocalHistoryRepository(applicationContext)

        setContent {
            LegalAssistantTheme {
                val viewModel: LegalChatViewModel = viewModel(
                    factory = object : androidx.lifecycle.ViewModelProvider.Factory {
                        @Suppress("UNCHECKED_CAST")
                        override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                            return LegalChatViewModel(historyRepository = historyRepository) as T
                        }
                    }
                )

                val uiState by viewModel.uiState.collectAsState()

                when (uiState.currentScreen) {
                    AppScreen.WELCOME -> WelcomeScreen(onAccept = { viewModel.acceptDisclaimer() })
                    AppScreen.HOME -> HomeScreen(viewModel = viewModel)
                    AppScreen.CHAT -> ChatScreen(viewModel = viewModel)
                    AppScreen.HISTORY -> HistoryScreen(viewModel = viewModel)
                    AppScreen.COVERAGE -> CoverageScreen(viewModel = viewModel)
                    AppScreen.ABOUT -> AboutScreen(viewModel = viewModel)
                }
            }
        }
    }
}
