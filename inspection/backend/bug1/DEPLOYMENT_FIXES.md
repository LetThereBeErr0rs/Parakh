# Production Deployment Fixes - Render & Vercel

## Problem
The frontend (Vercel) was getting "All models failed" error when calling backend (Render), even though local testing works perfectly.

## Root Causes Identified & Fixed

### 1. **Environment Variables Not Loaded on Render**
**Problem:** The `.env` file is NOT automatically loaded on Render. You must set env vars in the Render dashboard.

**Fix Applied:**
- Removed dependency on `.env` being loaded
- Added startup validation logging to show what env vars are configured
- Added `/health` diagnostic endpoint

**Action Required on Render Dashboard:**
Set these environment variables in your Render service:
```
GEMINI_API_KEY_1=your_api_key_here
GEMINI_API_KEY_2=your_api_key_here
GEMINI_API_KEY_3=your_api_key_here
GEMINI_API_KEY_4=your_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_token_here
```

### 2. **Missing Data Files in Production**
**Problem:** `train.tsv` and `data.txt` may not be deployed to Render if not in `.gitignore` or if build process excluded them.

**Fix Applied:**
- Added `_create_fallback_corpus()` function that generates minimal test data
- System automatically falls back to minimal corpus if files are missing
- Never returns complete failure on startup

**Action Required:**
- Push `train.tsv` and `data.txt` to your Git repository
- Ensure they're in `.gitignore` is NOT blocking them
- Or use Render's "Build-time environment variables" to generate them

### 3. **FAISS Index Not Persisting or Rebuilding**
**Problem:** FAISS index builds in temp directory on Render and doesn't persist between deploys.

**Fix Applied:**
- Added robust index loading with auto-rebuild on corruption
- Added vector count logging for diagnostics
- Better error handling if index is corrupted

**Action Required:**
- Ensure `faiss_index/` directory is created and writable
- Consider using Render's persistent disk if available:
  ```yaml
  services:
    - name: backend
      environments:
        RENDER_PERSISTENT_FOLDER: /mnt/data
  ```

### 4. **Too-Strict Relevance Checking**
**Problem:** The relevance filter required 20% of question terms to match, blocking valid results.

**Fix Applied:**
- Reduced requirement from 20% to just 1 term match
- Much more permissive in production

### 5. **Weak Fallback Handling**
**Problem:** When local chain failed, the system would fallback to Gemini, but if no API keys were set, it returned generic "All models failed".

**Fix Applied:**
- Better error messages from `multi_ai_fallback.py`
- Checks if API keys exist at startup
- Improved logging of what failed and why
- System returns meaningful errors instead of silence

### 6. **Missing `evidence` Field in Responses**
**Problem:** Some response paths weren't including the expected `evidence` array.

**Fix Applied:**
- All endpoints now guarantee `evidence: []` in responses
- Updated `_structured_response()` helper
- Consistent JSON schema across all endpoints

## Verification Steps

### 1. Check Backend Health (Development)
```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "running",
  "gemini_api_keys_configured": 4,
  "faiss_index_exists": true,
  "data_sources_available": true,
  "timestamp": "2026-04-18T10:30:45.123456"
}
```

### 2. Test Verification Endpoint (Development)
```bash
curl -X POST http://localhost:8000/verify-text \
  -H "Content-Type: application/json" \
  -d '{"text": "The Earth orbits the Sun"}'
```

### 3. Monitor Production Logs on Render
- Go to Render Dashboard > your backend service
- Click "Logs"
- Look for lines starting with:
  - `✓ Found X valid Gemini API key(s)` ✅ (good)
  - `⚠ No GEMINI_API_KEY_n environment variables found` ⚠️ (needs env vars set)
  - `✓ RAG pipeline initialized successfully` ✅ (good)

## .gitignore Recommendations

```gitignore
# Don't ignore these in production:
# !train.tsv
# !data.txt
# !faiss_index/

# But DO ignore these:
.env
__pycache__/
*.pyc
history.db
```

## Frontend Environment Setup (Vercel)

Update your Vercel environment variables to point to your Render backend:

```
VITE_API_BASE_URL=https://your-backend.onrender.com
# or
REACT_APP_API_BASE_URL=https://your-backend.onrender.com
```

## Monitoring & Diagnostics

### Check if backend is reachable
```bash
# From Vercel (in browser console)
fetch('https://your-backend.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log(d))
```

### New Diagnostic Endpoint
Access this from your browser or curl to see deployment status:
```
https://your-backend.onrender.com/health
```

Returns:
- `gemini_api_keys_configured`: how many API keys are set
- `faiss_index_exists`: if vector store is ready
- `data_sources_available`: if data files were found
- `status`: "running" if healthy

## Summary of Changes

| Component | Issue | Fix |
|-----------|-------|-----|
| `ingest.py` | Missing data files crash startup | Added fallback corpus generation |
| `rag.py` | Too strict relevance gate | Relaxed from 20% to 1 term match |
| `rag.py` | No generator fallback | Detect when generator disabled, force external fallback |
| `main.py` | Missing responses fields | Make all responses include `evidence` array |
| `main.py` | No diagnostics | Added `/health` endpoint for production monitoring |
| `multi_ai_fallback.py` | Unhelpful error messages | Improved messages for missing API keys |

## Next Steps After Deployment

1. **Set Render Environment Variables** (CRITICAL)
2. **Push Code with `train.tsv` and `data.txt`** (if available)
3. **Deploy Backend** on Render
4. **Test `/health` endpoint** to verify configuration
5. **Test `/verify-text` endpoint** with a sample claim
6. **Monitor Logs** for warnings about missing API keys or FAISS issues
7. **Update Vercel** to point to new backend URL (if changed)

## Emergency Fallback

If nothing works, the system will:
1. Use minimal fallback corpus (5 test facts)
2. Return "Uncertain" with 50% confidence
3. Include diagnostic information in logs

This ensures the API never completely fails, even in worst-case scenarios.
