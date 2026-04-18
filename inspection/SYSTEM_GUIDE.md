# PARAKH Fact-Checking System - Complete Setup & Operations Guide

## 🎯 Overview

Parakh is an enterprise-grade AI fact-checking platform using Retrieval-Augmented Generation (RAG) with FAISS vector search and Gemini API fallback.

**Key Features:**
- ✅ Local FAISS vector indexing (10,223 claims from LIAR dataset)
- ✅ Multi-model Gemini API fallback (4 API keys configured)
- ✅ Web-based UI with dark/light modes and custom theming
- ✅ Text, URL, and image verification
- ✅ Comprehensive error handling and retry logic
- ✅ Professional confidence distribution graphs
- ✅ Real-time verification results

---

## 🚀 Quick Start (30 seconds)

### Option 1: Easiest - Double-Click Batch File

```bash
start-system.bat
```

This will:
1. ✓ Start the FastAPI backend on http://127.0.0.1:8000
2. ✓ Start the frontend web server on http://127.0.0.1:3000
3. ✓ Automatically open your browser

### Option 2: PowerShell (More Control)

```powershell
# Run with default settings
.\start-system.ps1

# Or specify custom ports
.\start-system.ps1 -Port 8001 -FrontendPort 3000 -AutoOpen $true
```

### Option 3: Manual - Separate Terminals

**Terminal 1 - Backend:**
```bash
cd inspection/backend/bug1
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd inspection/frontend/fe
python -m http.server 3000
```

**Then open browser:**
```
http://127.0.0.1:3000/fe.html
```

---

## 🧪 Testing

### After System Starts

Run the automated test suite:

```bash
python test-system.py
```

Expected output:
```
✓ PASS  Backend Connectivity (~50ms)
✓ PASS  Health Check (~40ms)
✓ PASS  Verify Text: 'The Earth orbits the Sun.' (Status: Supported, Confidence: 85%)
✓ PASS  Verify Text: 'The Earth is flat.' (Status: Refuted, Confidence: 92%)
```

### Manual Testing

#### Test 1: Text Verification

```bash
curl -X POST http://127.0.0.1:8000/verify-text \
  -H "Content-Type: application/json" \
  -d '{"text":"Earth orbits the Sun"}'
```

Expected response:
```json
{
  "status": "Supported",
  "confidence": 85,
  "summary": "This claim is supported by verified evidence. Retrieved context: ...",
  "evidence": [...]
}
```

#### Test 2: Health Check

```bash
curl http://127.0.0.1:8000/health
```

Response shows:
- `gemini_api_keys_configured`: Number of valid API keys
- `faiss_index_exists`: Whether FAISS vector index is loaded
- `data_sources_available`: Whether training data is available

#### Test 3: API Documentation

Open in browser:
```
http://127.0.0.1:8000/docs
```

This provides interactive Swagger documentation for all endpoints.

---

## 📋 Endpoints

### Health & Diagnostics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check (message) |
| GET | `/health` | Detailed diagnostics |
| GET | `/history` | Get verification history |

### Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/verify-text` | Verify a text claim |
| POST | `/verify-url` | Scrape and verify URL content |
| POST | `/verify-image` | OCR and verify image text |

### Request/Response Format

**Text Verification Request:**
```json
{
  "text": "The claim to verify here"
}
```

**Response:**
```json
{
  "status": "Supported|Refuted|Uncertain",
  "confidence": 0-100,
  "summary": "Human-readable explanation",
  "evidence": [
    {
      "speaker": "Source name",
      "statement": "Related fact from dataset"
    }
  ]
}
```

---

## ⚙️ Configuration

### Backend Environment Variables

Required for production (set in `.env` or Render dashboard):

