# Phase 0 Research: Multi-App Architecture Refactoring

**Feature**: Multi-App Architecture Refactoring
**Date**: 2025-10-21
**Status**: Complete

## Research Questions

This document resolves all "NEEDS CLARIFICATION" items from plan.md Technical Context and provides best practices research for technology choices.

---

## Q1: Testing Framework and Strategy

**Question**: What testing framework and strategy should be used for multi-app monorepo with Python, TypeScript, and Vue 3 applications?

### Decision

**Per-App Testing Strategy** - Each application uses its native testing framework:

1. **resume-agent (Python)**:
   - Framework: **pytest**
   - Contract tests: pytest + MCP test utilities
   - Unit tests: pytest with fixtures
   - Integration tests: pytest with temporary databases

2. **observability-server (TypeScript/Bun)**:
   - Framework: **Bun's built-in test runner** (`bun test`)
   - API tests: Bun test + supertest-like assertions
   - Database tests: In-memory SQLite for speed
   - WebSocket tests: Mock WebSocket clients

3. **client (Vue 3)**:
   - Framework: **Vitest** (Vite-native, fast)
   - Component tests: Vitest + Vue Test Utils
   - E2E tests: Playwright (optional, later phase)

4. **System Integration Tests** (root-level):
   - Framework: **pytest** (can orchestrate all apps)
   - Scope: End-to-end workflows across apps
   - Location: `tests/integration/` at repo root

### Rationale

- **Native frameworks**: Each app uses its ecosystem's standard (pytest for Python, Bun test for TypeScript, Vitest for Vue)
- **No shared testing infrastructure**: Aligns with multi-app isolation principle
- **Proven tools**: All frameworks are industry-standard and well-documented
- **Fast feedback**: Bun test and Vitest are extremely fast for local development

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Single testing framework (e.g., Jest for all) | Would require awkward Python→JS interop, violates app isolation |
| No integration tests | Wouldn't catch cross-app communication issues |
| Heavy E2E from start | Premature - can add Playwright later if needed |

### Implementation Notes

- Each app's tests run independently: `cd apps/resume-agent && pytest`, `cd apps/observability-server && bun test`, `cd apps/client && npm run test`
- CI/CD runs all test suites in parallel
- System integration tests run after all unit/contract tests pass

---

## Q2: Path Resolution Strategy

**Question**: How should apps resolve paths to shared root directories (data/, resumes/, job-applications/) from different locations in apps/?

### Decision

**Absolute Path Resolution with PROJECT_ROOT Constant**

Each app defines a `PROJECT_ROOT` constant that points to repository root:

```python
# Python (resume-agent)
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESUMES_DIR = PROJECT_ROOT / "resumes"
```

```typescript
// TypeScript (observability-server)
import path from 'path';
const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const DATA_DIR = path.join(PROJECT_ROOT, 'data');
```

### Rationale

- **Reliability**: Absolute paths work from any working directory
- **Clarity**: Explicit path calculation shows directory structure
- **Testable**: Easy to override in tests with mock PROJECT_ROOT
- **No magic**: Doesn't rely on environment variables or config files

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Relative paths (../../data/) | Breaks if working directory changes |
| Environment variables (DATA_DIR env var) | Adds configuration complexity, harder to discover |
| Symbolic links | Platform-specific, error-prone on Windows |
| Config file with paths | Over-engineering for simple path resolution |

### Implementation Notes

- Each app calculates PROJECT_ROOT once at startup
- Paths are validated on startup (fail fast if directories missing)
- Tests can override PROJECT_ROOT to use temporary directories

---

## Q3: WebSocket Message Format

**Question**: What message format and protocol should hooks use to send events to observability-server?

### Decision

**JSON over HTTP POST + Server-Sent Events (SSE) for Dashboard**

1. **Hook → Server (Event Ingestion)**:
   - Protocol: HTTP POST to `/events`
   - Format: JSON with structured schema
   - Non-blocking: Hooks timeout after 100ms, don't fail agent on error

2. **Server → Dashboard (Event Broadcasting)**:
   - Protocol: WebSocket (`ws://localhost:4000/stream`)
   - Format: JSON event stream
   - Reconnection: Client auto-reconnects on disconnect

### Message Schema

```typescript
// Event ingestion (POST /events)
{
  "timestamp": "2025-10-21T10:30:45.123Z",
  "source_app": "resume-agent",
  "event_type": "PreToolUse" | "PostToolUse" | "UserPromptSubmit" | ...,
  "tool_name": "mcp__sqlite__query",
  "summary": "Querying portfolio_library table for examples matching RAG",
  "session_id": "uuid-v4",
  "metadata": {
    // Optional additional context
  }
}

// WebSocket broadcast (ws://localhost:4000/stream)
{
  "id": 123,
  "timestamp": "2025-10-21T10:30:45.123Z",
  "source_app": "resume-agent",
  "event_type": "PreToolUse",
  "tool_name": "mcp__sqlite__query",
  "summary": "Querying portfolio_library table...",
  "session_id": "uuid-v4"
}
```

