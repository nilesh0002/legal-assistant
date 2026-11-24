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
import com.legalassistant.ui.screens.HomeScreen
import com.legalassistant.ui.theme.LegalAssistantTheme

/**
 * Single-activity app.
 * Screens: Home, Chat, and About/Disclaimer.
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
                    AppScreen.HOME -> HomeScreen(viewModel = viewModel)
                    AppScreen.CHAT -> ChatScreen(viewModel = viewModel)
                    AppScreen.ABOUT -> AboutScreen(viewModel = viewModel)
                }
            }
        }
    }
}