```bash
# Gemini API Keys (at least one required)
GEMINI_API_KEY_1=sk-...
GEMINI_API_KEY_2=sk-...
GEMINI_API_KEY_3=sk-...
GEMINI_API_KEY_4=sk-...

# Optional: Hugging Face token
HUGGINGFACEHUB_API_TOKEN=hf_...

# Optional: Enable local LLM (disabled by default)
ENABLE_LOCAL_GENERATOR=0
FACT_CHECK_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

### Frontend Settings

Navigate to **Settings** → **Backend Connection** to configure:

- **Base API URL**: Points to backend (auto-detected for local dev)
- **Theme**: Dark/Light/Custom
- **Card Style**: Glass/Solid/Tinted
- **Accent Color**: 5 presets + custom gradient
- **Color Palette**: Full control over BG/Card/Text colors

---

## 🔧 Troubleshooting

### Backend Won't Start

**Error: Port already in use**
```
Address already in use
```

**Fix:**
- Change port in start-system: `.\start-system.ps1 -Port 8001`
- Or kill existing process: `Get-Process python | Stop-Process`

**Error: ModuleNotFoundError**
```
No module named 'fastapi'
```

**Fix:**
```bash
cd backend/bug1
pip install -r requirements.txt
```

### Frontend Not Connecting

**Error: "Server not reachable"**

**Causes & Fixes:**
1. Backend not running → Start backend first
2. Wrong API URL → Check Settings → Backend Connection
3. CORS issue → Should be fixed (CORSMiddleware enabled)
4. Firewall → Allow port 8000 in firewall

**Debug:**
```bash
# Check if backend is running
curl http://127.0.0.1:8000/health

# Check what IP frontend is using
console.log(app.state.apiBase)
```

### RAG Not Finding Results

**Problem: Always returns "Uncertain"**

**Causes:**
1. FAISS index not loaded → Check `/health` for `faiss_index_exists: false`
2. Data files missing → Ensure `train.tsv` exists in backend/bug1/
3. Retrieval too strict → System is intentionally permissive (1 term overlap minimum)

**Fix:**
```bash
# Check FAISS loading
python -c "from ingest import ensure_faiss_index; idx = ensure_faiss_index(); print('✓ Index loaded')"
```

### Production Deployment (Render)

1. **Push code to Git:**
   ```bash
   git add .
   git commit -m "feat: enhanced system with retry logic"
   git push origin main
   ```

2. **Set Environment Variables on Render Dashboard:**
   - Go to Service Settings → Environment
   - Add: `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc.
   - Add: `HUGGINGFACEHUB_API_TOKEN`

3. **Ensure Data Files are Committed:**
   ```bash
   git add backend/bug1/train.tsv backend/bug1/data.txt
   git commit -m "data: include training data for production"
   git push
   ```

4. **Verify Deployment:**
   ```bash
   curl https://your-app.onrender.com/health
   ```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                      │
│  • HTML/CSS/JS (no build step needed)                       │
│  • Real-time themes and color customization                │
│  • Retry logic (2 attempts with 2s backoff)                │
│  • Auto-detects local/production environment              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/FETCH
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              RAG PIPELINE                            │   │
│  │  1. Text Cleaning & Normalization                  │   │
│  │  2. FAISS Vector Similarity Search (k=8)           │   │
│  │  3. Context Relevance Check (1 term minimum)       │   │
│  │  4. Local Model Generation (if enabled)            │   │
│  │  5. Gemini API Fallback (multi-model)              │   │
│  │  6. Formatted JSON Response                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                       │                                      │
│       ┌───────────────┼───────────────┐                     │
│       ↓               ↓               ↓                     │
│   ┌────────────┐ ┌─────────┐  ┌──────────────┐             │
│   │  FAISS DB  │ │ Gemini  │  │  Utils/Cache │             │
│   │ (10.2K)    │ │  APIs   │  │   (SQLite)   │             │
│   └────────────┘ └─────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 UI Features

### Dark Mode (Default)
- Professional deep blues and purples
- Reduced eye strain for long sessions
- Default newspaper texture background

### Light Mode
- High transparency (newspaper clearly visible)
- Optimized contrast for reading
- Professional enterprise colors

### Custom Theme
- Full color control: Background, Card, Text
- Accent color presets: Purple, Blue, Green, Orange, Pink
- Custom gradient accent support
- Real-time preview as you adjust

### Graph
- Smooth Gaussian curve showing confidence distribution
- Dynamic peak positioning (Supported → right, Refuted → left)
- Color-coded gradient fill
- Professional typography

---

## 📱 Features

### Verification Modes
1. **Text**: Direct claim input
2. **URL**: Automatic web scraping
3. **Image**: OCR text extraction

### Result Display
- Verdict badge with color coding
- Confidence bar with percentage
- Rich summary with evidence attribution
- Speaker/source information

### History & Actions
- Local storage of verification history
- Share results to clipboard
- Download as PNG image
- Save to persistent storage
- Helpful/not helpful feedback

---

## 🔒 Security & Privacy

