# Server Management Scripts

This directory contains scripts to start and stop the LangGraph Resume Agent server.

## Available Scripts

### Start Server

Starts the LangGraph development server with automatic dependency checking and environment validation.

**Windows PowerShell (Recommended):**
```powershell
.\start-server.ps1
```

**Windows Batch:**
```cmd
start-server.bat
```

**Unix/Linux/macOS:**
```bash
./start-server.sh
```

**Features:**
- ✅ Checks for `.env` file
- ✅ Verifies dependencies are installed
- ✅ Warns if port 2024 is already in use
- ✅ Displays server URLs (API, Studio, Docs)
- ✅ Runs `langgraph dev` in foreground
- ✅ Graceful shutdown on Ctrl+C

### Stop Server

Stops the running LangGraph server gracefully.

**Windows PowerShell (Recommended):**
```powershell
.\stop-server.ps1
```

**Windows Batch:**
```cmd
stop-server.bat
```

**Unix/Linux/macOS:**
```bash
./stop-server.sh
```

**Features:**
- ✅ Finds process listening on port 2024
- ✅ Attempts graceful shutdown (SIGTERM)
- ✅ Force kills if graceful shutdown fails (SIGKILL)
- ✅ Verifies port is freed
- ✅ Shows process details before stopping

## Quick Start

### 1. First Time Setup

```bash
# Ensure .env is configured
cp .env.example .env
# Edit .env and add your API keys

# Install dependencies
python -m pip install -e .
```

### 2. Start Server

**Windows:**
```powershell
.\start-server.ps1
```

**Unix/Linux/macOS:**
```bash
./start-server.sh
```

Server will be available at:
- **API**: http://127.0.0.1:2024
- **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- **API Docs**: http://127.0.0.1:2024/docs

### 3. Stop Server

**Windows:**
```powershell
.\stop-server.ps1
```

**Unix/Linux/macOS:**
```bash
./stop-server.sh
```

Or press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

### Port Already in Use

**Problem:** Port 2024 is already in use

**Solution:**
```powershell
# Windows PowerShell
Get-NetTCPConnection -LocalPort 2024
# Kill the process manually if needed
Stop-Process -Id <PID> -Force
```

```bash
# Unix/Linux/macOS
lsof -i :2024
# Kill the process manually if needed
kill -9 <PID>
```

### Dependencies Not Found

**Problem:** `ModuleNotFoundError: No module named 'anthropic'`

**Solution:**
```bash
# Reinstall dependencies
python -m pip install -e .

# Or using UV
uv sync
```

### Script Won't Execute (Unix/Linux/macOS)

**Problem:** `Permission denied: ./start-server.sh`

**Solution:**
```bash
# Make scripts executable
chmod +x start-server.sh stop-server.sh
```

### PowerShell Execution Policy Error

**Problem:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run with bypass flag
powershell -ExecutionPolicy Bypass -File .\start-server.ps1

# Or permanently change policy (requires admin)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Manual Commands

If you prefer not to use the scripts:

### Start Manually
```bash
cd apps/resume-agent-langgraph
langgraph dev
```

### Stop Manually

**Windows:**
```cmd
# Find process on port 2024
netstat -ano | findstr ":2024"
# Kill process by PID
taskkill /F /PID <PID>
```

**Unix/Linux/macOS:**
```bash
# Find and kill process on port 2024
lsof -ti:2024 | xargs kill -9
```

## Integration with Agent Chat UI

After starting the LangGraph server, you can connect the Agent Chat UI:

```bash
# In a new terminal
cd apps/agent-chat-ui
pnpm install  # first time only
pnpm dev      # starts on port 3000
```

See [apps/agent-chat-ui/SETUP.md](../agent-chat-ui/SETUP.md) for details.

## Architecture

```
start-server.ps1/bat/sh
       ↓
   Check .env exists
       ↓
   Check dependencies
       ↓
   langgraph dev
       ↓
   Server runs on port 2024
       ↓
   [Ctrl+C or stop-server script]
       ↓
   Graceful shutdown
```

## Resources

- **LangGraph CLI Docs**: https://langchain-ai.github.io/langgraph/cloud/reference/cli
- **Resume Agent README**: [README.md](README.md)
- **Agent Chat UI Setup**: [../agent-chat-ui/SETUP.md](../agent-chat-ui/SETUP.md)
