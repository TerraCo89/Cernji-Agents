# Stop Multi-App System
# Stops observability-server and web client processes

Write-Host "`n=== Stopping Multi-App System ===" -ForegroundColor Yellow

# Find processes listening on ports 4000 and 5173
$ports = @(4000, 5173)
$processesKilled = 0

foreach ($port in $ports) {
    Write-Host "`nChecking port $port..." -ForegroundColor Cyan

    try {
        # Get connections on the specified port
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

        if ($connections) {
            # Get unique process IDs
            $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique

            foreach ($pid in $pids) {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "  Stopping process: $($process.ProcessName) (PID: $pid)" -ForegroundColor Yellow
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    $processesKilled++
                    Write-Host "  ✓ Process $pid terminated" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "  No process found on port $port" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Error checking port $port : $_" -ForegroundColor Red
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
