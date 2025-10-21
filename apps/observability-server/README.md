# Observability Server

Real-time event tracking server for multi-agent monitoring.

## Overview

This server captures, stores, and broadcasts Claude Code hook events in real-time. It provides:
- HTTP POST endpoint for receiving events from Claude Code hooks
- SQLite database for event persistence
- WebSocket server for broadcasting events to connected clients
- RESTful API for querying historical events

**Based on**: Disler's [Multi-Agent Observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) pattern

## Architecture

- **Runtime**: Bun (fast JavaScript/TypeScript runtime)
- **Language**: TypeScript
- **Database**: SQLite with WAL mode
- **Transport**: HTTP REST + WebSocket
- **Port**: 4000 (default)

## Quick Start

### Prerequisites

- [Bun](https://bun.sh/) installed (`curl -fsSL https://bun.sh/install | bash`)

### Installation

1. **Install dependencies**:
   ```bash
   cd apps/observability-server
   bun install
   ```

2. **Run the server**:
   ```bash
   # Development mode (with hot reload)
   bun run dev

   # Production mode
   bun run start
   ```

3. **Verify server is running**:
   ```bash
   curl http://localhost:4000/health
   # Should return: {"status":"ok"}
   ```

## API Endpoints

### Health Check
```
GET /health
```
Returns server health status.

### Submit Event
```
POST /events
Content-Type: application/json

{
  "source_app": "resume-agent",
  "session_id": "session-123",
  "hook_event_type": "PreToolUse",
  "payload": {
    "tool_name": "Read",
    "tool_input": { "file_path": "README.md" }
  },
  "ai_summary": "Reading README file"
}
```

### Get Recent Events
```
GET /events/recent?limit=50&source_app=resume-agent&session_id=session-123
```

Query Parameters:
- `limit` (default: 100) - Number of events to return
- `source_app` - Filter by source application
- `session_id` - Filter by session ID
- `hook_event_type` - Filter by event type

### Get Filter Options
```
GET /events/filter-options
```
Returns available values for filtering (apps, sessions, event types).

### WebSocket Stream
```
WS /stream
```
Real-time event broadcasting to all connected clients.

## Database Schema

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp INTEGER NOT NULL,
  source_app TEXT NOT NULL,
  session_id TEXT NOT NULL,
  hook_event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  ai_summary TEXT,
  chat_transcript TEXT
);

CREATE INDEX idx_timestamp ON events(timestamp DESC);
CREATE INDEX idx_source_app ON events(source_app);
CREATE INDEX idx_session_id ON events(session_id);
CREATE INDEX idx_hook_event_type ON events(hook_event_type);
```

## Hook Integration

Events are sent from Claude Code hooks using the `send_event.py` script:

```bash
# From .claude/hooks/
uv run send_event.py --source-app resume-agent --event-type PreToolUse --summarize
```

Example `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PreToolUse --summarize"
      }]
    }]
  }
}
```

## Development

### File Structure

```
apps/observability-server/
├── src/
│   ├── index.ts     # HTTP + WebSocket server
│   ├── db.ts        # SQLite database management
│   ├── types.ts     # TypeScript type definitions
│   └── theme.ts     # Theme management (optional)
├── package.json
├── tsconfig.json
├── README.md
└── CLAUDE.md
```

### Type Checking

```bash
bun run typecheck
```

### Database Location

The SQLite database is created at: `../../data/events.db` (relative to project root)

## Testing

### Manual Event Test

```bash
curl -X POST http://localhost:4000/events \
  -H "Content-Type: application/json" \
  -d '{
    "source_app": "test",
    "session_id": "test-123",
    "hook_event_type": "PreToolUse",
    "payload": {"tool_name": "Bash", "tool_input": {"command": "ls"}}
  }'
```

### WebSocket Test

```javascript
const ws = new WebSocket('ws://localhost:4000/stream');
ws.onmessage = (event) => {
  console.log('Event received:', JSON.parse(event.data));
};
```

## Troubleshooting

### Port Already in Use

If port 4000 is already in use, change it in `src/index.ts`:

```typescript
const PORT = 4001; // Change to any available port
```

### Database Locked

If you see SQLite "database is locked" errors:
1. Close all connections to the database
2. Delete `../../data/events.db` and `../../data/events.db-wal`
3. Restart the server

### Bun Not Found

Install Bun:
```bash
curl -fsSL https://bun.sh/install | bash
```

## Related Documentation

- [Client App](../client/README.md) - Web dashboard for visualizing events
- [Root README](../../README.md) - Overall project architecture
- [Disler's Original Repo](https://github.com/disler/claude-code-hooks-multi-agent-observability)
