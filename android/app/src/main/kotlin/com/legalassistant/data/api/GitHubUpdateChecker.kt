package com.legalassistant.data.api

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class UpdateInfo(
    val hasUpdate: Boolean,
    val latestVersion: String,
    val downloadUrl: String?,
    val releaseNotes: String?
)

object GitHubUpdateChecker {
    private const val GITHUB_API_URL = "https://api.github.com/repos/nilesh0002/legal-assistant/releases/latest"

    suspend fun checkForUpdate(currentVersionName: String): UpdateInfo = withContext(Dispatchers.IO) {
        try {
            val url = URL(GITHUB_API_URL)
            val conn = url.openConnection() as HttpURLConnection
            conn.setRequestProperty("User-Agent", "NyayaSahayak-App")
            conn.connectTimeout = 8000
            conn.readTimeout = 8000

            if (conn.responseCode == 200) {
                val jsonStr = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(jsonStr)
                val tagName = json.optString("tag_name", "")
                val cleanTag = tagName.removePrefix("v").trim()
                val cleanCurrent = currentVersionName.removePrefix("v").trim()

                // Find APK download URL in release assets
                var apkUrl: String? = null
                val assets = json.optJSONArray("assets")
                if (assets != null) {
                    for (i in 0 until assets.length()) {
                        val asset = assets.getJSONObject(i)
                        val name = asset.optString("name", "")
                        if (name.endsWith(".apk")) {
                            apkUrl = asset.optString("browser_download_url")
                            break
                        }
                    }
                }
                if (apkUrl == null) {
                    apkUrl = "https://github.com/nilesh0002/legal-assistant/releases/latest"
                }

                val hasUpdate = cleanTag.isNotEmpty() && cleanTag != cleanCurrent
                return@withContext UpdateInfo(
                    hasUpdate = hasUpdate,
                    latestVersion = tagName,
                    downloadUrl = apkUrl,
                    releaseNotes = json.optString("body")
                )
            }
        } catch (_: Exception) {
            // Ignore connection errors and report no update
        }
        return@withContext UpdateInfo(
            hasUpdate = false,
            latestVersion = currentVersionName,
            downloadUrl = null,
            releaseNotes = null
        )
    }
}
