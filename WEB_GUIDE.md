# NyayaSahayak Web App Guide

The NyayaSahayak web client is a zero-dependency, static ES-module web app (`web/`) built with plain HTML, CSS, and JavaScript. It requires no build step, no third-party CDNs, and no tracking scripts.

---

## 1. Running Locally

### Option A: Served by the FastAPI Backend (Recommended)
The FastAPI backend automatically mounts `web/` at `/`:
```powershell
cd legal-assistant/backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/` in your browser.

### Option B: Standalone Static Server
You can serve `web/` with any static HTTP server (such as Python's `http.server` or `npx serve`):
```powershell
cd legal-assistant/web
python -m http.server 3000
```
Open `http://127.0.0.1:3000/`. By default, `web/js/config.js` detects `localhost` / `127.0.0.1` and points API calls to `http://127.0.0.1:8000`.

---

## 2. Setting the API Base URL

- **Single Configuration File:** Edit `DEFAULT_PRODUCTION_API_URL` in [web/js/config.js](web/js/config.js):
  ```js
  export const DEFAULT_PRODUCTION_API_URL = 'https://legal-assistant-1qgm.onrender.com';
  ```
- **Runtime Override:** Users can also open **About → Backend API configuration** in the UI to test a different backend URL (stored in `localStorage`).
- **HTTPS Enforcement:** Production origins require `https://`. Plain `http://` is permitted only when running against `localhost` or `127.0.0.1`.

---

## 3. Deploying to Vercel

1. Ensure `DEFAULT_PRODUCTION_API_URL` in `web/js/config.js` points to your HTTPS backend (e.g. Render).
2. In Vercel, set the **Root Directory** to `web` (or configure `vercel.json` / CLI from `web/`):
   - **Framework Preset:** Other (Static)
   - **Build Command:** *(leave empty)*
   - **Output Directory:** `.`
3. Deploy via the Vercel dashboard or `vercel --prod` from `legal-assistant/web` (only when you are ready to deploy).

---

## 4. CORS Configuration on the Backend

In `backend/app/main.py` (lines 51–58), FastAPI currently configures `CORSMiddleware` with `allow_origins=["*"]`.

**Do NOT use a wildcard `"*"` in production.** Replace `allow_origins=["*"]` with your exact frontend origins (or load them from an `ALLOWED_ORIGINS` environment variable):

```python
import os

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://legal-assistant-web-rho.vercel.app,http://127.0.0.1:8000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
```

If your Vercel preview or custom domain changes, add that exact `https://...` origin to `ALLOWED_ORIGINS` on Render.
