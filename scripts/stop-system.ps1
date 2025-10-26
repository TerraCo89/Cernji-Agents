# Stop Multi-App System
# Stops all system components:
# - Resume Agent LangGraph (port 2024)
# - Agent Chat UI (port 3000)
# - Observability Server (port 4000)
# - Web Dashboard (port 5173)

Write-Host "`n=== Stopping Multi-App System ===" -ForegroundColor Yellow

# Find processes listening on all system ports
$ports = @{
    2024 = "Resume Agent LangGraph"
    3000 = "Agent Chat UI"
    4000 = "Observability Server"
    5173 = "Web Dashboard"
}
$processesKilled = 0

foreach ($port in $ports.Keys | Sort-Object) {
    $serviceName = $ports[$port]
    Write-Host "`nChecking port $port ($serviceName)..." -ForegroundColor Cyan

    try {
        # Get connections on the specified port
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop

        if ($connections) {
            # Get unique process IDs
            $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

            foreach ($processId in $processIds) {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "  Stopping $serviceName - $($process.ProcessName) (PID: $processId)" -ForegroundColor Yellow
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                    $processesKilled++
                    Write-Host "  ✓ Process $processId terminated" -ForegroundColor Green
                }
            }
        }
    } catch {
        # If no connections found, the cmdlet throws an error - this is expected
        if ($_.Exception.Message -match "No MSFT_NetTCPConnection objects found" -or
            $_.CategoryInfo.Category -eq "ObjectNotFound") {
            Write-Host "  No process found on port $port" -ForegroundColor Gray
        } else {
            Write-Host "  Error checking port $port : $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Stop any PowerShell background jobs related to our services
Write-Host "`nCleaning up background jobs..." -ForegroundColor Cyan
$jobs = Get-Job | Where-Object { $_.State -eq 'Running' }

if ($jobs) {
    foreach ($job in $jobs) {
        Write-Host "  Stopping job: $($job.Id)" -ForegroundColor Yellow
        Stop-Job -Id $job.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $job.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Job $($job.Id) removed" -ForegroundColor Green
    }
} else {
    Write-Host "  No background jobs found" -ForegroundColor Gray
}

# Final status
Write-Host "`n=== System Stopped ===" -ForegroundColor Green
if ($processesKilled -gt 0) {
    Write-Host "  ✓ Stopped $processesKilled process(es)" -ForegroundColor Green
} else {
    Write-Host "  No processes were running" -ForegroundColor Gray
}

Write-Host ""
