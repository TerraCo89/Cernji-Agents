# 🌅 Morning Startup Checklist

Your daily startup routine to get all systems ready.

## ✅ Already Running (Auto-Start with Docker)

These services start automatically when Docker starts:

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **N8N** | 5678 | http://localhost:5678 | ✅ Auto-start |
| **Elasticsearch** | 9200 | http://localhost:9200 | ✅ Auto-start |
| **Kibana** | 5601 | http://localhost:5601 | ✅ Auto-start |
| **Qdrant** | 6333 | http://localhost:6333 | ✅ Auto-start |
| **PostgreSQL** | 5432 | localhost:5432 | ✅ Auto-start |
| **Redis** | 6379 | localhost:6379 | ✅ Auto-start |

**No action needed** - These are ready when you turn on your PC.

---

## 📋 Manual Startup Steps

### Option 1: For N8N Error Workflow Only (Quick Start)

**Single command to start error-analysis MCP server:**

```powershell
.\apps\error-analysis-mcp\start-server.ps1
```

**Or manually:**
```powershell
uv run apps/error-analysis-mcp/error_analysis_mcp.py --transport streamable-http --port 8080
```

**Expected output:**
```
🚀 Starting Error Analysis MCP Server
📡 Transport: streamable-http
🌐 HTTP Server: http://127.0.0.1:8080/mcp
💡 N8N Connection URL: http://127.0.0.1:8080/mcp
```

**N8N Configuration:**
- Connection Type: `HTTP Streamable`
- URL: `http://localhost:8080/mcp`
- Tools: `All` (or select specific error analysis tools)

---

### Option 2: Full System Startup (All Apps)

**Start everything with one command:**

```powershell
.\scripts\start-system.ps1
```

**This starts:**
- Resume Agent LangGraph → http://localhost:2024
- Agent Chat UI → http://localhost:3000
- Observability Server → http://localhost:4000
- Web Dashboard → http://localhost:5173

---

## 🔍 Verification Checklist

After startup, verify all services are running:

```powershell
# Quick health check
curl http://localhost:8080/mcp  # Error Analysis MCP
curl http://localhost:9200      # Elasticsearch
curl http://localhost:5678      # N8N
```

**Or open in browser:**
- N8N: http://localhost:5678
- Kibana: http://localhost:5601
- LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

---

## 🛑 Shutdown

### Stop MCP Server
Press `Ctrl+C` in the terminal running the error-analysis MCP server

### Stop All Apps
```powershell
.\scripts\stop-system.ps1
```

### Stop Docker Services
```powershell
docker-compose -f docker/elk/docker-compose.yml down
```

---

## 🚨 Troubleshooting

### "Port 8080 already in use"
```powershell
# Find what's using the port
netstat -ano | findstr :8080

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### "Error Analysis MCP not connecting to N8N"
**Docker Networking Issue:**
- If N8N is in Docker, use: `http://host.docker.internal:8080/mcp`
- If on same host, use: `http://localhost:8080/mcp`

**Verify server is running:**
```powershell
curl -H "Accept: application/json, text/event-stream" http://localhost:8080/mcp
```

### "Elasticsearch connection refused"
```powershell
# Check if Elasticsearch is running
docker ps | findstr elasticsearch

# If not running, start ELK stack
cd docker/elk
docker-compose up -d
```

---

## 📝 Morning Routine Summary

**Minimal Setup (N8N Error Workflow):**
1. Turn on PC (Docker auto-starts N8N, Elasticsearch, etc.)
2. Open PowerShell
3. Run: `.\apps\error-analysis-mcp\start-server.ps1`
4. Open N8N: http://localhost:5678
5. ✅ Ready to work

**Full Development Setup:**
1. Turn on PC
2. Run: `.\scripts\start-system.ps1`
3. Run: `.\apps\error-analysis-mcp\start-server.ps1` (separate terminal)
4. ✅ All systems ready

**Estimated startup time:** ~30 seconds (after PC boot)

---

## 🔗 Quick Links

- **N8N Workflows:** http://localhost:5678/workflows
- **Kibana Errors:** http://localhost:5601/app/discover
- **LangGraph Studio:** https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- **Agent Chat UI:** http://localhost:3000
- **Observability Dashboard:** http://localhost:5173

---

## 💡 Notes

- **For Claude Desktop:** MCP servers run via `.mcp.json` (stdio transport) - no manual startup needed
- **For N8N:** Use HTTP Streamable transport (manual startup with `start-server.ps1`)
- **Docker services:** Auto-start with Docker Desktop
- **Node services:** Manual startup via `start-system.ps1`
