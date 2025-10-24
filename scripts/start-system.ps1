# Start Multi-App System
# Starts all system components:
# - Observability Server (port 4000)
# - Web Dashboard (port 5173)
# - Resume Agent LangGraph (port 2024)
# - Agent Chat UI (port 3000)

Write-Host "`n=== Starting Multi-App System ===" -ForegroundColor Green

# Check if ports are already in use
$ports = @{
    2024 = "Resume Agent LangGraph"
    3000 = "Agent Chat UI"
    4000 = "Observability Server"
    5173 = "Web Dashboard"
}

$portsInUse = @()

foreach ($port in $ports.Keys) {
    $portCheck = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
    if ($portCheck) {
        Write-Host "⚠ Port $port already in use ($($ports[$port]) may already be running)" -ForegroundColor Yellow
        $portsInUse += $port
    }
}

if ($portsInUse.Count -gt 0) {
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        Write-Host "Aborted" -ForegroundColor Red
        exit 1
    }
}

# Get repository root (script is in scripts/ directory)
$repoRoot = Split-Path $PSScriptRoot -Parent

# Track all jobs for cleanup on error
$allJobs = @()

Write-Host "`nStarting Resume Agent LangGraph Server..." -ForegroundColor Cyan
try {
    $langgraphPath = Join-Path $repoRoot "apps\resume-agent-langgraph"
    $langgraphJob = Start-Job -ScriptBlock {
        param($path)
        Set-Location $path
        # Check for .env file
        if (-not (Test-Path ".env")) {
            Write-Host "[ERROR] .env file not found in resume-agent-langgraph!" -ForegroundColor Red
            Write-Host "Please copy .env.example to .env and configure your API keys."
            exit 1
        }
        langgraph dev
    } -ArgumentList $langgraphPath

    $allJobs += $langgraphJob
    Write-Host "  ✓ Resume Agent LangGraph starting (Job ID: $($langgraphJob.Id))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start Resume Agent LangGraph: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nStarting Agent Chat UI..." -ForegroundColor Cyan
try {
    $chatUIPath = Join-Path $repoRoot "apps\agent-chat-ui"
    $chatUIJob = Start-Job -ScriptBlock {
        param($path)
        Set-Location $path
        pnpm dev
    } -ArgumentList $chatUIPath

    $allJobs += $chatUIJob
    Write-Host "  ✓ Agent Chat UI starting (Job ID: $($chatUIJob.Id))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start Agent Chat UI: $_" -ForegroundColor Red
    foreach ($job in $allJobs) {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -ErrorAction SilentlyContinue
    }
    exit 1
}

Write-Host "`nStarting Observability Server..." -ForegroundColor Cyan
try {
    $serverPath = Join-Path $repoRoot "apps\observability-server"
    $serverJob = Start-Job -ScriptBlock {
        param($path)
        Set-Location $path
        bun run src/index.ts
    } -ArgumentList $serverPath

    $allJobs += $serverJob
    Write-Host "  ✓ Observability server starting (Job ID: $($serverJob.Id))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start observability-server: $_" -ForegroundColor Red
    foreach ($job in $allJobs) {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -ErrorAction SilentlyContinue
    }
    exit 1
}

Write-Host "`nStarting Web Dashboard..." -ForegroundColor Cyan
try {
    $clientPath = Join-Path $repoRoot "apps\client"
    $clientJob = Start-Job -ScriptBlock {
        param($path)
        Set-Location $path
        bun run dev
    } -ArgumentList $clientPath

    $allJobs += $clientJob
    Write-Host "  ✓ Web Dashboard starting (Job ID: $($clientJob.Id))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start web client: $_" -ForegroundColor Red
    foreach ($job in $allJobs) {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -ErrorAction SilentlyContinue
    }
    exit 1
}

# Wait for services to start
Write-Host "`nWaiting for services to start (8 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Verify services are running
Write-Host "`nVerifying services..." -ForegroundColor Cyan

$services = @{
    2024 = @{ Name = "Resume Agent LangGraph"; Job = $langgraphJob }
    3000 = @{ Name = "Agent Chat UI"; Job = $chatUIJob }
    4000 = @{ Name = "Observability Server"; Job = $serverJob }
    5173 = @{ Name = "Web Dashboard"; Job = $clientJob }
}

$runningCount = 0

foreach ($port in $services.Keys | Sort-Object) {
    $service = $services[$port]
    $running = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null

    if ($running) {
        Write-Host "  ✓ $($service.Name): http://localhost:$port" -ForegroundColor Green
        $runningCount++
    } else {
        Write-Host "  ✗ $($service.Name) failed to start on port $port" -ForegroundColor Red
        Write-Host "    Check job output with: Receive-Job -Id $($service.Job.Id)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== System Status ===" -ForegroundColor Green
if ($runningCount -eq 4) {
    Write-Host "  ✓ All services running ($runningCount/4)" -ForegroundColor Green
    Write-Host "`n📊 Quick Links:" -ForegroundColor Cyan
    Write-Host "  • Resume Agent API: http://localhost:2024/docs" -ForegroundColor White
    Write-Host "  • Agent Chat UI: http://localhost:3000" -ForegroundColor White
    Write-Host "  • Observability Dashboard: http://localhost:5173" -ForegroundColor White
    Write-Host "  • LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024" -ForegroundColor White
    Write-Host "`n💡 Note: MCP Server (resume-agent) runs via Claude Desktop - check .mcp.json configuration" -ForegroundColor Yellow
    Write-Host "`nTo stop the system, run: .\scripts\stop-system.ps1" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠ Some services failed to start ($runningCount/4 running)" -ForegroundColor Yellow
    Write-Host "`nTo clean up, run: .\scripts\stop-system.ps1" -ForegroundColor Yellow
}

Write-Host ""
