# 🖼️ IMAGE OCR TROUBLESHOOTING GUIDE

## ❌ Problem: "No readable text was found in the uploaded image"

When you try to upload an image with text, you get one of these messages:
- "No readable text was found"
- "OCR service unavailable: Tesseract is not installed"
- "The image could not be processed"

---

## 🔍 Root Causes

### **1. Tesseract Not Installed (Most Common)**

**Error Message:**
```
OCR service unavailable: Tesseract is not installed. 
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Solution:**

**Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Download latest version (e.g., `tesseract-ocr-w64-setup-v5.x.exe`)
3. Run the installer
4. Keep default install path: `C:\Program Files\Tesseract-OCR`
5. Complete installation
6. **Restart the backend server**

```batch
# Download link:
https://github.com/UB-Mannheim/tesseract/releases
# Choose: tesseract-ocr-w64-setup-v5.x.exe
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
# Verify:
tesseract --version
```

**Linux (Fedora/RHEL):**
```bash
sudo yum install tesseract
```

**macOS:**
```bash
brew install tesseract
# Verify:
tesseract --version
```

---

### **2. Image Quality Too Low for OCR**

**Error Message:**
```
No readable text was found in the image. Try:
• Use clearer text (avoid cursive/decorative fonts)
• Increase image resolution
• Improve lighting
```

**Solutions:**

✓ **Use high-quality images:**
- Resolution: At least 300x300 pixels (higher is better)
- Format: JPG, PNG, WEBP (not BMP or GIF)
- Quality: Sharp, not blurry or low-contrast

✓ **Improve image quality:**
- Take photo with good lighting (no shadows/glare)
- Use black text on white background (best for OCR)
- Crop to just the important text area
- Avoid curved/decorative fonts

✓ **Test images that work:**
```
❌ BAD:
  • Screenshot with 8pt font
  • Photo of handwritten text
  • Blurry document scan
  • Rainbow gradient background
  
✓ GOOD:
  • Screenshot of normal text (14pt+)
  • High-resolution document scan
  • Photo of printed text with good lighting
  • Simple white background
```

---

### **3. Image Processing Errors**

**Error Message:**
```
The uploaded file could not be processed as a readable image.
Try JPG, PNG, or WEBP format.
```

**Solutions:**

✓ **Check image format:**
```
Supported: JPG, PNG, WEBP, GIF
Verify: Image actually opens in Windows Photos or web browser
```

✓ **Fix corrupted images:**
```
• Re-save the image (File → Export As)
• Use online converter: jpegmini.com, tinypng.com
• Screenshot again instead of uploading
```

✓ **Check file size:**
```
• Max recommended: < 20MB
• If too large: compress or resize
```

---

## 🧪 Quick Diagnostic

### Check if Tesseract is installed:

```bash
# Windows (PowerShell)
Get-Command tesseract

# Linux/macOS
which tesseract

# Python check
python -c "import pytesseract; print('✓ pytesseract installed')"
```

### Run diagnostic tool:

```bash
cd inspection
python check-ocr.py
```

This will show:
- ✓ Python packages status
- ✓ Tesseract installation location
- ✓ Tesseract functionality test
- ✓ Backend configuration

---

## 🛠️ Step-by-Step Fix

### **Step 1: Install Tesseract (if not installed)**

```batch
# Windows: Download and run installer
https://github.com/UB-Mannheim/tesseract/releases

# Linux:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
```

### **Step 2: Verify Installation**

```bash
# Check Tesseract is accessible
tesseract --version

# Should output something like:
# tesseract 5.x.x
# leptonica-1.x.x
```

### **Step 3: Restart Backend**

```batch
# Close backend server (Ctrl+C)
# Restart:
cd inspection\backend\bug1
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### **Step 4: Check Backend Logs**

Look for these lines in backend console:
```
[OCR] Original image size: (width, height)
[OCR] Converted to grayscale
[OCR] Enhanced contrast (2.5x)
[OCR] Started Tesseract OCR processing
[OCR] Extracted {N} characters
```

If you see these logs, OCR is working!

### **Step 5: Test with Sample Image**

Try uploading a simple test image:

