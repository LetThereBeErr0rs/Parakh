# ⚡ PARAKH QUICK REFERENCE

## 🚀 30-SECOND STARTUP

```batch
cd inspection
start-system.bat
```

✓ Backend starts  
✓ Frontend starts  
✓ Browser opens automatically  

---

## 🧪 VERIFY IT WORKS

```bash
python test-system.py
```

Should show: **✓ All tests passed**

---

## 📍 KEY ENDPOINTS

| What | URL |
|------|-----|
| Frontend | http://127.0.0.1:3000/fe.html |
| API | http://127.0.0.1:8000 |
| API Docs | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

---

## 📝 QUICK TEST CLAIMS

```
✓ SUPPORTED:   "Earth orbits the Sun"
✗ REFUTED:     "Earth is flat"
✗ REFUTED:     "Vaccines cause autism"
✓ SUPPORTED:   "Water boils at 100°C"
```

---

## 🎨 FEATURES TO TRY

- [ ] Dark mode (default)
- [ ] Light mode (more transparent)
- [ ] Custom colors (Settings)
- [ ] Gradient accent colors
- [ ] URL verification (paste link)
- [ ] Image verification (upload photo)
- [ ] Graph animation (shows distribution)
- [ ] Error retry (turn off backend to test)
- [ ] History (bottom of verify panel)
- [ ] Download result (as PNG image)

---

## 🔧 TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| Port in use | Change: `.\start-system.ps1 -Port 8001` |
| Backend won't start | Check: `python -m pip install -r backend/bug1/requirements.txt` |
| "Server not reachable" | Verify: `curl http://127.0.0.1:8000/health` |
| API base URL wrong | Settings → Backend Connection → Clear or update |

---

## 📚 FULL DOCUMENTATION

- **Setup:** See `SYSTEM_GUIDE.md`
- **Changes:** See `COMPLETION_SUMMARY.md`
- **Development:** See code comments in `main.py`, `rag.py`, `index.html`

---

## 🎯 PRODUCTION DEPLOYMENT

1. Set environment variables on Render:
   ```
   GEMINI_API_KEY_1=sk-...
   GEMINI_API_KEY_2=sk-...
   GEMINI_API_KEY_3=sk-...
   GEMINI_API_KEY_4=sk-...
   ```

2. Push code to Git:
   ```bash
   git add .
   git commit -m "feat: enhanced system"
   git push
   ```

3. Verify:
   ```bash
   curl https://your-app.onrender.com/health
   ```

---

## 💡 PRO TIPS

- **Custom Backend URL:** Settings → Backend Connection → Paste your URL
- **Hide Sidebar:** Click menu icon (≡) to collapse navigation
- **Languages:** Settings → Language Engine → EN/HI
- **Theme Persistence:** All settings auto-save to browser storage
- **API Docs:** Visit http://127.0.0.1:8000/docs for interactive API explorer

---

## ✅ COMPLETED

- ✓ Backend connection auto-detection
- ✓ Retry logic (2 attempts, 2s backoff)
- ✓ CORS enabled
- ✓ RAG reliability (8 fallback conditions)
- ✓ Light mode improvement
- ✓ Graph professional rendering
- ✓ Full color customization
- ✓ Auto-start (one command)
- ✓ Auto-open browser
- ✓ Automated test suite

---

**Ready? Run:** `start-system.bat`