### Rationale

- **HTTP POST**: Simpler than WebSocket for one-way communication from hooks
- **WebSocket for dashboard**: Real-time updates without polling
- **JSON**: Language-agnostic, easy to debug, human-readable
- **Timeout**: Prevents slow observability from blocking agents

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| WebSocket for ingestion | Over-complicated for one-way fire-and-forget events |
| Server-Sent Events (SSE) for dashboard | WebSocket more widely supported, bidirectional if needed later |
| MessagePack binary format | JSON readability more valuable than marginal size savings |
| gRPC | Massive overkill for localhost-only communication |

### Implementation Notes

- **send_event.py** hook script uses `requests` library with 100ms timeout
- Observability-server stores events in SQLite, then broadcasts via WebSocket
- Dashboard maintains WebSocket connection, shows notifications on new events
- Failed event sends are silently logged (don't disrupt agent operation)

---

## Q4: Database Schema for Events

**Question**: What schema should events.db use for storing observability events?

### Decision

**Single events table with JSON metadata column**

```sql
CREATE TABLE events (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp       TEXT NOT NULL,              -- ISO 8601 format
  source_app      TEXT NOT NULL,              -- "resume-agent", "translation-teacher", etc.
  event_type      TEXT NOT NULL,              -- "PreToolUse", "PostToolUse", etc.
  tool_name       TEXT,                       -- Tool/function name (if applicable)
  summary         TEXT,                       -- AI-generated or manual summary
  session_id      TEXT,                       -- UUID for grouping related events
  metadata        TEXT,                       -- JSON blob for additional context
  created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_source_app ON events(source_app);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_session ON events(session_id);
```

### Rationale

- **Simple schema**: Single table, easy to query
- **Flexible metadata**: JSON column allows app-specific data without schema changes
- **Indexed queries**: Fast filtering by app, time, and session
- **Text timestamps**: ISO 8601 strings are SQLite-friendly and human-readable

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Separate table per event type | Over-normalized, harder to query across types |
| NoSQL/document store | SQLite simpler for small-scale, no external dependencies |
| Timeseries database (InfluxDB) | Overkill for development observability |
| Separate database per app | Would fragment data, harder to correlate events |

### Implementation Notes

- Database location: `data/events.db` (shared, accessible to all apps)
- Retention policy: Manual cleanup (or future auto-delete events older than 30 days)
- Query patterns optimized: "Recent events by app", "Events in session", "Events by time range"

---

## Q5: System Startup Script Design

**Question**: How should start-system script detect running processes and handle errors?

### Decision

**Port-Based Detection + PID File Tracking**

Script behavior:

1. **Check ports** 4000 (observability-server) and 5173 (client)
   - If port in use → Warn user, ask to continue or stop
2. **Start observability-server** in background, save PID
3. **Start client** in background, save PID
4. **Wait 5 seconds**, verify ports are listening
5. **Display URLs** and status

Error handling:
- If startup fails → Kill started processes, display error
- If port already in use → Option to kill existing or skip

### PowerShell Script Structure

```powershell
# scripts/start-system.ps1
# Check port 4000
if (Test-NetConnection -ComputerName localhost -Port 4000 -InformationLevel Quiet) {
    Write-Warning "Port 4000 already in use"
}

# Start observability-server
cd apps/observability-server
$serverJob = Start-Job { bun run src/index.ts }

# Start client
cd ../client
$clientJob = Start-Job { bun run dev }

# Wait and verify
Start-Sleep -Seconds 5
if (-not (Test-NetConnection -ComputerName localhost -Port 4000 -InformationLevel Quiet)) {
    Write-Error "Observability server failed to start"
    Stop-Job $serverJob, $clientJob
    exit 1
}

Write-Host "✓ Observability Server: http://localhost:4000"
Write-Host "✓ Web Dashboard: http://localhost:5173"
```

### Rationale

- **Port checking**: Reliable way to detect running services
- **Background jobs**: PowerShell `Start-Job` keeps processes alive after script exits
- **Graceful errors**: Cleanup on failure prevents orphaned processes
- **User-friendly**: Clear status messages and URLs

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Process name detection (Get-Process) | Unreliable - "bun" might be running for other projects |
| PID file only | Stale PID files cause false positives |
| Docker Compose | Over-complicated for localhost development |
| systemd/launchd services | Platform-specific, over-engineered |

### Implementation Notes

- Create both PowerShell (.ps1) and Bash (.sh) versions
- Stop script kills jobs by port number (finds process using port, kills it)
- Reset script runs stop, deletes data/events.db, runs start

---

## Q6: Disler Repository Adaptation Strategy

**Question**: How should code from Disler's reference repository be adapted for this project?

### Decision

**Direct File Copy + Minimal Adaptation**

Process:
1. **Clone reference repo** to `temp-observability-reference/` (git ignored)
2. **Copy files directly**:
   - `apps/server/*` → `apps/observability-server/`
   - `apps/client/*` → `apps/client/`
   - `.claude/hooks/*` → `.claude/hooks/`
3. **Adapt only paths**:
   - Update database path: `./data/events.db` → `../../data/events.db`
   - Update import paths if needed
4. **Keep Disler code intact**: Don't refactor, don't optimize, copy as-is
5. **Add attribution** in README files

### Rationale

- **Proven code**: Disler's implementation is battle-tested
- **Faster delivery**: Copy+adapt faster than rewrite
- **Lower risk**: Less chance of introducing bugs
- **Learn by using**: Can refactor later after understanding patterns

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Rewrite from scratch | Higher risk, slower, likely to miss edge cases |
| Fork Disler's repo | Would import unnecessary files, harder to customize |
| Git submodule | Complications with mono repo structure, harder to adapt paths |

### Implementation Notes

- Add comment headers: `// Adapted from Disler's Multi-Agent Observability`
- Document differences in CLAUDE.md
- Keep reference repo around until migration complete
- File cleanup removes `temp-observability-reference/` after validation

---

## Best Practices Research

### Multi-App Monorepo Best Practices

**Research Sources**: Google's Bazel docs, Nx monorepo patterns, turborepo documentation

**Key Findings**:

1. **Dependency Isolation**: Each app should have its own package.json/requirements.txt
2. **Shared Code**: Resist urge to create shared libraries early (YAGNI)
3. **Build Independence**: Each app builds without requiring others
4. **Test Independence**: Tests run without cross-app dependencies
5. **Documentation**: Each app README should be complete standalone guide

**Applied to This Project**:
- ✅ Each app has own dependencies
- ✅ No shared code libraries (apps communicate via events/data only)
- ✅ Resume-agent builds with `uv run`, observability-server with `bun install && bun run`
- ✅ Tests run per-app: `pytest` in resume-agent, `bun test` in observability-server
- ✅ Each app has README with setup instructions

### MCP Server Best Practices

**Research Sources**: Anthropic MCP documentation, FastMCP examples, MCP servers repository

**Key Findings**:

1. **Tool Design**: Each tool should do one thing well
2. **Error Handling**: Return structured errors, not exceptions
3. **Validation**: Validate inputs with Pydantic before processing
4. **Idempotency**: Tools should be safe to retry
5. **Testing**: Contract tests for tool signatures, integration tests for workflows

**Applied to This Project**:
- ✅ Resume-agent tools follow single-responsibility (analyze_job, tailor_resume, apply_to_job)
- ✅ All tools return structured results with error field
- ✅ Pydantic validation on all MCP tool parameters
- ✅ fetch-job command is idempotent (safe to run multiple times)
- ✅ Contract tests planned (Phase 1)

### SQLite for Multi-App Shared Storage

**Research Sources**: SQLite documentation, "SQLite Is Not a Toy Database" article

**Key Findings**:

1. **Locking**: SQLite handles concurrent reads well, writes are serialized
2. **WAL Mode**: Write-Ahead Logging mode improves concurrent access
3. **Busy Timeout**: Set PRAGMA busy_timeout for retry on locks
4. **Connection Pooling**: Not needed for SQLite (single file)
5. **Indexing**: Critical for query performance (timestamps, foreign keys)

**Applied to This Project**:
- ✅ Enable WAL mode on both databases: `PRAGMA journal_mode=WAL;`
- ✅ Set busy timeout: `PRAGMA busy_timeout=5000;` (5 seconds)
- ✅ Indexes on events table: source_app, timestamp, session_id
- ✅ No connection pooling (unnecessary for SQLite)
- ✅ Database location: `data/*.db` (shared, accessible to all apps)

---

## Research Summary

All "NEEDS CLARIFICATION" items resolved:

1. ✅ **Testing Framework**: pytest (Python), Bun test (TypeScript), Vitest (Vue 3)
2. ✅ **Path Resolution**: Absolute paths via PROJECT_ROOT constant
3. ✅ **WebSocket Message Format**: JSON over HTTP POST + WebSocket broadcast
4. ✅ **Database Schema**: Single events table with JSON metadata
5. ✅ **System Startup Script**: Port-based detection with PowerShell jobs
6. ✅ **Disler Repository Adaptation**: Direct file copy with minimal path changes

**Risks Identified**:

- **Testing complexity**: Multiple testing frameworks increases learning curve
  - **Mitigation**: Each app uses its ecosystem's standard, well-documented frameworks
- **SQLite write contention**: If event volume is very high (>100/sec)
  - **Mitigation**: WAL mode + busy timeout, batch writes if needed
- **Path resolution bugs**: Incorrect PROJECT_ROOT calculation
  - **Mitigation**: Validate paths at startup, fail fast with clear errors

**Dependencies Validated**:

- Bun: Fast TypeScript runtime, justified for observability-server
- Vue 3: Industry standard for reactive UIs, justified for dashboard
- pytest: Python standard, justified for resume-agent
- Vitest: Vite-native testing, justified for client

**Proceed to Phase 1**: All research complete, ready for data modeling and contract definition.
