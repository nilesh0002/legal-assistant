package com.legalassistant.data.api

import com.legalassistant.data.model.CoverageResponse
import com.legalassistant.data.model.ExamplesResponse
import com.legalassistant.data.model.FeedbackRequest
import com.legalassistant.data.model.FeedbackResponse
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

    @GET("/coverage")
    suspend fun getCoverage(): CoverageResponse

    @GET("/examples")
    suspend fun getExamples(): ExamplesResponse

    @POST("/feedback")
    suspend fun submitFeedback(@Body request: FeedbackRequest): FeedbackResponse
}
