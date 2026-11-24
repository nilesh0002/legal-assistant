package com.legalassistant.data.api

/**
 * Maps the JSON returned by GET /health.
 */
data class HealthResponse(
    val status: String,
    val service: String,
    val version: String,
    val timestamp: String,
)
