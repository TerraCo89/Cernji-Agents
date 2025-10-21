# Quick Start: Multi-App Architecture

**Goal**: Get the complete multi-app system running in under 10 minutes.

## Prerequisites

Ensure you have these installed:

- **Python 3.10+** with UV package manager
- **Bun** (JavaScript runtime) - https://bun.sh
- **Git** (for cloning reference repository)
- **Windows PowerShell** (or Bash if on Linux/macOS)

```powershell
# Verify installations
uv --version      # Should show UV version
bun --version     # Should show Bun version
python --version  # Should show Python 3.10+
```

## Step 1: Clone Reference Repository (One-Time Setup)

```powershell
# From repository root
cd D:\source\Cernji-Agents

# Clone Disler's observability reference (temporary)
git clone https://github.com/disler/claude-code-hooks-multi-agent-observability.git temp-observability-reference
```

## Step 2: Copy Observability Server

```powershell
# Copy observability-server files
cp -r temp-observability-reference/apps/server/* apps/observability-server/

# Update database path in db.ts
# Change: './data/events.db'
# To:     '../../data/events.db'

# Install dependencies
cd apps/observability-server
bun install
```

**Verify**:

```powershell
# Test server starts
bun run src/index.ts

# Should see: "Server running on port 4000"
# Ctrl+C to stop
```

## Step 3: Copy Web Client

```powershell
# From repository root
cp -r temp-observability-reference/apps/client/* apps/client/

# Install dependencies
cd apps/client
bun install
```

**Verify**:

```powershell
# Test client starts
bun run dev

# Should see: "Local: http://localhost:5173"
# Open browser to http://localhost:5173
# Ctrl+C to stop
```

## Step 4: Copy Hook Scripts

```powershell
# From repository root
cp -r temp-observability-reference/.claude/hooks/* .claude/hooks/

# Create root .claude/settings.json
# (Copy from template in research.md or REFACTORING_PLAN.md)
```

**Hook Configuration** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PreToolUse --summarize"
      }]
    }],
    "PostToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PostToolUse --summarize"
      }]
    }]
  }
}
```

## Step 5: Update Resume Agent Paths

```powershell
# Edit apps/resume-agent/resume_agent.py
# Update PROJECT_ROOT calculation to account for new location:

# Change:
# PROJECT_ROOT = Path(__file__).resolve().parent

# To:
# PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# (Goes up 3 levels: resume_agent.py -> apps/resume-agent -> apps -> root)
```

**Verify**:

```python
# In resume_agent.py, add debug print after PROJECT_ROOT
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"RESUMES_DIR: {RESUMES_DIR}")

# Should show:
# PROJECT_ROOT: D:\source\Cernji-Agents
# DATA_DIR: D:\source\Cernji-Agents\data
# RESUMES_DIR: D:\source\Cernji-Agents\resumes
```

## Step 6: Update MCP Configuration

```json
// .mcp.json (repository root)
{
  "mcpServers": {
    "resume-agent": {
      "command": "uv",
      "args": ["run", "apps/resume-agent/resume_agent.py"],
      "env": {}
    }
  }
}
```

## Step 7: Create System Management Scripts

**start-system.ps1** (PowerShell):

```powershell
# scripts/start-system.ps1

Write-Host "Starting Multi-App System..." -ForegroundColor Green

# Start observability server
Write-Host "Starting observability server..." -ForegroundColor Yellow
cd apps/observability-server
$serverJob = Start-Job { bun run src/index.ts }

# Start web client
Write-Host "Starting web client..." -ForegroundColor Yellow
cd ../client
$clientJob = Start-Job { bun run dev }

# Wait for startup
Start-Sleep -Seconds 5

# Check if servers are running
if (Test-NetConnection -ComputerName localhost -Port 4000 -InformationLevel Quiet) {
    Write-Host "✓ Observability Server: http://localhost:4000" -ForegroundColor Green
} else {
    Write-Host "✗ Observability Server failed to start" -ForegroundColor Red
}

if (Test-NetConnection -ComputerName localhost -Port 5173 -InformationLevel Quiet) {
    Write-Host "✓ Web Dashboard: http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "✗ Web Client failed to start" -ForegroundColor Red
}