**Good test image:**
```
Plain black text on white background
Font size: 14pt or larger
Example: "The Earth orbits the Sun"
```

**Expected result:**
```
Status: Supported (or Refuted, depending on claim)
Confidence: 75-90%
Summary: Shows verification result for the extracted text
```

---

## 📋 Troubleshooting Checklist

- [ ] Tesseract installed (run `tesseract --version`)
- [ ] pytesseract installed (`pip install pytesseract`)
- [ ] Backend restarted after installation
- [ ] Image is JPG/PNG/WEBP format
- [ ] Image has readable text (not blurry/low-quality)
- [ ] Image text is clear (not decorative/cursive)
- [ ] Image resolution is at least 300x300 pixels
- [ ] File size is < 20MB
- [ ] Backend shows no OCR errors in console
- [ ] Diagnostic tool passes: `python check-ocr.py`

---

## 🔍 Advanced Debugging

### Check Backend Logs

**Windows (PowerShell):**
```powershell
# Look at full backend output - you should see:
[OCR] Original image size: (width, height)
[OCR] Extracted {N} characters
```

**Linux/macOS:**
```bash
# Run backend with verbose logging
PYTHONUNBUFFERED=1 python -m uvicorn main:app --reload

# Check logs:
tail -f backend.log
```

### Test with curl

```bash
# Test endpoint directly
curl -F "file=@test-image.png" http://127.0.0.1:8000/verify-image

# Expected response (if OCR works):
{
  "status": "Supported",
  "confidence": 85,
  "summary": "...",
  "evidence": [...]
}
```

### Set Custom Tesseract Path

If Tesseract is in non-standard location, set environment variable:

**Windows (PowerShell):**
```powershell
$env:TESSERACT_CMD = "C:\Custom\Path\tesseract.exe"
python -m uvicorn main:app --reload
```

**Linux/macOS:**
```bash
export TESSERACT_CMD="/custom/path/tesseract"
python -m uvicorn main:app --reload
```

---

## 🎯 Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "OCR service unavailable" | Tesseract not installed | Install from GitHub link |
| "No readable text found" | Image quality poor | Use clearer, higher-res image |
| "Invalid image format" | Wrong file type | Upload JPG, PNG, or WEBP |
| "File not processed" | Corrupted image | Re-save or re-screenshot |
| "Unexpected backend error" | Permission issue | Check file permissions |

---

## ✅ Workaround (Temporary)

If you can't install Tesseract right now, use this workaround:

1. **Manually copy text from image**
2. **Use "Analyze Text" instead of image upload**
3. **Paste the copied text**

This will verify the text without needing OCR.

---

## 💡 Tips for Best Results

### ✓ DO:
- Use official screenshots (Ctrl+PrintScreen → Save as PNG)
- Use clear, readable fonts (Arial, Calibri, Times New Roman)
- Ensure good contrast (black text on white)
- Use natural lighting if photographing
- Crop to show only the text you want to verify

### ✗ DON'T:
- Use phone camera photos of screens (blurry/glare)
- Use handwritten documents without scanning
- Use small fonts (< 10pt)
- Use decorative/artistic fonts
- Upload .BMP or .TIFF files
- Resize very small images

---

## 📞 Still Having Issues?

### Check these error messages:

**"pytesseract is not installed"**
```bash
pip install pytesseract
pip install Pillow  # Image library
```

**"Tesseract command not found" (Linux/Mac)**
```bash
# Make sure installed:
which tesseract
# If not found, reinstall
```

**"Please install Tesseract" message**
- This appear if the file couldn't be found in standard locations
- Set `TESSERACT_CMD` environment variable externally

### Need more help?

1. Check backend logs for specific error message
2. Run `python check-ocr.py` for diagnostic report
3. Try diagnostic test email with log output
4. Share exact error message from backend console

---

## 📊 Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Image upload | < 1s | File transfer |
| Image processing | 1-3s | Quality enhancement |
| OCR extraction | 2-5s | Tesseract processing |
| Verification | 1-2s | RAG verification |
| **Total** | **5-11s** | Typical end-to-end |

If significantly slower, image might be very large or resolution very high.

---

**Last Updated**: 2026-04-18  
**Version**: 1.0  
**Status**: Ready for OCR support
