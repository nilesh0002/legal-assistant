package com.legalassistant.data.repository

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.legalassistant.data.model.ChatHistoryItem
import com.legalassistant.data.model.FeedbackType
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Repository for storing and retrieving user chat sessions and app preferences locally on-device.
 * Zero telemetry, zero accounts, completely private.
 */
class LocalHistoryRepository(context: Context) {

    private val prefs = context.getSharedPreferences("legal_assistant_prefs", Context.MODE_PRIVATE)
    private val gson = Gson()

    private val _history = MutableStateFlow<List<ChatHistoryItem>>(emptyList())
    val history: StateFlow<List<ChatHistoryItem>> = _history.asStateFlow()

    init {
        loadHistory()
    }

    fun hasAcceptedDisclaimer(): Boolean {
        return prefs.getBoolean("has_accepted_disclaimer", false)
    }

    fun setDisclaimerAccepted(accepted: Boolean) {
        prefs.edit().putBoolean("has_accepted_disclaimer", accepted).apply()
    }

    fun getSavedBaseUrl(): String? {
        return prefs.getString("custom_base_url", null)
    }

    fun saveBaseUrl(url: String) {
        prefs.edit().putString("custom_base_url", url).apply()
    }

    private fun loadHistory() {
        val json = prefs.getString("history_items", null)
        if (!json.isNullOrBlank()) {
            try {
                val type = object : TypeToken<List<ChatHistoryItem>>() {}.type
                val items: List<ChatHistoryItem> = gson.fromJson(json, type)
                _history.value = items
            } catch (e: Exception) {
                _history.value = emptyList()
            }
        }
    }

    private fun saveHistory(items: List<ChatHistoryItem>) {
        val json = gson.toJson(items)
        prefs.edit().putString("history_items", json).apply()
        _history.value = items
    }

    fun addItem(item: ChatHistoryItem) {
        val current = _history.value.toMutableList()
        current.add(0, item) // newest first
        saveHistory(current)
    }

    fun updateFeedback(itemId: String, feedback: FeedbackType) {
        val current = _history.value.toMutableList()
        val index = current.indexOfFirst { it.id == itemId }
        if (index != -1) {
            val item = current[index]
            current[index] = item.copy(feedback = feedback)
            saveHistory(current)
        }
    }

    fun clearHistory() {
        prefs.edit().remove("history_items").apply()
        _history.value = emptyList()
    }
}
