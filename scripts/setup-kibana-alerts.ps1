# Kibana Alerts Setup Script
# This script helps you set up automatic error detection alerts in Kibana

param(
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Kibana Alerts Setup Script
===========================

This script will guide you through setting up Kibana alerts for automatic
error detection and analysis.

Usage:
    .\scripts\setup-kibana-alerts.ps1

Prerequisites:
    - Kibana running on http://localhost:5601
    - Observability server running on port 4000
    - Elasticsearch running on port 9200

What this script does:
    1. Checks Kibana is accessible
    2. Provides step-by-step instructions to create webhook connector
    3. Provides step-by-step instructions to create alert rules
    4. Tests the alerts with sample errors
    5. Verifies the workflow

"@
    exit 0
}

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Kibana Automatic Error Detection Setup" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Step 1: Check prerequisites
Write-Host "[Step 1/6] Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

$kibanaUrl = "http://localhost:5601"
$obsServerUrl = "http://localhost:4000"
$esUrl = "http://localhost:9200"

try {
    $kibanaStatus = Invoke-RestMethod -Uri "$kibanaUrl/api/status" -Method Get -TimeoutSec 5
    Write-Host "  [OK] Kibana is running (v$($kibanaStatus.version.number))" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Kibana is not accessible at $kibanaUrl" -ForegroundColor Red
    Write-Host "  Please start Kibana and try again." -ForegroundColor Red
    exit 1
}

try {
    Invoke-RestMethod -Uri "$obsServerUrl/events/recent?limit=1" -Method Get -TimeoutSec 5 | Out-Null
    Write-Host "  [OK] Observability server is running" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Observability server is not accessible at $obsServerUrl" -ForegroundColor Red
    Write-Host "  Start it with: cd apps/observability-server && bun run dev" -ForegroundColor Yellow
    exit 1
}