Write-Host "`nMCP Server (resume-agent) must be started manually via Claude Desktop" -ForegroundColor Cyan
```

**stop-system.ps1** (PowerShell):

```powershell
# scripts/stop-system.ps1

Write-Host "Stopping Multi-App System..." -ForegroundColor Yellow

# Kill processes on ports 4000 and 5173
$processes = Get-NetTCPConnection -LocalPort 4000,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Select-Object -Unique

foreach ($proc in $processes) {
    Stop-Process -Id $proc -Force
    Write-Host "Killed process $proc" -ForegroundColor Green
}

Write-Host "System stopped" -ForegroundColor Green
```

## Step 8: Start the Complete System

```powershell
# From repository root
./scripts/start-system.ps1

# Expected output:
# Starting Multi-App System...
# Starting observability server...
# Starting web client...
# ✓ Observability Server: http://localhost:4000
# ✓ Web Dashboard: http://localhost:5173
```

## Step 9: Verify Observability

1. **Open dashboard**: http://localhost:5173
2. **Open Claude Desktop** (resume-agent MCP server should auto-connect)
3. **Run a command**: `/career:analyze-job https://example.com/job`
4. **Check dashboard**: Events should appear in real-time

**What to expect**:

- PreToolUse events when Claude calls tools
- PostToolUse events after tools complete
- UserPromptSubmit events when you send messages
- All events labeled with `source_app: "resume-agent"`

## Step 10: Test Resume Agent Functionality

```bash
# In Claude Desktop, run:
/career:analyze-job https://japan-dev.com/jobs/cookpad/conversational-ai-engineer

# Should work identically to before migration
# Verify outputs go to: job-applications/Cookpad_Conversational_AI_Engineer/
```

## Troubleshooting

### Issue: Observability server won't start

**Symptom**: Port 4000 already in use
**Solution**:

```powershell
# Find and kill process using port 4000
Get-NetTCPConnection -LocalPort 4000 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
```

### Issue: Resume agent can't find data files

**Symptom**: `FileNotFoundError: data/resume_agent.db`
**Solution**: Verify PROJECT_ROOT path calculation in resume_agent.py

```python
# Should resolve to repository root
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
# Expected: D:\source\Cernji-Agents (not D:\source\Cernji-Agents\apps\resume-agent)
```

### Issue: Hooks not sending events

**Symptom**: Dashboard shows no events
**Solution**: Check observability server is running and hook script has no errors

```powershell
# Test hook script manually
echo '{"tool_name": "test"}' | uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PreToolUse

# Should POST to http://localhost:4000/events
# Check server logs for incoming request
```

### Issue: WebSocket won't connect

**Symptom**: Dashboard shows "Disconnected"
**Solution**: Verify observability server is running and WebSocket endpoint is exposed

```powershell
# Test WebSocket connection
# In browser console (http://localhost:5173):
const ws = new WebSocket('ws://localhost:4000/stream');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', event.data);
```

## Cleanup (Optional)

```powershell
# Remove reference repository after migration is complete
rm -r temp-observability-reference
```

## Next Steps

Once the system is running:

1. ✅ **Test all resume agent commands**: Verify `/career:*` commands work
2. ✅ **Monitor events**: Watch dashboard while running commands
3. ✅ **Add translation-teacher** (Phase 4): Follow same pattern as resume-agent
4. ✅ **Write tests**: Add contract tests for observability API
5. ✅ **Update documentation**: Update root README.md and CLAUDE.md

## Summary

**Time to complete**: ~10 minutes

**System Components Running**:

- ✅ Observability Server (port 4000) - Event collection and WebSocket
- ✅ Web Client (port 5173) - Real-time dashboard
- ✅ Resume Agent (MCP) - Career application workflows
- ✅ Root-level hooks - Send events on tool use

**Verification Checklist**:

- [ ] Dashboard shows "Connected" status
- [ ] Running a slash command generates events
- [ ] Events appear in dashboard within 1 second
- [ ] Resume agent slash commands work identically to before
- [ ] Data files accessible from new resume-agent location

**You're done!** 🎉

The multi-app architecture is now operational. All apps run independently with shared observability.
