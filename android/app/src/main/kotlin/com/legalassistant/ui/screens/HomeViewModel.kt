package com.legalassistant.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.legalassistant.data.api.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

/**
 * Sealed interface for the health-check UI states.
 */
sealed interface HealthUiState {
    data object Loading : HealthUiState
    data class Connected(val version: String) : HealthUiState
    data class Error(val message: String) : HealthUiState
}

/**
 * ViewModel for the Home screen.
 *
 * On init, calls GET /health to verify the backend is reachable.
 */
class HomeViewModel : ViewModel() {

    private val _uiState = MutableStateFlow<HealthUiState>(HealthUiState.Loading)
    val uiState: StateFlow<HealthUiState> = _uiState

    init {
        checkHealth()
    }

    fun checkHealth() {
        _uiState.value = HealthUiState.Loading
        viewModelScope.launch {
            try {
                val response = RetrofitClient.apiService.healthCheck()
                if (response.status == "healthy") {
                    _uiState.value = HealthUiState.Connected(version = response.version)
                } else {
                    _uiState.value = HealthUiState.Error("Unexpected status: ${response.status}")
                }
            } catch (e: Exception) {
                _uiState.value = HealthUiState.Error(
                    e.localizedMessage ?: "Unknown error"
                )
            }
        }
    }
}
