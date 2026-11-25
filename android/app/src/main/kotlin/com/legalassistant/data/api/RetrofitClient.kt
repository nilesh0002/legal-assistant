package com.legalassistant.data.api

import com.legalassistant.BuildConfig
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

class RateLimitException(message: String = "Server rate limit reached (HTTP 429). Please wait a few seconds and tap Retry.") : IOException(message)

/**
 * Singleton Retrofit client with dynamic base URL configuration and error interception.
 */
object RetrofitClient {

    private fun ensureTrailingSlash(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    private var currentBaseUrl: String = ensureTrailingSlash(BuildConfig.BASE_URL)

    private val rateLimitInterceptor = Interceptor { chain ->
        val request = chain.request()
        val response: Response = chain.proceed(request)
        if (response.code == 429) {
            throw RateLimitException()
        }
        response
    }

    private val okHttpClient: OkHttpClient by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        OkHttpClient.Builder()
            .addInterceptor(rateLimitInterceptor)
            .addInterceptor(logging)
            .connectTimeout(45, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(45, TimeUnit.SECONDS)
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

    fun isValidUrl(url: String, requireHttps: Boolean = BuildConfig.REQUIRE_HTTPS): Boolean {
        val trimmed = url.trim().lowercase()
        if (requireHttps) {
            return trimmed.startsWith("https://")
        }
        return trimmed.startsWith("http://") || trimmed.startsWith("https://")
    }

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
