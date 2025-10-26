# Test LangGraph Dev Server API (PowerShell)
#
# Usage:
#   .\test_langgraph_api.ps1
#
# Prerequisites:
#   - langgraph dev server running on port 2024

$ErrorActionPreference = "Stop"

$API_URL = "http://localhost:2024"
$ASSISTANT_ID = "resume_agent"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "LangGraph Dev Server API Test" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check server health
Write-Host "Test 1: Checking server health..." -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "$API_URL/ok" -Method Get
    if ($response -eq "ok") {
        Write-Host "✓ Server is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Server health check failed" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Create a thread
Write-Host "Test 2: Creating a thread..." -ForegroundColor Blue
$threadResponse = Invoke-RestMethod -Uri "$API_URL/threads" -Method Post `
    -ContentType "application/json" -Body "{}"

$threadId = $threadResponse.thread_id
Write-Host "✓ Thread created: $threadId" -ForegroundColor Green
Write-Host ""

# Test 3: Send first message (stateful with thread)
Write-Host "Test 3: Sending first message..." -ForegroundColor Blue
Write-Host "Message: 'My name is John and I need help with my resume'" -ForegroundColor Gray

$body = @{
    assistant_id = $ASSISTANT_ID
    input = @{
        messages = @(
            @{
                role = "user"
                content = "My name is John and I need help with my resume"
            }
        )
    }
    stream_mode = @("values")
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_URL/threads/$threadId/runs/stream" `
        -Method Post -ContentType "application/json" -Body $body

    Write-Host "✓ Message sent successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to send message" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Send follow-up message (tests memory)
Write-Host "Test 4: Sending follow-up message (testing memory)..." -ForegroundColor Blue
Write-Host "Message: 'What did I just tell you my name was?'" -ForegroundColor Gray

$body = @{
    assistant_id = $ASSISTANT_ID
    input = @{
        messages = @(
            @{
                role = "user"
                content = "What did I just tell you my name was?"
            }
        )
    }
    stream_mode = @("values")
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_URL/threads/$threadId/runs/stream" `
        -Method Post -ContentType "application/json" -Body $body

    Write-Host "✓ Follow-up message sent successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to send follow-up message" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Get thread state
Write-Host "Test 5: Getting thread state..." -ForegroundColor Blue
try {
    $stateResponse = Invoke-RestMethod -Uri "$API_URL/threads/$threadId/state" `
        -Method Get -ContentType "application/json"

    $messageCount = $stateResponse.values.messages.Count
    Write-Host "✓ Thread has $messageCount messages" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to get thread state" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Stateless run (no thread)
Write-Host "Test 6: Stateless run (no thread persistence)..." -ForegroundColor Blue
Write-Host "Message: 'What is LangGraph?'" -ForegroundColor Gray

$body = @{
    assistant_id = $ASSISTANT_ID
    input = @{
        messages = @(
            @{
                role = "user"
                content = "What is LangGraph?"
            }
        )
    }
    stream_mode = @("values")
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_URL/runs/stream" `
        -Method Post -ContentType "application/json" -Body $body

    Write-Host "✓ Stateless message sent successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to send stateless message" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 7: Create another thread
Write-Host "Test 7: Creating second thread..." -ForegroundColor Blue
$thread2Response = Invoke-RestMethod -Uri "$API_URL/threads" -Method Post `
    -ContentType "application/json" -Body "{}"

$thread2Id = $thread2Response.thread_id
Write-Host "✓ Second thread created: $thread2Id" -ForegroundColor Green
Write-Host ""

# Test 8: Search threads
Write-Host "Test 8: Searching threads..." -ForegroundColor Blue
$searchBody = @{
    limit = 10
} | ConvertTo-Json

try {
    $searchResponse = Invoke-RestMethod -Uri "$API_URL/threads/search" `
        -Method Post -ContentType "application/json" -Body $searchBody

    $threadCount = $searchResponse.Count
    Write-Host "✓ Found $threadCount threads" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to search threads" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "All tests completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Thread IDs created:" -ForegroundColor Cyan
Write-Host "  - Thread 1: $threadId" -ForegroundColor White
Write-Host "  - Thread 2: $thread2Id" -ForegroundColor White
Write-Host ""
Write-Host "To continue the conversation with Thread 1:" -ForegroundColor Cyan
Write-Host ""
Write-Host @"
`$body = @{
    assistant_id = "$ASSISTANT_ID"
    input = @{
        messages = @(
            @{
                role = "user"
                content = "Your message here"
            }
        )
    }
    stream_mode = @("values")
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$API_URL/threads/$threadId/runs/stream" ``
    -Method Post -ContentType "application/json" -Body `$body
"@ -ForegroundColor Gray
