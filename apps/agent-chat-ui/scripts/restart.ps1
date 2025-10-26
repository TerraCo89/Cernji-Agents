# Restart Agent Chat UI (Next.js Development Server)
# This script stops and then starts the Next.js development server

$ErrorActionPreference = "Stop"

Write-Host "Restarting Agent Chat UI..." -ForegroundColor Cyan

# Get the scripts directory
$ScriptsDir = $PSScriptRoot

# Stop the server
Write-Host "`nStopping server..." -ForegroundColor Yellow
& "$ScriptsDir\stop.ps1"

# Wait a moment before starting
Start-Sleep -Seconds 2

# Start the server
Write-Host "`nStarting server..." -ForegroundColor Green
& "$ScriptsDir\start.ps1"
