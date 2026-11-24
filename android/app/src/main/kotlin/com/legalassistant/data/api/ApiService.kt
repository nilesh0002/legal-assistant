package com.legalassistant.data.api

import com.legalassistant.data.model.LegalResponse
import com.legalassistant.data.model.QuestionRequest
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/**
 * Retrofit interface for the Legal Assistant backend API.
 */
interface ApiService {

    @GET("/health")
    suspend fun healthCheck(): HealthResponse

    @POST("/ask")
    suspend fun askQuestion(@Body request: QuestionRequest): LegalResponse
}