try {
    $esStatus = Invoke-RestMethod -Uri $esUrl -Method Get -TimeoutSec 5
    Write-Host "  [OK] Elasticsearch is running (v$($esStatus.version.number))" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Elasticsearch is not accessible at $esUrl" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verify Kibana encryption keys
Write-Host "🔍 Verifying Kibana encryption keys..." -ForegroundColor Cyan

try {
    $keyCheck = docker exec cernji-kibana bash -c 'test -n "$XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY" && echo "present"' 2>$null

    if ($keyCheck -eq "present") {
        Write-Host "  [OK] Encryption keys are configured" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Encryption keys not found in Kibana container" -ForegroundColor Yellow
        Write-Host "  This will prevent alerting features from working." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  The keys are defined in docker-compose.yml but the container" -ForegroundColor Gray
        Write-Host "  was created before they were added." -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Recreating Kibana container with encryption keys..." -ForegroundColor Cyan

        Set-Location docker/elk
        docker-compose down kibana 2>&1 | Out-Null
        docker-compose up -d kibana 2>&1 | Out-Null
        Set-Location ../..

        Write-Host "  Waiting 45 seconds for Kibana to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 45

        # Verify keys are now present
        $keyCheckRetry = docker exec cernji-kibana bash -c 'test -n "$XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY" && echo "present"' 2>$null

        if ($keyCheckRetry -eq "present") {
            Write-Host "  [OK] Kibana restarted successfully with encryption keys" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Encryption keys still not found after restart" -ForegroundColor Red
            Write-Host "  Please check docker-compose.yml configuration." -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "  [WARNING] Could not verify encryption keys: $_" -ForegroundColor Yellow
    Write-Host "  Continuing anyway..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "All prerequisites met!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to continue"

# Step 2: Create Webhook Connector
Write-Host ""
Write-Host "[Step 2/6] Create Webhook Connector" -ForegroundColor Yellow
Write-Host ""
Write-Host "We need to create a webhook connector in Kibana that will send alerts"
Write-Host "to the observability server."
Write-Host ""
Write-Host "Follow these steps:"
Write-Host ""
Write-Host "1. Open Kibana in your browser:" -ForegroundColor Cyan
Write-Host "   $kibanaUrl" -ForegroundColor White
Write-Host ""
Write-Host "2. Navigate to: Stack Management > Rules and Connectors > Connectors" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Click 'Create connector'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Select 'Webhook' connector type" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Fill in the details:" -ForegroundColor Cyan
Write-Host "   Name:               Error Analysis Webhook" -ForegroundColor White
Write-Host "   URL:                http://host.docker.internal:4000/alerts/trigger" -ForegroundColor White
Write-Host "   Method:             POST" -ForegroundColor White
Write-Host "   Headers:            Content-Type = application/json" -ForegroundColor White
Write-Host "   Authentication:     None" -ForegroundColor White
Write-Host ""
Write-Host "6. Click 'Test' to verify the connection works" -ForegroundColor Cyan
Write-Host ""
Write-Host "7. Click 'Save'" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter when you've created the webhook connector"

# Step 3: Create Alert Rule #1 - High Error Rate (Resume Agent)
Write-Host ""
Write-Host "[Step 3/6] Create Alert Rule: High Error Rate - Resume Agent" -ForegroundColor Yellow
Write-Host ""
Write-Host "Now we'll create the first alert rule to detect high error rates."
Write-Host ""
Write-Host "Follow these steps:"
Write-Host ""
Write-Host "1. In Kibana, go to: Stack Management > Rules and Connectors > Rules" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Click 'Create rule'" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Fill in Rule details:" -ForegroundColor Cyan
Write-Host "   Name:               High Error Rate - Resume Agent" -ForegroundColor White
Write-Host "   Tags:               error-detection, automatic-analysis, resume-agent" -ForegroundColor White
Write-Host "   Check every:        1 minute" -ForegroundColor White
Write-Host "   Notify:             On status changes" -ForegroundColor White
Write-Host ""
Write-Host "4. Select Rule type: 'Elasticsearch query'" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Configure the query:" -ForegroundColor Cyan
Write-Host "   Index:              logs-*" -ForegroundColor White
Write-Host "   Time field:         @timestamp" -ForegroundColor White
Write-Host ""
Write-Host "   Query (copy this):" -ForegroundColor White
Write-Host '   {' -ForegroundColor Gray
Write-Host '     "query": {' -ForegroundColor Gray
Write-Host '       "bool": {' -ForegroundColor Gray
Write-Host '         "must": [' -ForegroundColor Gray
Write-Host '           { "term": { "log.level": "error" } },' -ForegroundColor Gray
Write-Host '           { "term": { "service.name": "resume-agent" } }' -ForegroundColor Gray
Write-Host '         ]' -ForegroundColor Gray
Write-Host '       }' -ForegroundColor Gray
Write-Host '     }' -ForegroundColor Gray
Write-Host '   }' -ForegroundColor Gray
Write-Host ""
Write-Host "6. Set threshold:" -ForegroundColor Cyan
Write-Host "   When:               Count of matches" -ForegroundColor White
Write-Host "   IS ABOVE:           10" -ForegroundColor White
Write-Host "   For the last:       5 minutes" -ForegroundColor White
Write-Host ""
Write-Host "7. Add Action:" -ForegroundColor Cyan
Write-Host "   Action type:        Webhook" -ForegroundColor White
Write-Host "   Connector:          Error Analysis Webhook" -ForegroundColor White
Write-Host ""
Write-Host "   Body (copy this):" -ForegroundColor White
Write-Host '   {' -ForegroundColor Gray
Write-Host '     "alert_id": "{{alert.id}}",' -ForegroundColor Gray
Write-Host '     "alert_name": "{{rule.name}}",' -ForegroundColor Gray
Write-Host '     "service": "resume-agent",' -ForegroundColor Gray
Write-Host '     "error_count": "{{context.hits}}",' -ForegroundColor Gray
Write-Host '     "severity": "high",' -ForegroundColor Gray
Write-Host '     "timestamp": "{{date}}",' -ForegroundColor Gray
Write-Host '     "time_range": "5m"' -ForegroundColor Gray
Write-Host '   }' -ForegroundColor Gray
Write-Host ""
Write-Host "8. Click 'Save'" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter when you've created the alert rule"

# Step 4: Create Alert Rule #2 - Critical Error Patterns
Write-Host ""
Write-Host "[Step 4/6] Create Alert Rule: Critical Error Patterns" -ForegroundColor Yellow
Write-Host ""
Write-Host "Create a second alert for critical error types."
Write-Host ""
Write-Host "Follow the same steps, but use these values:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Name:               Critical Error Patterns" -ForegroundColor White
Write-Host "   Tags:               error-detection, automatic-analysis, critical" -ForegroundColor White
Write-Host "   Check every:        1 minute" -ForegroundColor White
Write-Host ""
Write-Host "   Query:" -ForegroundColor White
Write-Host '   {' -ForegroundColor Gray
Write-Host '     "query": {' -ForegroundColor Gray
Write-Host '       "bool": {' -ForegroundColor Gray
Write-Host '         "must": [' -ForegroundColor Gray
Write-Host '           { "term": { "log.level": "error" } },' -ForegroundColor Gray
Write-Host '           { "terms": { "error.type.keyword": [' -ForegroundColor Gray
Write-Host '             "ModuleNotFoundError",' -ForegroundColor Gray
Write-Host '             "ImportError",' -ForegroundColor Gray
Write-Host '             "ConnectionError",' -ForegroundColor Gray
Write-Host '             "TimeoutError"' -ForegroundColor Gray
Write-Host '           ]}}' -ForegroundColor Gray
Write-Host '         ]' -ForegroundColor Gray
Write-Host '       }' -ForegroundColor Gray
Write-Host '     }' -ForegroundColor Gray
Write-Host '   }' -ForegroundColor Gray
Write-Host ""
Write-Host "   Threshold:          IS ABOVE 3 for the last 1 minute" -ForegroundColor White
Write-Host ""
Write-Host "   Webhook Body:" -ForegroundColor White
Write-Host '   {' -ForegroundColor Gray
Write-Host '     "alert_id": "{{alert.id}}",' -ForegroundColor Gray
Write-Host '     "alert_name": "{{rule.name}}",' -ForegroundColor Gray
Write-Host '     "service": "all",' -ForegroundColor Gray
Write-Host '     "error_count": "{{context.hits}}",' -ForegroundColor Gray
Write-Host '     "severity": "high",' -ForegroundColor Gray
Write-Host '     "timestamp": "{{date}}",' -ForegroundColor Gray
Write-Host '     "time_range": "1m"' -ForegroundColor Gray
Write-Host '   }' -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter when you've created the second alert rule"

# Step 5: Test the alerts
Write-Host ""
Write-Host "[Step 5/6] Test the Alerts" -ForegroundColor Yellow
Write-Host ""
Write-Host "Let's trigger some errors to test the alert system."
Write-Host ""
Write-Host "Running test error generator..." -ForegroundColor Cyan

try {
    $result = & uv run scripts/generate_test_errors.py 2>&1
    Write-Host $result -ForegroundColor Gray
    Write-Host ""
    Write-Host "  [OK] Generated test errors" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to generate test errors: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Waiting 90 seconds for Kibana to detect errors and trigger alerts..." -ForegroundColor Cyan
Write-Host "(Kibana checks every 1 minute)" -ForegroundColor Gray

for ($i = 90; $i -gt 0; $i -= 10) {
    Write-Host "  $i seconds remaining..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# Step 6: Verify
Write-Host ""
Write-Host "[Step 6/6] Verify Alert Execution" -ForegroundColor Yellow
Write-Host ""
Write-Host "Check the following to verify alerts are working:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. In Kibana UI:" -ForegroundColor Yellow
Write-Host "   - Go to Stack Management > Rules and Connectors > Rules" -ForegroundColor White
Write-Host "   - Click on your rule name" -ForegroundColor White
Write-Host "   - Check the 'Execution history' tab" -ForegroundColor White
Write-Host "   - You should see recent executions with 'active' status" -ForegroundColor White
Write-Host ""
Write-Host "2. In Observability Server logs:" -ForegroundColor Yellow
Write-Host "   - Look for lines like:" -ForegroundColor White
Write-Host "     [Kibana Alert] Received alert: High Error Rate - Resume Agent" -ForegroundColor Gray
Write-Host "     [Kibana Alert] Triggering error analysis..." -ForegroundColor Gray
Write-Host "     [Error Analysis] Analysis complete..." -ForegroundColor Gray
Write-Host ""
Write-Host "3. Check recent events:" -ForegroundColor Yellow

try {
    $events = Invoke-RestMethod -Uri "$obsServerUrl/events/recent?limit=5" -Method Get
    $alertEvents = $events | Where-Object { $_.hook_event_type -eq "KibanaAlert" -or $_.hook_event_type -eq "ErrorAnalysisComplete" }

    if ($alertEvents.Count -gt 0) {
        Write-Host ""
        Write-Host "  [OK] Found $($alertEvents.Count) recent alert/analysis events:" -ForegroundColor Green
        foreach ($event in $alertEvents) {
            Write-Host "    - $($event.hook_event_type) from $($event.source_app) at $(([DateTimeOffset]::FromUnixTimeMilliseconds($event.timestamp)).ToString('HH:mm:ss'))" -ForegroundColor White
        }
    } else {
        Write-Host "  [WARNING] No alert events found yet. Wait a bit longer and check Kibana execution history." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] Could not fetch events: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Your Kibana alerts are now configured for automatic error detection." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Monitor Kibana execution history to see when alerts trigger" -ForegroundColor White
Write-Host "  - Check observability server logs for analysis results" -ForegroundColor White
Write-Host "  - Adjust thresholds in Kibana if needed (too sensitive/not sensitive enough)" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: docker/elk/kibana-alerts.md" -ForegroundColor Gray
Write-Host ""
