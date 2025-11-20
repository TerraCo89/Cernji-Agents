# Quick Authentication Reference

## TL;DR

**Development (No Auth)**:
```powershell
.\apps\error-analysis-mcp\start-server.ps1
```

**Production (With Auth)**:
```powershell
# 1. Generate token
$TOKEN = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# 2. Set environment
$env:MCP_REQUIRE_AUTH="true"
$env:MCP_AUTH_TOKEN=$TOKEN

# 3. Start server
.\apps\error-analysis-mcp\start-server.ps1

# 4. Use in N8N
# Authorization: Bearer $TOKEN
```

---

## N8N Configuration

### Without Auth (Default)
```
URL: http://host.docker.internal:8080/mcp
Headers: (none)
```

### With Auth
```
URL: http://host.docker.internal:8080/mcp
Headers:
  Authorization: Bearer a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4...
```

---

## Testing

**Test without auth:**
```powershell
curl http://localhost:8080/mcp
# Should work if auth disabled
```

**Test with auth:**
```powershell
curl -Method POST `
  -Uri "http://localhost:8080/mcp" `
  -Headers @{
    "Authorization" = "Bearer YOUR_TOKEN_HERE"
    "Accept" = "application/json, text/event-stream"
  }
```

---

## N8N Compatibility Notes

### Known Issue: toolCallId Parameter (v1.118.2+)

N8N MCP Client node includes metadata fields in tool calls, causing validation errors. This server includes defensive middleware to handle this automatically.

**Affected N8N versions**: 1.118.2+
**Status**: Fixed server-side via middleware (DEV-249)
**Upstream**: https://community.n8n.io/t/mcp-client-node-now-includes-toolcallid-in-tool-calls-bug/219307

**What was fixed**:
- Server now strips `toolCallId`, `__fromNode`, `__outputIndex` before validation
- No N8N configuration changes needed
- Works with both authenticated and unauthenticated modes

**Verification**:
1. Create N8N workflow with AI Agent + MCP Client Tool
2. Configure: `http://localhost:8080/mcp` (or `host.docker.internal`)
3. Test `search_errors` tool - should work without validation errors

---

## Full Documentation

See [AUTH-SETUP.md](./AUTH-SETUP.md) for complete setup guide.
