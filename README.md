# Indian Legal Knowledge Assistant

A RAG-based chatbot that answers questions about Indian law using **only
approved, verified sources**. Every answer is grounded in retrieved passages,
validated by code, and shows its sources.

> **General information, not legal advice.**

## Architecture

```
+----------------+     HTTP/JSON     +----------------------------------+
|  Android App   | <===============> |  Python Backend (FastAPI)        |
|  Kotlin +      |                   |                                  |
|  Compose +     |                   |  /health  - service status       |
|  Material 3    |                   |  /search  - hybrid retrieval     |
|                |                   |  /ask     - RAG Q&A pipeline     |
+----------------+                   |                                  |
                                     |  Pipeline:                       |
                                     |  Question -> Retrieve -> Generate|
                                     |          -> Validate -> Respond  |
                                     |                                  |
                                     |  Vector DB: Chroma (local)       |
                                     |  Embeddings: BGE-small-en-v1.5   |
                                     |  LLM: Gemini (free) / Ollama     |
                                     +----------------------------------+
```

## Project Structure

```
legal-assistant/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route definitions
│   │   ├── models/       # Pydantic request/response schemas
│   │   ├── retrieval/    # Vector + BM25 hybrid search (interface + impl)
│   │   ├── generation/   # LLM wrapper (interface + impl)
│   │   └── validation/   # Citation & quote validator (interface + impl)
│   ├── pipeline/         # Document ingestion scripts
│   ├── data/
│   │   ├── raw/          # Downloaded source documents
│   │   ├── processed/    # Parsed & chunked documents
│   │   ├── mappings/     # Old law -> new law mapping tables
│   │   └── sources.yaml  # Approved source registry
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── android/              # Kotlin + Jetpack Compose app
├── eval/                 # Golden test questions & eval scripts
│   └── questions.yaml
└── README.md
```

## 🌐 Live Web App

Try NyayaSahayak directly in your browser:

