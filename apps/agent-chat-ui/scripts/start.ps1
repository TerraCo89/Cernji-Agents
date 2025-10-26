# Start Agent Chat UI (Next.js Development Server)
# This script starts the Next.js development server for the agent-chat-ui application

$ErrorActionPreference = "Stop"

Write-Host "Starting Agent Chat UI..." -ForegroundColor Green

# Change to the agent-chat-ui directory
$AppDir = Split-Path -Parent $PSScriptRoot
Set-Location $AppDir

# Check if pnpm is installed
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "Error: pnpm is not installed. Please install it first." -ForegroundColor Red
    Write-Host "Run: npm install -g pnpm" -ForegroundColor Yellow
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    pnpm install
}

# Start the development server
Write-Host "Starting Next.js development server on http://localhost:3000" -ForegroundColor Cyan
pnpm dev