- ✅ **Zero Tracking**: No analytics or IP logging
- ✅ **Ephemeral Processing**: Data stored only in-memory during verification
- ✅ **Local Indexing**: FAISS runs entirely on local machine
- ✅ **Encrypted Transport**: TLS for external API calls (Gemini)
- ✅ **No Training**: Data never used to train Gemini models

---

## 📈 Performance

Expected response times:

| Operation | Time | Notes |
|-----------|------|-------|
| Health Check | 20-50ms | Diagnostic only |
| Text Verification | 500-2000ms | FAISS + LLM |
| URL Scrape | 2-5s | Download + verification |
| Image OCR | 1-3s | Tesseract interpretation |

---

## 🎓 Development

### Code Structure

```
inspection/
├── backend/bug1/
│   ├── main.py              # FastAPI app (CORS, endpoints)
│   ├── rag.py               # RAG pipeline (retrieval + generation)
│   ├── ingest.py            # FAISS indexing + data loading
│   ├── multi_ai_fallback.py # Gemini multi-model fallback
│   ├── utils.py             # Text processing, OCR, URL scraping
│   ├── train.tsv            # LIAR dataset (10.2K claims)
│   ├── faiss_index/         # FAISS binary index (auto-generated)
│   └── requirements.txt
│
├── frontend/
│   ├── fe.html              # Single-file web app
│   ├── fe/                  # Alternate location
│   └── index.html           # Enhanced version
│
├── start-system.ps1         # PowerShell launcher (advanced)
├── start-system.bat         # Batch launcher (simple)
├── test-system.py           # Automated test suite
└── README.md                # This file
```

### Key Improvements Made

1. **Backend Connection**
   - Smart environment detection (local vs deployed)
   - Automatic retry with 2s exponential backoff
   - Better error messages with diagnostic hints
   - CORS enabled for all origins

2. **Frontend UX**
   - Stop infinite loading on error
   - Show error banner with actionable messages
   - Enable retry button
   - Pre-configure API base URL

3. **Light Mode**
   - Much lower transparency (28% gradient opacity)
   - Newspaper texture clearly visible throughout
   - Better readability in bright environments

4. **Graph Rendering**
   - Smooth Gaussian curves (σ=16-20)
   - Dynamic peak positioning
   - Enhanced gradient fill with subtle glow
   - Professional appearance

5. **Auto-Start**
   - One-command system startup
   - Automatic browser opening
   - Port availability checking
   - Combined backend + frontend

---

## 💡 Tips & Tricks

### Clear Cache & Reset
Settings → Secure Wipe Cache → Wipe Cache
- Clears all verification history
- Resets preferences to defaults
- Clears stored API base URL

### Custom API Endpoint
1. Go to Settings
2. Backend Connection → paste your custom URL
3. Settings are saved to localStorage automatically

### Language Support
- English (English UI)
- Hindi (हिन्दी UI)
Select in Settings → Language Engine

### Download Results
- Click "↓ Download" button to get PNG
- Shows verdict, confidence, and claim
- Professional format for reporting

---

## 🆘 Support

### Common Questions

**Q: Why does it say "Uncertain" for obvious facts?**
A: Context from FAISS might not match exactly. Try different phrasing. Gemini fallback provides backup.

**Q: Can I use this without internet?**
A: Yes! Local FAISS works offline. Without Gemini keys, it uses local fallback corpus.

**Q: How do I add more training data?**
A: Modify `backend/bug1/ingest.py` to load additional datasets (CSV/TSV format).

**Q: Is my data stored?**
A: No. Only in-memory during verification. SQLite history is local-only.

### Error Messages Guide

| Error | Meaning | Fix |
|-------|---------|-----|
| "Server not reachable" | Backend down | Start backend |
| "No GEMINI_API_KEY found" | Keys missing | Add to .env |
| "FAISS index missing" | Data not loaded | Check backend logs |
| "Uncertainty – All models" | Internal error | Check /health endpoint |

---

## 📞 Next Steps

1. **Local Testing** → Run `start-system.bat` and test with the UI
2. **Verify Functionality** → Use `test-system.py` for automated tests
3. **Check Production** → Run `/health` endpoint to see configuration
4. **Deploy if Ready** → Push to Render and set environment variables

---

**Status:** ✓ System Ready | All Components Configured | Auto-Start Available

Last Updated: 2026-04-18
