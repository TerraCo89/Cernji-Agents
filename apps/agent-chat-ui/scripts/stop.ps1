# Stop Agent Chat UI (Next.js Development Server)
# This script stops the Next.js development server by killing the process on port 3000

$ErrorActionPreference = "Stop"

Write-Host "Stopping Agent Chat UI..." -ForegroundColor Yellow

# Find the process using port 3000
$Port = 3000
$ProcessId = $null

try {
    # Get the process ID listening on port 3000
    $Connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"

    if ($Connections) {
        foreach ($Connection in $Connections) {
            # Extract process ID from the last column
            $ProcessId = ($Connection -split '\s+')[-1]

            if ($ProcessId -and $ProcessId -ne "0") {
                Write-Host "Found process $ProcessId listening on port $Port" -ForegroundColor Cyan

                # Kill the process
                Stop-Process -Id $ProcessId -Force -ErrorAction Stop
                Write-Host "Successfully stopped process $ProcessId" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "No process found listening on port $Port" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error stopping process: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Agent Chat UI stopped." -ForegroundColor Green
