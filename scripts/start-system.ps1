# Start Multi-App System
# Starts observability-server and web client for Claude Code observability

Write-Host "`n=== Starting Multi-App System ===" -ForegroundColor Green

# Check if ports are already in use
$port4000 = Test-NetConnection -ComputerName localhost -Port 4000 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
$port5173 = Test-NetConnection -ComputerName localhost -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null

if ($port4000) {
    Write-Host "⚠ Port 4000 already in use (observability-server may already be running)" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        Write-Host "Aborted" -ForegroundColor Red
        exit 1
    }
}

if ($port5173) {
    Write-Host "⚠ Port 5173 already in use (web client may already be running)" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        Write-Host "Aborted" -ForegroundColor Red
        exit 1
    }
}

# Get repository root (script is in scripts/ directory)
$repoRoot = Split-Path $PSScriptRoot -Parent

Write-Host "`nStarting observability-server..." -ForegroundColor Cyan
try {
    # Start observability-server in background
    $serverPath = Join-Path $repoRoot "apps\observability-server"
    $serverJob = Start-Job -ScriptBlock {
        param($path)
        Set-Location $path
        bun run src/index.ts
    } -ArgumentList $serverPath

    Write-Host "  ✓ Observability server starting (Job ID: $($serverJob.Id))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start observability-server: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nStarting web client..." -ForegroundColor Cyan
try {
    # Start client in background
    $clientPath = Join-Path $repoRoot "apps\client"
    $clientJob = Start-Job -ScriptBlock {
        param($path)
        Set-Location $path
        bun run dev
    } -ArgumentList $clientPath

    Write-Host "  ✓ Web client starting (Job ID: $($clientJob.Id))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start web client: $_" -ForegroundColor Red
    Stop-Job $serverJob -ErrorAction SilentlyContinue
    Remove-Job $serverJob -ErrorAction SilentlyContinue
    exit 1
}

# Wait for services to start
Write-Host "`nWaiting for services to start (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verify services are running
Write-Host "`nVerifying services..." -ForegroundColor Cyan

$serverRunning = Test-NetConnection -ComputerName localhost -Port 4000 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
$clientRunning = Test-NetConnection -ComputerName localhost -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null

if ($serverRunning) {
    Write-Host "  ✓ Observability Server: http://localhost:4000" -ForegroundColor Green
} else {
    Write-Host "  ✗ Observability Server failed to start on port 4000" -ForegroundColor Red
    Write-Host "    Check job output with: Receive-Job -Id $($serverJob.Id)" -ForegroundColor Yellow
}

if ($clientRunning) {
    Write-Host "  ✓ Web Dashboard: http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "  ✗ Web Client failed to start on port 5173" -ForegroundColor Red
    Write-Host "    Check job output with: Receive-Job -Id $($clientJob.Id)" -ForegroundColor Yellow
}

Write-Host "`n=== System Status ===" -ForegroundColor Green
if ($serverRunning -and $clientRunning) {
    Write-Host "  ✓ All services running" -ForegroundColor Green
    Write-Host "`nOpen the dashboard in your browser: http://localhost:5173" -ForegroundColor Cyan
    Write-Host "MCP Server (resume-agent) runs via Claude Desktop - check .mcp.json configuration" -ForegroundColor Yellow
    Write-Host "`nTo stop the system, run: .\scripts\stop-system.ps1" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠ Some services failed to start" -ForegroundColor Yellow
    Write-Host "`nTo clean up, run: .\scripts\stop-system.ps1" -ForegroundColor Yellow
}

Write-Host ""