➡️ **[Open NyayaSahayak Web App](https://legal-assistant-web-rho.vercel.app/)**

---

## 📱 Download Android APK

You can download the pre-compiled Android APK directly from GitHub Releases:

➡️ **[Download Latest Android APK (app-debug.apk)](https://github.com/nilesh0002/legal-assistant/releases/latest/download/app-debug.apk)**

*Or visit the [GitHub Releases](https://github.com/nilesh0002/legal-assistant/releases) page to choose a specific version or download build artifacts from GitHub Actions.*

### How to Install on Android
1. Download `app-debug.apk` directly to your Android device using Chrome or your browser.
2. When prompted by Android security, tap **Settings** and allow **Install Unknown Apps** for your browser / file manager.
3. Tap **Install** and launch **NyayaSahayak**.
4. In the app's **About / Settings** tab, you can configure the backend URL (default is `http://10.0.2.2:8000` for Android Studio emulator, or your computer's local Wi-Fi IP such as `http://192.168.x.x:8000` for physical devices).

---

### Backend

```bash
cd legal-assistant/backend
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/health — you should see:

```json
{"status": "healthy", "service": "Indian Legal Knowledge Assistant", "version": "0.1.0", "timestamp": "..."}
```

### Run Tests

```bash
cd legal-assistant/backend
# Activate venv first, then:
pytest tests/ -v
```

### Android

1. Open the `android/` folder in Android Studio.
2. Sync Gradle.
3. Run on an emulator (the app connects to `10.0.2.2:8000` by default,
   which maps to the host machine's `localhost`).
4. The home screen should show "Connected to backend" if the FastAPI
   server is running.

## Decisions & Assumptions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Language | English only for v1 (Hindi-ready embedding model chosen) |
| 2 | LLM | Google Gemini free tier (Ollama fallback) |
| 3 | Embeddings | BAAI/bge-small-en-v1.5 (multilingual upgrade path: bge-m3) |
| 4 | Vector DB | Chroma (local, no server needed) |
| 5 | Search | Hybrid: vector similarity + BM25 keyword search |
| 6 | Android min SDK | 26 (Android 8.0, covers ~95% of devices) |
| 7 | Auth | None in v1 (chat history device-only) |
| 8 | Hosting | Local development; free cloud at beta (M9) |

### Assumptions

These choices were made to keep moving. Flag if you disagree:

1. **Constitution text** will be manually downloaded from the official
   Legislative Department website and stored in `data/raw/`.
   We will not scrape; we will download the official PDF/HTML.

2. **Judgment texts** will use headnotes + ratio decidendi paragraphs,
   not full 300-page judgments, to stay within embedding/context limits.

3. **Embedding model** `bge-small-en-v1.5` is chosen for speed and
   free local inference. The BGE family has a multilingual variant
   (`bge-m3`) for the Hindi upgrade path.

4. **Section number mappings** (CrPC->BNSS, IPC->BNS) are stored as
   YAML files that must be **human-verified** before the system cites them.
   Each entry has a `status: verified | pending` field.

5. **Free-tier limits**: Gemini free tier has limited requests/minute.
   The app shows a graceful error if rate-limited, not a crash.
   Verify current limits at https://ai.google.dev/pricing.

6. **10.0.2.2** is used as the backend URL in the Android emulator.
   For physical device testing, change `BASE_URL` in `app/build.gradle.kts`.

## Assumptions

1. **Official Sources Only**: All non-official and third-party sources (`indian-kanoon`, `prs-india`, `livelaw`, `bar-and-bench`) and live web retrieval tools (`web_search.py`, `WebLegalRetriever`) have been strictly purged from `sources.yaml` and backend code.
2. **Network Isolation**: The `/ask` retrieval, thresholding, and validation pipeline runs 100% offline without network calls. Only external LLM calls (e.g. Gemini) are allowed network access.
3. **Deterministic Cross-Feature Reranking**: Replaced external heavy ONNX model downloads with an offline cross-encoder reranker combining vector similarity, BM25 signals, title precision/recall (F1), exact phrase matching, and multi-query agreement.
4. **Calibrated Evidence Gating**: Replaced brittle vector cutoffs with a two-gate calibrated threshold: high semantic vector score (>= 0.67) or solid semantic score (>= 0.64) combined with multi-query agreement (>= 2) and high rerank score (>= 0.67). Uncovered legal topics reliably return `insufficient_evidence`.
5. **Conversational Memory**: Follow-up questions resolve conversational references (last 2 turns) strictly in-memory per request body with no server-side user data retention.
6. **Statutory Coverage**: BNSS 2023 corpus expanded to 46 key sections covering arrest procedure, rights of arrested persons, summons/warrants, search/seizure, remand custody limits, and bail.

## Milestones

| M# | Name | Status |
|----|------|--------|
| M0 | Project setup, /health, empty Compose app | Done |
| M1 | Source corpus: collect & parse Part III | Done |
| M1b| Expand corpus: DPSP, Fundamental Duties & BNSS 2023 | Done |
| M2 | Indexing: chunk, embed, index into Chroma | Done |
| M3 | /search endpoint with hybrid retrieval | Done |
| M4 | /ask endpoint: LLM + citations in JSON | Done |
| M5 | Validators + adversarial tests | Done |
| M6 | Android chat UI (Compose + Material 3, two-layer answers, local history) | Done |
| M7 | Old/new law mapping in answers | Next |
| M8 | Evaluation: 50+ golden questions + report | Pending |
| M9 | Beta: cloud deployment, production release | Pending |

## Non-Negotiable Rules

1. **Source accuracy over fluency** — always.
2. **RAG only** — LLM answers from retrieved passages, never from memory.
3. **Code-enforced validation** — every quote, source ID, and case name
   is checked programmatically before the answer reaches the user.
4. **Refuse rather than guess** — `insufficient_evidence` is better than
   a wrong answer.
5. **No legal text from memory** — everything traces to `sources.yaml`.
6. **Disclaimer on every answer** — "General information, not legal advice."
7. **Swappable components** — LLM, embeddings, and vector DB are behind
   abstract interfaces.
