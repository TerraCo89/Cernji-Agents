# Reset Observability System
# Stops system, clears events database, and restarts

Write-Host "`n=== Resetting Observability System ===" -ForegroundColor Yellow

# Get repository root
$repoRoot = Split-Path $PSScriptRoot -Parent
$eventsDb = Join-Path $repoRoot "data\events.db"

# Step 1: Stop the system
Write-Host "`nStep 1: Stopping system..." -ForegroundColor Cyan
& "$PSScriptRoot\stop-system.ps1"

# Wait a moment for processes to fully terminate
Start-Sleep -Seconds 2

# Step 2: Delete events database
Write-Host "`nStep 2: Clearing events database..." -ForegroundColor Cyan

if (Test-Path $eventsDb) {
    try {
        # Also remove WAL and SHM files if they exist
        $walFile = "$eventsDb-wal"
        $shmFile = "$eventsDb-shm"

        Remove-Item $eventsDb -Force
        Write-Host "  ✓ Removed $eventsDb" -ForegroundColor Green

        if (Test-Path $walFile) {
            Remove-Item $walFile -Force
            Write-Host "  ✓ Removed $walFile" -ForegroundColor Green
        }

        if (Test-Path $shmFile) {
            Remove-Item $shmFile -Force
            Write-Host "  ✓ Removed $shmFile" -ForegroundColor Green
        }

        Write-Host "  ✓ Events database cleared" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to delete database: $_" -ForegroundColor Red
        Write-Host "    Make sure no processes are using the database" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "  Events database not found (may already be deleted)" -ForegroundColor Gray
}

# Step 3: Recreate database
Write-Host "`nStep 3: Recreating database schema..." -ForegroundColor Cyan
Write-Host "  (Database will be created automatically on first server start)" -ForegroundColor Gray

# Step 4: Restart system
Write-Host "`nStep 4: Restarting system..." -ForegroundColor Cyan
& "$PSScriptRoot\start-system.ps1"

Write-Host "`n=== Reset Complete ===" -ForegroundColor Green
Write-Host "  The observability system has been reset with a fresh events database." -ForegroundColor Green
Write-Host ""
