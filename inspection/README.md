# Viral Claim Radar (Project Documentation)

Viral Claim Radar is a fact-checking application with a FastAPI backend and a static HTML frontend.
It accepts three input types:
- Text claim
- Image upload (OCR with pytesseract)
- URL link (web page text extraction)

The backend returns a normalized JSON verdict:

```json
{
  "status": "Supported | Refuted | Uncertain",
  "confidence": 0,
  "summary": "short explanation"
}
```

## Repository Structure

```text
backend/
  bug1/
    .env
    main.py
    rag.py
    ingest.py
    utils.py
    multi_ai_fallback.py
    convert_data.py
    requirements.txt
    data.txt
    train.tsv
    valid.tsv
    test.tsv
    data/
      data.txt
    faiss_index/
      index.faiss
      index.pkl (created/used by ingest flow)
frontend/
  fe/
    fe.html
    IMG_3629.png
    IMG_3632.png
    IMG_3633.png
    IMG_3635.png
requirements.txt
README.md
```

## Core Files

- `backend/bug1/main.py`: FastAPI app, routes, CORS, startup hooks.
- `backend/bug1/rag.py`: verification pipeline, retrieval verdict logic, fallback routing.
- `backend/bug1/ingest.py`: corpus loading and local vector index build/load.
- `backend/bug1/utils.py`: OCR config/extraction, URL scraping, response normalization.
- `backend/bug1/multi_ai_fallback.py`: optional Gemini multi-key and multi-model fallback.
- `backend/bug1/convert_data.py`: utility script to convert TSV claims into text corpus lines.
- `frontend/fe/fe.html`: single-page UI that calls backend APIs.

## Backend API

Defined in `backend/bug1/main.py`:
- `GET /` - health message
- `POST /verify-text` - verify plain text
- `POST /verify-image` - verify uploaded image (multipart form-data)
- `POST /verify-url` - verify a URL by scraping text
- `POST /verify` - legacy alias of `/verify-text`

All verification endpoints return the same response shape (`status`, `confidence`, `summary`).

## Verification Pipeline (Current Behavior)

1. Input is cleaned/normalized.
2. Retriever gets relevant documents from local index (`ingest.py`).
3. Verdict is determined in `rag.py` using:
   - context relevance checks
   - document metadata labels
   - optional generator response parsing
4. If retrieval/generation is weak or fails, fallback can call Gemini via `multi_ai_fallback.py`.

Important implementation note:
- The project uses a local vector store implementation in `ingest.py` (saved to `faiss_index/index.faiss` and `faiss_index/index.pkl`).
- No LangChain dependency is used in the current code.

## OCR and URL Extraction

In `backend/bug1/utils.py`:
- OCR uses `pytesseract` + Tesseract executable.
- URL extraction uses `requests` + `BeautifulSoup`.
- Tesseract path resolution checks:
  1. `TESSERACT_CMD` env var
  2. `C:\Program Files\Tesseract-OCR\tesseract.exe`
  3. `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
  4. `D:\programs\tesseract\tesseract.exe`

## Setup (Windows)

### 1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

Use the root requirements file (same dependency set as `backend/bug1/requirements.txt`):

```powershell
pip install -r requirements.txt
```

### 3. Install Tesseract OCR (required for image verification)

1. Open: https://github.com/UB-Mannheim/tesseract/wiki
2. Download the latest Windows installer (`.exe`).
3. Install it.
4. Verify installation:

```powershell
tesseract --version
```

If `tesseract` is not recognized, set `TESSERACT_CMD` in `.env` (recommended).

### 4. Configure environment variables

Edit `backend/bug1/.env`:

```env
# Required for OCR if PATH is not set
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Optional fallback keys for Gemini
GEMINI_API_KEY_1=
GEMINI_API_KEY_2=
GEMINI_API_KEY_3=
GEMINI_API_KEY_4=
```

Security recommendation:
- Do not commit real API keys to version control.
- Rotate any keys that were exposed.

### 5. Run backend

```powershell
cd backend/bug1
uvicorn main:app --reload
```

Backend docs:
- http://127.0.0.1:8000/docs

### 6. Run frontend

Open `frontend/fe/fe.html` in your browser.

The frontend default backend URL is:
- `http://127.0.0.1:8000`

You can override before page script execution:
- `window.FACT_CHECK_API_BASE_URL = "http://your-host:8000"`

## How to Use in This Project

### Verify text claim

Request:

```json
{ "text": "The Earth orbits the Sun." }
```

Endpoint:
- `POST /verify-text`

### Verify image (pytesseract flow)

- Use image upload from frontend, or send multipart request to `POST /verify-image`.
- Backend reads the image, runs OCR, then verifies extracted text.

Example PowerShell using curl:

```powershell
curl -X POST "http://127.0.0.1:8000/verify-image" ^
  -H "accept: application/json" ^
  -H "Content-Type: multipart/form-data" ^
  -F "file=@C:/path/to/your/image.png"
```

### Verify URL

Request:

```json
{ "url": "https://example.com/article" }
```

Endpoint:
- `POST /verify-url`

## Response Contract (All verify endpoints)

```json
{
  "status": "Supported",
  "confidence": 76,
  "summary": "Retrieved evidence directly supports the claim."
}
```

## Data and Index Notes

- `ingest.py` reads local `.txt`, `.tsv`, and optional `.json/.jsonl` sources.
- If index files are missing/corrupt, the project rebuilds the index.
- Fallback example facts are also included if data is sparse.

## Utilities

- Build/rebuild index manually:

```powershell
cd backend/bug1
python ingest.py
```

- Convert training TSV to simple text corpus:

```powershell
cd backend/bug1
python convert_data.py
```

## Troubleshooting

- OCR returns empty text:
  - Confirm Tesseract is installed.
  - Confirm `TESSERACT_CMD` points to a valid `tesseract.exe`.
- URL verification returns uncertain:
  - Target site may block scraping or contain little readable text.
- Model fallback issues:
  - Ensure Gemini keys are valid if using cloud fallback.
