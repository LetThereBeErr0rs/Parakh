# Project Context: Inspection

**Target Audience:** Future AI assistants and developers taking over this session. Read this document before suggesting major architectural changes or altering the retrieval logic.

---

## PROJECT SUMMARY
- **What it does:** Inspection is a fact-checking application that verifies textual claims, URLs, and text extracted from images against a local FAISS knowledge base, with a Gemini LLM fallback.
- **Why it was built:** To provide a verifiable, evidence-based fact-checking tool as a portfolio piece, prioritizing stability and reliable output over experimental features.
- **Current status:** Stable and operational. All core endpoints (text, image, URL) are functional. The frontend correctly interfaces with the backend.

---

## CURRENT WORKING STATE
- **Backend operational:** FastAPI runs flawlessly on Uvicorn.
- **Frontend operational:** Vanilla HTML/JS UI successfully manages state, fetch requests, and timeouts.
- **API operational:** `/verify-text`, `/verify-url`, `/verify-image`, and `/history` endpoints are stable.
- **OCR operational:** Pytesseract extracts text from image uploads.
- **Gemini fallback operational:** Handles general queries not found in the FAISS index.
- **FAISS operational:** Successfully embeds and searches claims using `all-MiniLM-L6-v2`.

---

## PROJECT STRUCTURE
- `inspection/` (Root Package)
  - `__init__.py`: Makes the directory a Python package.
  - `backend/`
    - `__init__.py`: Package marker.
    - `main.py`: FastAPI entry point and endpoint router.
    - `rag.py`: RAG logic, FAISS retrieval, relevance checks, and verdict finalisation.
    - `ingest.py`: Handles vectorising data and saving the FAISS index.
    - `utils.py`: Helper functions for OCR and URL scraping.
    - `multi_ai_fallback.py`: Interface for Google GenAI (Gemini) fallback.
  - `frontend/`
    - `index.html`: The monolithic frontend application containing UI, styling, and JavaScript logic.

---

## STARTUP INSTRUCTIONS
To guarantee correct Python module resolution, all commands **must** be executed from the project root (`C:\MyPrograms\FINAL_PROJECT\inspection`).

```bash
# 1. Activate the environment
.venv\Scripts\activate

# 2. Run the backend as a module
python -m uvicorn inspection.backend.main:app --reload
```

---

## DEPENDENCIES
- **Python Packages:** `fastapi`, `uvicorn`, `langchain`, `faiss-cpu`, `sentence-transformers`, `google-genai`, `pytesseract`, `Pillow`, `requests`, `beautifulsoup4`, `python-dotenv`.
- **Frontend Packages:** None. It uses vanilla HTML/JS and relies on standard browser Fetch API.
- **External Software:** Tesseract OCR (required for the image verification endpoint).

---

## ARCHITECTURE
- **User Flow:** User enters a claim (Text/URL/Image) into the frontend. The UI presents a loading state and displays the verdict (Supported, Refuted, Uncertain) alongside a summary and evidence snippets.
- **Frontend Flow:** `index.html` orchestrates requests using the Fetch API with an `AbortController` (60s timeout) and an exponential backoff retry mechanism (max 3 tries).
- **Backend Flow:** `main.py` parses requests, handles OCR/Scraping if necessary, and routes the extracted text to `verify_claim()` in `rag.py`.
- **Retrieval Flow:** `rag.py` embeds the query and searches the FAISS index. It applies a strict `MAX_DISTANCE = 0.98` filter and a `min_overlap=2` string-matching check to discard unrelated documents.
- **Gemini Fallback Flow:** If FAISS returns no highly relevant documents, the system seamlessly delegates the query to `multi_model_verify()` which utilizes the Gemini API.

---

## KNOWN FIXES APPLIED (Do Not Revert)
1. **Package import fixes:** Changed relative imports to absolute module imports (`inspection.backend.X`).
2. **`__init__.py` additions:** Added missing init files to ensure `inspection` is recognized as a package.
3. **Path corrections:** Fixed SQLite and FAISS paths to use absolute resolution based on `os.path.dirname(__file__)`.
4. **Frontend timeout fix:** Increased the frontend `fetch` timeout from 10s to 60s. Previously, the 10s timeout aborted Gemini fallback requests, causing false "Backend connection failed" errors.
5. **Retrieval relevance filtering:** Introduced L2 distance thresholding (`0.98`) to prevent FAISS from returning hallucinated evidence for off-topic queries.
6. **Repository cleanup:** Removed duplicated/dead HTML files and scripts to maintain a clean GitHub footprint.

---

## KNOWN LIMITATIONS
- Retrieval quality still depends heavily on dataset coverage (`train.tsv`).
- General world knowledge often bypasses FAISS and relies entirely on the Gemini fallback.
- Deployment has not yet been completed (currently relies on local Uvicorn and SQLite).

---

## IMPORTANT FILES
Handle these files with extreme care:
- `main.py`: Central router. Avoid altering Pydantic schemas unless the frontend is also updated.
- `rag.py`: Core RAG logic. Any changes to `_context_relevance` or `MAX_DISTANCE` dramatically affect system stability and hallucination rates.
- `index.html`: The entire frontend state machine. The `verify` function contains the critical fetch timeout and retry logic.

---

## RECOVERY GUIDE
If the project stops working during a future session, check these in order:
1. **Verify venv:** Is the virtual environment activated?
2. **Verify backend startup:** Are you running `python -m uvicorn inspection.backend.main:app` from the project root?
3. **Verify /docs:** Navigate to `http://127.0.0.1:8000/docs` to ensure FastAPI is running.
4. **Verify frontend API URL:** Does `window.app.DEFAULT_API_BASE` in `index.html` match the backend URL?
5. **Verify FAISS index:** Does `inspection/backend/faiss_index` exist? (If not, run `ingest.py`).
6. **Verify Gemini keys:** Are valid keys loaded in `inspection/backend/.env`?

---

## NEXT DEVELOPMENT PRIORITIES
1. **Deployment:** Containerize with Docker and deploy to Render/Railway.
2. **Retrieval Improvements:** Explore switching from FAISS to a managed vector DB (e.g., Pinecone) if the dataset grows.
3. **UI Improvements:** Enhance the design aesthetics (dark mode, better evidence snippet formatting).
4. **Analytics:** Implement basic logging or analytics for queries hitting the fallback vs. the FAISS index.

---

## HANDOVER NOTES
**To Future AI Assistants:**
This project is currently completely stable. The user prioritizes **stability and reliability over clever experiments**. 
Do not attempt to rewrite the RAG implementation or alter the `MAX_DISTANCE` / `min_overlap` thresholds in `rag.py` unless explicitly instructed to do so, as previous modifications to these values caused significant frontend timeout issues. 
When making changes, always ensure that your commands are executed from the project root (`C:\MyPrograms\FINAL_PROJECT\inspection`) to prevent Python `ModuleNotFoundError` issues.
