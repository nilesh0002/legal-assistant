# NyayaSahayak Android Signed Release Guide

This guide explains how to generate a private release signing keystore, keep it strictly out of version control, back it up safely, and build a signed APK or AAB.

> **WARNING:** Never commit a keystore file (`*.jks`, `*.keystore`) or signing passwords to Git. If you lose your release keystore or its passwords, you **cannot** publish updates to an existing Google Play listing.

---

## 1. Create a Release Keystore

Run `keytool` (included with JDK 17/21) **outside** or in a git-ignored location:

```cmd
keytool -genkeypair -v ^
  -keystore nyayasahayak-release.jks ^
  -keyalg RSA -keysize 2048 -validity 10000 ^
  -alias nyayasahayak-key
```

You will be prompted for:
- Keystore password (choose a strong, unique password)
- Key password
- Name, organization, city, state, and country code (`IN`)

---

## 2. Keep It Out of Git & Back It Up

1. **Verify `.gitignore`:** The repository `.gitignore` already excludes `*.jks`, `*.keystore`, `*keystore.properties`, `release.properties`, `*.apk`, and `*.aab`. Double-check with `git status` before committing anything.
2. **Back Up Immediately:** Store an encrypted copy of `nyayasahayak-release.jks` and its passwords in at least **two** secure locations (e.g. a password manager such as Bitwarden/1Password + an encrypted offline USB/cloud vault).

---

## 3. Configure Release Signing Locally

Add the following untracked properties to `android/local.properties` (already git-ignored):

```properties
release.base.url=https://legal-assistant-1qgm.onrender.com/
release.keystore.file=C:/secure-keys/nyayasahayak-release.jks
release.keystore.password=YOUR_KEYSTORE_PASSWORD
release.key.alias=nyayasahayak-key
release.key.password=YOUR_KEY_PASSWORD
```

And in `android/app/build.gradle.kts`, wire a `signingConfigs { create("release") { ... } }` block that reads those `local.properties` values only when present (never hardcode passwords in `build.gradle.kts`).

---

## 4. Build the Signed Release APK and AAB

- **Release builds require HTTPS:** `REQUIRE_HTTPS` is `true` in `release` and cleartext HTTP is disabled by `src/main/res/xml/network_security_config.xml`.

From `legal-assistant/android`:

```cmd
:: Build signed Release AAB (required for Google Play Store)
gradlew.bat bundleRelease

:: Build signed Release APK (for direct distribution)
gradlew.bat assembleRelease
```

Outputs:
- **AAB:** `android/app/build/outputs/bundle/release/app-release.aab`
- **APK:** `android/app/build/outputs/apk/release/app-release.apk`
