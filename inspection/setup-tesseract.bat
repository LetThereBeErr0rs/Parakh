@echo off
REM ╔═══════════════════════════════════════════════════════════════════════════╗
REM ║  PARAKH - FIX TESSERACT PATH (Windows)                                   ║
REM ║  This sets up the environment variable for pytesseract to find Tesseract  ║
REM ╚═══════════════════════════════════════════════════════════════════════════╝

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         PARAKH - SETUP TESSERACT FOR OCR SUPPORT              ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check if Tesseract is installed in standard location
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ✓ Found Tesseract at: C:\Program Files\Tesseract-OCR\tesseract.exe
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    echo ✓ Found Tesseract at: C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
) else (
    echo ✗ Tesseract not found in standard locations!
    echo.
    echo 📥 INSTALLATION REQUIRED:
    echo   1. Download: https://github.com/UB-Mannheim/tesseract/releases
    echo   2. Download: tesseract-ocr-w64-setup-v5.x.exe
    echo   3. Run installer and choose default path
    echo   4. After installation, run this script again
    echo.
    pause
    exit /b 1
)

echo.
echo 🔧 Setting up environment variable...
echo   Setting: TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
echo.

REM Set environment variable in Windows system
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"

if errorlevel 1 (
    echo ❌ Failed to set environment variable (permissions required)
    echo   Try running this script as Administrator
    pause
    exit /b 1
)

echo ✓ Environment variable set successfully!
echo.
echo ✅ SETUP COMPLETE
echo.
echo Next steps:
echo   1. Close all open command prompts and Python terminals
echo   2. Restart your backend server:
echo      cd inspection\backend\bug1
echo      python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
echo   3. Try uploading an image again
echo.
echo 🧪 To test OCR immediately:
echo    python check-ocr.py
echo.
pause
