# Stop LangGraph Resume Agent Server
# PowerShell Script

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Stopping LangGraph Resume Agent" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host

# Find process listening on port 2024
$connection = Get-NetTCPConnection -LocalPort 2024 -State Listen -ErrorAction SilentlyContinue

if (-not $connection) {
    Write-Host "[INFO] No server found running on port 2024." -ForegroundColor Yellow
} else {
    $processId = $connection.OwningProcess
    Write-Host "[INFO] Found server process: $processId" -ForegroundColor Green

    # Get process details
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "[INFO] Process name: $($process.ProcessName)" -ForegroundColor White
        Write-Host "[INFO] Stopping gracefully..." -ForegroundColor Yellow

        # Try graceful shutdown first
        try {
            $process.CloseMainWindow() | Out-Null
            Start-Sleep -Seconds 2

            # Check if still running
            if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
                Write-Host "[WARNING] Graceful shutdown failed. Force stopping..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 1
            }

            Write-Host "[SUCCESS] Server stopped successfully." -ForegroundColor Green
        }
        catch {
            Write-Host "[ERROR] Failed to stop server: $_" -ForegroundColor Red
            exit 1
        }
    }
}

# Verify server is stopped
Start-Sleep -Seconds 1
$stillRunning = Get-NetTCPConnection -LocalPort 2024 -State Listen -ErrorAction SilentlyContinue

if ($stillRunning) {
    Write-Host "[WARNING] Port 2024 is still in use." -ForegroundColor Yellow
    Write-Host "Check with: Get-NetTCPConnection -LocalPort 2024" -ForegroundColor White
    exit 1
} else {
    Write-Host "[SUCCESS] Port 2024 is now free." -ForegroundColor Green
}

Write-Host
Read-Host "Press Enter to exit"
