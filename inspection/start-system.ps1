# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║           PARAKH FACT-CHECKING SYSTEM - AUTO START & BROWSER OPEN          ║
# ║                 Starts Backend, Frontend, and Opens Browser                ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

param(
    [string]$Port = "8000",
    [string]$FrontendPort = "3000",
    [string]$AutoOpen = $true
)

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         PARAKH FACT-CHECKING SYSTEM - STARTUP                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$inspectionDir = $scriptDir
$backendDir = Join-Path $inspectionDir "backend\bug1"
$frontendDir = Join-Path $inspectionDir "frontend\fe"

Write-Host "📁 Backend Directory:  $backendDir" -ForegroundColor Gray
Write-Host "📁 Frontend Directory: $frontendDir" -ForegroundColor Gray
Write-Host ""

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    try {
        $tnc = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return $tnc.TcpTestSucceeded
    }
    catch {
        return $false
    }
}

# Check if ports are available
Write-Host "🔍 Checking available ports..." -ForegroundColor Yellow
if (Test-Port -Port $Port) {
    Write-Host "⚠️  Port $Port is already in use. Trying next available port..." -ForegroundColor Yellow
    $Port = 8001
    if (Test-Port -Port $Port) {
        $Port = 8002
    }
}

Write-Host "✓ Backend will run on port: $Port" -ForegroundColor Green
Write-Host ""

# Start Backend in new PowerShell window
Write-Host "🚀 Starting Backend (FastAPI)..." -ForegroundColor Cyan
$backendCmdlet = {
    Set-Location $using:backendDir
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                    BACKEND SERVICE RUNNING                   ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📍 API Base URL: http://127.0.0.1:$using:Port" -ForegroundColor Green
    Write-Host "🔗 Health Check: http://127.0.0.1:$using:Port/health" -ForegroundColor Green
    Write-Host "📚 API Docs: http://127.0.0.1:$using:Port/docs" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting uvicorn server..." -ForegroundColor Yellow
    Write-Host ""
    
    & python -m uvicorn main:app --host 127.0.0.1 --port $using:Port --reload 2>&1
}

$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmdlet -PassThru
Write-Host "✓ Backend started (PID: $($backendProcess.Id))" -ForegroundColor Green
Write-Host ""

# Wait for backend to be ready
Write-Host "⏳ Waiting for backend to be ready..." -ForegroundColor Yellow
$maxWait = 30
$elapsed = 0
$ready = $false

while ($elapsed -lt $maxWait) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -ErrorAction SilentlyContinue
        if ($health.status -eq "running") {
            $ready = $true
            break
        }
    }
    catch {
        # Still waiting...
    }
    Start-Sleep -Seconds 1
    $elapsed += 1
    Write-Host "." -NoNewline -ForegroundColor Cyan
}

if ($ready) {
    Write-Host " ✓ Backend is ready!" -ForegroundColor Green
}
else {
    Write-Host " ⚠️  Backend startup taking longer than expected. Continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""

# Start Frontend in new PowerShell window
Write-Host "🚀 Starting Frontend Web Server..." -ForegroundColor Cyan
$frontendCmdlet = {
    Set-Location $using:frontendDir
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                    FRONTEND SERVER RUNNING                   ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📍 Frontend URL: http://127.0.0.1:$using:FrontendPort" -ForegroundColor Green
    Write-Host "📄 File: $using:frontendDir\fe.html" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting HTTP server with Python..." -ForegroundColor Yellow
    Write-Host ""
    
    & python -m http.server $using:FrontendPort --directory $using:frontendDir 2>&1
}

$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmdlet -PassThru
Write-Host "✓ Frontend started (PID: $($frontendProcess.Id))" -ForegroundColor Green
Write-Host ""

# Wait a moment for frontend to start
Start-Sleep -Seconds 2

# Open in browser
if ($AutoOpen) {
    Write-Host "🌐 Opening in default browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 1
    
    $frontendUrl = "http://127.0.0.1:$FrontendPort/fe.html"
    Write-Host "   URL: $frontendUrl" -ForegroundColor Green
    
    Start-Process $frontendUrl
    Write-Host "✓ Browser opened!" -ForegroundColor Green
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                 SYSTEM IS RUNNING & READY                     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📌 KEY ENDPOINTS:" -ForegroundColor Yellow
Write-Host "   • Frontend:     http://127.0.0.1:$FrontendPort/fe.html" -ForegroundColor Cyan
Write-Host "   • Backend API:  http://127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "   • API Docs:     http://127.0.0.1:$Port/docs" -ForegroundColor Cyan
Write-Host "   • Health Check: http://127.0.0.1:$Port/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 QUICK TEST:" -ForegroundColor Yellow
Write-Host "   Try verifying 'Earth orbits the Sun' in the frontend" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏹️  To stop: Close both terminal windows or press Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Tip: Configure auto-open by editing this script or passing -AutoOpen `$false" -ForegroundColor Gray
Write-Host ""

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 60
    }
}
catch {
    Write-Host "⚠️  Cleaning up processes..." -ForegroundColor Yellow
}
finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue | Out-Null
    }
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue | Out-Null
    }
}
