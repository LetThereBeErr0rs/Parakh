# Inspection (Fact-Checking Application)

Inspection is a full-stack, evidence-based fact-checking application that allows users to verify claims from text, images, or URLs. It leverages Retrieval-Augmented Generation (RAG) backed by a FAISS vector database to retrieve trusted knowledge and uses Gemini API as a sophisticated fallback for general queries or missing context.

## 🚀 Features

- **Multi-Modal Input:** Verify text claims, scrape URLs, or extract text from images using OCR.
- **RAG Architecture:** Searches a FAISS knowledge base (powered by HuggingFace `all-MiniLM-L6-v2` embeddings) for reliable fact-check records.
- **Strict Evidence Filtering:** Implements strict L2 distance and relevance thresholding so the system never hallucinates evidence for unrelated claims.
- **Gemini Fallback:** Seamlessly delegates out-of-domain claims or general world knowledge questions to the Gemini LLM.
- **History Tracking:** Saves recent verifications locally using SQLite.
- **Interactive UI:** A modern, robust vanilla HTML/JS frontend with exponential backoff and timeout handling.

## 🏗️ Architecture Overview

1. **Frontend (`Vanilla HTML/JS/CSS`)**: Provides the user interface. It communicates directly with the FastAPI backend via REST.
2. **Backend (`FastAPI/Python`)**: Exposes fact-checking endpoints and handles OCR parsing, URL scraping, and history tracking.
3. **Retrieval (`FAISS`)**: Embeds user queries and searches local `.tsv` knowledge bases.
4. **Synthesis / Fallback (`LLM`)**: Combines retrieved evidence into a structured summary or uses Gemini API if the claim is outside the dataset's domain.

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, SQLite
- **AI/ML:** LangChain, FAISS, Sentence-Transformers, Google GenAI (Gemini)
- **OCR:** Pytesseract (Tesseract OCR), Pillow
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (Fetch API)

## 📁 Folder Structure

```text
C:\MyPrograms\FINAL_PROJECT\inspection\
│
├── inspection/
│   ├── backend/
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── rag.py                 # Retrieval & verdict logic
│   │   ├── ingest.py              # FAISS indexing script
│   │   ├── utils.py               # OCR & URL scraping helpers
│   │   ├── multi_ai_fallback.py   # Gemini API integration
│   │   └── .env                   # Environment variables (API Keys)
│   │
│   └── frontend/
│       └── index.html             # Main Frontend Application
│
├── .venv/                         # Python virtual environment
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## ⚙️ Installation Instructions

### 1. Prerequisites
- **Python 3.10+**
- **Tesseract OCR:** Must be installed on your system. 
  - Windows: Download from UB-Mannheim and ensure `tesseract.exe` is in your PATH (or placed in `C:\Program Files\Tesseract-OCR\`).

### 2. Virtual Environment Setup
Clone the repository and set up your Python environment from the project root:

```bash
cd C:\MyPrograms\FINAL_PROJECT\inspection
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in `inspection/backend/.env` with your Gemini API keys:
```env
GEMINI_API_KEY_1=your_key_here
ENABLE_LOCAL_GENERATOR=0
```

## 🏃 Startup Instructions

### Backend
The backend must be run as a module from the **project root folder**:
```bash
cd C:\MyPrograms\FINAL_PROJECT\inspection
.venv\Scripts\activate
python -m uvicorn inspection.backend.main:app --reload
```
The API will be available at: `http://127.0.0.1:8000`

### Frontend
You can open the frontend by simply double-clicking the `inspection/frontend/index.html` file in your browser, or serving it with a simple HTTP server:
```bash
cd inspection/frontend
python -m http.server 3000
```
Then navigate to `http://localhost:3000`.

## 🔌 API Endpoints

- `GET /health` : System diagnostics
- `POST /verify-text` : Accepts `{ "text": "claim" }`
- `POST /verify-url` : Accepts `{ "url": "https..." }`
- `POST /verify-image` : Accepts `multipart/form-data` with a file upload
- `GET /history` : Retrieves recent verifications

## 📸 Example Usage

*(Screenshots placeholders)*
- `![Dashboard](docs/dashboard.png)`
- `![Image Verification](docs/image_verification.png)`

## ⚠️ Known Limitations

- **Dataset Dependency:** RAG retrieval quality heavily depends on the comprehensiveness of the local `.tsv` training data.
- **Fallback Reliance:** General world knowledge or obscure claims that are missing from the FAISS index will heavily rely on the Gemini fallback API.
- **OCR Constraints:** Image text extraction relies on Tesseract and requires high-contrast, clear images to function optimally.
- **Production Deployment:** The current setup uses SQLite and Uvicorn development servers, which require migration to PostgreSQL/Gunicorn for enterprise-scale deployment.

## 🔮 Future Improvements

- Add support for video transcription and verification.
- Implement a more comprehensive Admin dashboard for managing the FAISS index.
- Migrate to a managed vector database (e.g., Pinecone or Weaviate).

## 📄 License

This project is licensed under the MIT License.
