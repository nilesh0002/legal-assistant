# NyayaSahayak Android APK Guide

This guide explains how to install, configure, test, and build the NyayaSahayak Android application (`com.legalassistant`).

---

## 1. Difference Between APK and AAB

1. **APK (Android Package)** is an installable binary package containing compiled dex code, assets, and resources that can be directly transferred and installed on any Android device.
2. **AAB (Android App Bundle)** is a publishing archive format uploaded to Google Play that contains modular code and resources from which Google Play dynamically generates device-specific split APKs tailored to each user's screen density and CPU architecture.
3. **Key distinction:** You can directly sideload and run an APK on a physical phone or emulator via `adb install`, whereas an AAB cannot be directly installed on an Android device without first converting it using Google Play or Google's `bundletool` utility.

---

## 2. Installing the APK on a Physical Android Phone

### Location of the Debug APK
```
legal-assistant/android/app/build/outputs/apk/debug/app-debug.apk
```
**File Size:** ~16.5 MB

### Method A: Direct USB Installation via ADB
1. Enable **Developer Options** and **USB Debugging** on your Android phone (Settings → About Phone → tap "Build Number" 7 times → Developer Options → USB Debugging).
2. Connect your phone to your computer with a USB cable and authorize the computer prompt.
3. Open a terminal in `legal-assistant/android` and run:
   ```cmd
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

### Method B: Sideloading via File Transfer / Google Drive
1. Transfer `app-debug.apk` to your phone via USB cable, WhatsApp, Telegram, or Google Drive.
2. Open your phone's File Manager and tap `app-debug.apk`.
3. When prompted by Android, grant permission to **Install Unknown Apps** for your file manager.
4. Tap **Install** and open **NyayaSahayak**.

---

## 3. Pointing the App to a Backend

The app features a built-in **Base URL Configuration** screen in **Settings (Gear Icon in Top App Bar)**, allowing you to switch between local development and cloud endpoints without rebuilding.

### Scenario A: Connecting to the Production Cloud Backend
1. Open the app and tap the **Settings icon** in the top-right corner.
2. In the **Base URL** field, enter:
   ```
   https://legal-assistant-1qgm.onrender.com/
   ```
3. Tap **Save URL**, then tap **Ping Health** to verify the connection turns green (**Connected / Live**).

### Scenario B: Connecting to a Local Backend from a Physical Phone (Same Wi-Fi)
1. Ensure your computer and phone are connected to the same Wi-Fi network.
2. Start the FastAPI backend bound to `0.0.0.0` (all network interfaces):
   ```powershell
   cd legal-assistant/backend
   .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. Find your computer's local IP address using `ipconfig` (e.g. `192.168.1.105`).
4. On your phone, open NyayaSahayak → Settings → enter:
   ```
   http://192.168.1.105:8000/
   ```
5. Tap **Save URL**. Cleartext HTTP is explicitly permitted in the debug build via `network_security_config.xml`.

### Scenario C: Connecting from an Android Emulator
When running inside the Android SDK Emulator, the host machine's `localhost` is accessible at `10.0.2.2`:
1. Start the backend locally:
   ```powershell
   cd legal-assistant/backend
   .venv\Scripts\python -m uvicorn app.main:app --port 8000
   ```
2. The debug build defaults to `http://10.0.2.2:8000/` automatically.

---

## 4. Running on an Android Emulator

1. Open Android Studio → **Device Manager** (or run `emulator -avd <Your_AVD_Name>`).
2. Once the virtual device boots, run:
   ```cmd
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```
3. Launch **NyayaSahayak** from the app launcher.

---

## 5. Creating a Signed Release Build (Keystore)

> **CRITICAL SECURITY RULE:** The signing keystore file (`*.jks`, `*.keystore`) and its passwords must **NEVER** be committed to Git. They are explicitly added to `.gitignore`.

### Step 1: Generate a Release Keystore
Run `keytool` from your JDK's `bin` directory:
```cmd
keytool -genkey -v -keystore release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias nyayasahayak-release
```
Enter a secure keystore password and answer the organizational unit prompts. Save `release-key.jks` in a secure location outside the repository (or inside `android/` where it is git-ignored).

### Step 2: Configure Signing in `local.properties` (Untracked)
Add the following to `legal-assistant/android/local.properties` (which is git-ignored):
```properties
release.keystore.file=C:/path/to/release-key.jks
release.keystore.password=YourKeystorePassword
release.key.alias=nyayasahayak-release
release.key.password=YourKeyPassword
release.base.url=https://legal-assistant-1qgm.onrender.com/
```

### Step 3: Build the Release APK or Bundle
Run:
```cmd
cd legal-assistant/android
gradlew.bat assembleRelease
```
Or for Google Play Store upload:
```cmd
gradlew.bat bundleRelease
```
The output will be placed in:
- APK: `app/build/outputs/apk/release/app-release-unsigned.apk` (or signed if configured).
- AAB: `app/build/outputs/bundle/release/app-release.aab`.

Note: Release builds enforce strict HTTPS and disable cleartext traffic in `src/main/res/xml/network_security_config.xml`.
