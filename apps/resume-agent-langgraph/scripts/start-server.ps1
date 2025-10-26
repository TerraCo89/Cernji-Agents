# Start LangGraph Resume Agent Server
# PowerShell Script

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Starting LangGraph Resume Agent" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host

# Navigate to script directory
Set-Location $PSScriptRoot

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure your API keys."
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if already running
$listener = Get-NetTCPConnection -LocalPort 2024 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Host "[WARNING] Port 2024 is already in use. Server may already be running." -ForegroundColor Yellow
    Write-Host "Check with: Get-NetTCPConnection -LocalPort 2024"
    Write-Host
}

# Check if dependencies are installed
$anthropicInstalled = python -c "import anthropic" 2>$null
if (-not $?) {
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    python -m pip install -e .
    if (-not $?) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[INFO] Starting LangGraph server..." -ForegroundColor Green
Write-Host
Write-Host "API:       http://127.0.0.1:2024" -ForegroundColor White
Write-Host "Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024" -ForegroundColor White
Write-Host "API Docs:  http://127.0.0.1:2024/docs" -ForegroundColor White
Write-Host
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host

# Start the server (this will block)
try {
    langgraph dev
}
finally {
    Write-Host
    Write-Host "[INFO] LangGraph server stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}
