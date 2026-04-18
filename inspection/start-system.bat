@echo off
REM ╔═══════════════════════════════════════════════════════════════════════════╗
REM ║           PARAKH FACT-CHECKING SYSTEM - QUICK START (BATCH)               ║
REM ║                   Run this file to start everything                       ║
REM ╚═══════════════════════════════════════════════════════════════════════════╝

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         PARAKH FACT-CHECKING SYSTEM - QUICKSTART              ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend\bug1
set FRONTEND_DIR=%SCRIPT_DIR%frontend\fe

echo 📁 Backend Directory:  %BACKEND_DIR%
echo 📁 Frontend Directory: %FRONTEND_DIR%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.10+ or add it to PATH
    pause
    exit /b 1
)

echo ✓ Python is available
echo.

REM Start Backend in new Command Prompt window
echo 🚀 Starting Backend on http://127.0.0.1:8000...
start "PARAKH Backend" cmd /k "cd /d %BACKEND_DIR% && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait a bit for backend to start
echo ⏳ Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak

REM Start Frontend in new Command Prompt window (on port 3000)
echo 🚀 Starting Frontend on http://127.0.0.1:3000...
start "PARAKH Frontend" cmd /k "cd /d %FRONTEND_DIR% && python -m http.server 3000"

REM Wait for frontend to start
echo ⏳ Waiting for frontend to start (2 seconds)...
timeout /t 2 /nobreak

REM Open in browser
echo 🌐 Opening browser...
start http://127.0.0.1:3000/fe.html

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                 SYSTEM IS RUNNING & READY                     ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 📌 KEY ENDPOINTS:
echo    • Frontend:     http://127.0.0.1:3000/fe.html
echo    • Backend API:  http://127.0.0.1:8000
echo    • API Docs:     http://127.0.0.1:8000/docs
echo    • Health Check: http://127.0.0.1:8000/health
echo.
echo 🧪 QUICK TEST:
echo    Try verifying 'Earth orbits the Sun' in the frontend
echo.
echo ⏹️  To stop: Close both terminal windows or press Ctrl+C
echo.
echo 💡 Both services will continue running. Don't close these windows!
echo.
pause
