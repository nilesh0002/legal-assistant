package com.legalassistant.data.api

import com.legalassistant.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Singleton Retrofit client with dynamic base URL configuration.
 */
object RetrofitClient {

    private fun ensureTrailingSlash(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    private var currentBaseUrl: String = ensureTrailingSlash(BuildConfig.BASE_URL)

    private val okHttpClient: OkHttpClient by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        OkHttpClient.Builder()
            .addInterceptor(logging)
            // 60-second timeouts to allow Render.com free tier cold starts
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }

    private var _apiService: ApiService? = null

    val apiService: ApiService
        get() {
            if (_apiService == null) {
                _apiService = createService(currentBaseUrl)
            }
            return _apiService!!
        }

    fun updateBaseUrl(newUrl: String) {
        val formatted = ensureTrailingSlash(newUrl)
        currentBaseUrl = formatted
        _apiService = createService(formatted)
    }

    fun getBaseUrl(): String = currentBaseUrl

    private fun createService(url: String): ApiService {
        val safeUrl = ensureTrailingSlash(url)
        return Retrofit.Builder()
            .baseUrl(safeUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
