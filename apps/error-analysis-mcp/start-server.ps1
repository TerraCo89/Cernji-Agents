# Start Error Analysis MCP Server for N8N
# Runs with HTTP Streamable transport on port 8080

Write-Host ""
Write-Host "=== Starting Error Analysis MCP Server ===" -ForegroundColor Green
Write-Host "Transport: HTTP Streamable" -ForegroundColor Cyan
Write-Host "Port: 8080" -ForegroundColor Cyan
Write-Host "N8N Connection URL: http://localhost:8080/mcp" -ForegroundColor Yellow
Write-Host ""

# Change to the error-analysis-mcp directory (where this script is located)
Set-Location $PSScriptRoot

# Run the server
uv run error_analysis_mcp.py --transport streamable-http --port 8080
