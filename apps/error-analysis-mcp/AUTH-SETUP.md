# Authentication Setup for Error Analysis MCP Server

## Overview

The error-analysis-mcp server supports optional Bearer token authentication for HTTP transports (streamable-http, SSE).

**Authentication is:**
- ✅ **Optional** - Disabled by default for local development
- ✅ **Recommended** for production deployments
- ✅ **Required** when exposing server to network/internet
- ❌ **Not used** for stdio transport (Claude Desktop)

---

## Quick Setup

### Step 1: Generate a Secure Token

**PowerShell (Windows):**
```powershell
# Generate random 32-byte hex token
-join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

**Or use a simple UUID:**
```powershell
[guid]::NewGuid().ToString("N")
```

**Linux/macOS:**
```bash
openssl rand -hex 32
```

**Example token:**
```
a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4b8f5a2c9d6e3f1a7c4b9d6e2f8a5c3d1
```

### Step 2: Configure Environment Variables

**Create `.env` file:**
```bash
# Copy example
cp apps/error-analysis-mcp/.env.example apps/error-analysis-mcp/.env

# Edit with your token
```

**Add to `.env`:**
```env
MCP_REQUIRE_AUTH=true
MCP_AUTH_TOKEN=a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4b8f5a2c9d6e3f1a7c4b9d6e2f8a5c3d1
```

### Step 3: Start Server with Authentication

```powershell
.\apps\error-analysis-mcp\start-server.ps1
```

**Expected output:**
```
🚀 Starting Error Analysis MCP Server (HTTP Streamable)
📡 Transport: HTTP Streamable
🌐 Port: 8080
🔒 Authentication: ENABLED
💡 N8N Connection: http://localhost:8080/mcp
```

---

## N8N Configuration

### Without Authentication (Default)

```
Connection Type: HTTP Streamable
HTTP Streamable URL: http://host.docker.internal:8080/mcp
Additional Headers: (none)
```

### With Authentication Enabled

```
Connection Type: HTTP Streamable
HTTP Streamable URL: http://host.docker.internal:8080/mcp
Additional Headers:
  Authorization: Bearer a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4b8f5a2c9d6e3f1a7c4b9d6e2f8a5c3d1
```

---

## Testing Authentication

### Test Unauthenticated Request (Should Fail)

```powershell
curl -Method POST `
  -Uri "http://localhost:8080/mcp" `
  -Headers @{
    "Accept" = "application/json, text/event-stream"
    "Content-Type" = "application/json"
  } `
  -Body '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
```

**Expected response (401):**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Missing Authorization header"
  },
  "id": null
}
```

### Test Authenticated Request (Should Succeed)

```powershell
curl -Method POST `
  -Uri "http://localhost:8080/mcp" `
  -Headers @{
    "Accept" = "application/json, text/event-stream"
    "Content-Type" = "application/json"
    "Authorization" = "Bearer a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4b8f5a2c9d6e3f1a7c4b9d6e2f8a5c3d1"
  } `
  -Body '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
```

**Expected response (200):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {...},
    "serverInfo": {
      "name": "error-analysis",
      "version": "2.13.1"
    }
  },
  "id": 1
}
```

---

## Security Best Practices

### Development
- ✅ Authentication optional (disabled by default)
- ✅ Use localhost binding (127.0.0.1)
- ✅ Simple UUID tokens acceptable

### Production
- ✅ **Always enable authentication** (`MCP_REQUIRE_AUTH=true`)
- ✅ **Use cryptographically secure tokens** (32+ bytes)
- ✅ **Store tokens in environment variables** (never commit to git)
- ✅ **Use HTTPS/TLS** for network access
- ✅ **Rotate tokens periodically** (every 90 days recommended)
- ✅ **Bind to specific interface** (not 0.0.0.0)

### Token Management

**DO:**
- Generate unique tokens per environment (dev, staging, prod)
- Store in `.env` files (added to `.gitignore`)
- Use password manager or secrets vault
- Rotate after security incidents

**DON'T:**
- Hardcode tokens in source code
- Commit tokens to version control
- Share tokens via email/chat
- Use weak or predictable tokens

---

## Troubleshooting

### "Server misconfigured: MCP_AUTH_TOKEN not set"

**Problem**: `MCP_REQUIRE_AUTH=true` but no token configured

**Solution**:
```bash
# Set token in .env
MCP_AUTH_TOKEN=your-generated-token-here
```

### "Invalid authentication token"

**Problem**: Token in N8N doesn't match server token

**Solution**:
1. Check `.env` file for correct token
2. Verify N8N header: `Authorization: Bearer <token>`
3. Ensure no extra spaces or newlines in token

### "Missing Authorization header"

**Problem**: N8N not sending authentication header

**Solution**:
1. Add header in N8N MCP Client configuration:
   ```
   Authorization: Bearer your-token-here
   ```
2. Verify header name is exactly `Authorization` (case-sensitive)

### N8N Connection Works Without Token

**Problem**: Server not enforcing authentication

**Solution**:
1. Check server logs for "Authentication: ENABLED"
2. Verify `.env` has `MCP_REQUIRE_AUTH=true`
3. Restart server after changing `.env`

---

## Disabling Authentication

For local development, you can disable authentication:

**Remove from `.env` (or set to false):**
```env
MCP_REQUIRE_AUTH=false
```

**Or start without .env file:**
```powershell
# Authentication disabled by default
uv run apps/error-analysis-mcp/error_analysis_mcp.py --transport streamable-http --port 8080
```

---

## Integration Examples

### Claude Desktop (No Auth Needed)

Claude Desktop uses stdio transport, which doesn't support HTTP authentication:

```json
{
  "mcpServers": {
    "error-analysis": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "apps/error-analysis-mcp/error_analysis_mcp.py"]
    }
  }
}
```

### N8N Workflow (With Auth)

1. **Create MCP Client credentials**:
   - Connection Type: `HTTP Streamable`
   - URL: `http://host.docker.internal:8080/mcp`
   - Additional Headers:
     - Key: `Authorization`
     - Value: `Bearer a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4...`

2. **Add to AI Agent workflow**:
   - AI Agent → Tools → MCP Client
   - Select credentials
   - Tools: All

### curl Testing (With Auth)

```powershell
$TOKEN = "a7e4f9c2b8d6e3a1f5c8b2d9e6a3f7c4b8f5a2c9d6e3f1a7c4b9d6e2f8a5c3d1"

curl -Method POST `
  -Uri "http://localhost:8080/mcp" `
  -Headers @{
    "Authorization" = "Bearer $TOKEN"
    "Accept" = "application/json, text/event-stream"
    "Content-Type" = "application/json"
  } `
  -Body '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ELASTICSEARCH_URL` | No | `http://localhost:9200` | Elasticsearch endpoint |
| `MCP_REQUIRE_AUTH` | No | `false` | Enable authentication |
| `MCP_AUTH_TOKEN` | Conditional | - | Bearer token (required if `MCP_REQUIRE_AUTH=true`) |

---

## Next Steps

1. ✅ Generate secure token
2. ✅ Configure `.env` file
3. ✅ Start server with authentication
4. ✅ Update N8N MCP Client with Authorization header
5. ✅ Test connection
6. ✅ Store token securely

For production deployment, also consider:
- TLS/HTTPS termination (nginx reverse proxy)
- Token rotation schedule
- Audit logging
- Rate limiting
- IP whitelisting
