# Start FastAPI Server for LangGraph Agents
# This replaces 'langgraph dev' which has Windows compatibility issues

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  FastAPI LangGraph Server" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Kill any existing servers on port 2024
Write-Host "Checking for existing servers on port 2024..." -ForegroundColor Yellow
$existingProcess = Get-NetTCPConnection -LocalPort 2024 -ErrorAction SilentlyContinue
if ($existingProcess) {
    Write-Host "Killing existing process on port 2024..." -ForegroundColor Yellow
    Stop-Process -Id $existingProcess.OwningProcess -Force
    Start-Sleep -Seconds 2
}

# Start FastAPI server
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host ""
Write-Host "Server will be available at:" -ForegroundColor White
Write-Host "  http://127.0.0.1:2024" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run with uvicorn via uv
uv run uvicorn fastapi_server:app --host 127.0.0.1 --port 2024 --reload
