# Observability Server

Real-time event tracking and broadcasting server for multi-agent observability.

## Overview

The Observability Server collects events from all apps (via hooks) and broadcasts them to connected clients via WebSocket. It provides a centralized observability system for monitoring agent activities in real-time.

## Features

- **Event Collection**: HTTP POST endpoint for receiving events from hooks
- **Real-time Broadcasting**: WebSocket streaming to connected clients
- **SQLite Storage**: Events stored in `../../data/events.db` with WAL mode
- **Session Tracking**: Events grouped by session ID for debugging workflows
- **AI Summaries**: Optional AI-generated summaries of tool usage

## Quick Start

### Prerequisites

- Bun runtime (https://bun.sh)

### Installation

```bash
cd apps/observability-server
bun install
```

### Running

```bash
# Development with hot reload
bun run dev

# Production
bun run start
```

The server will start on http://localhost:4000

## API Endpoints

### POST /events

Submit an event for storage and broadcasting.

**Request Body**:
```json
{
  "timestamp": 1234567890,
  "source_app": "resume-agent",
  "session_id": "uuid-v4",
  "hook_event_type": "PreToolUse",
  "payload": {},
  "ai_summary": "Optional AI summary"
}
```

**Response**: `200 OK`

### WebSocket /stream

Subscribe to real-time event stream.

**Connection**: `ws://localhost:4000/stream`

**Messages**: JSON event objects broadcasted as they arrive

## Architecture

- **Runtime**: Bun (fast JavaScript/TypeScript runtime)
- **Language**: TypeScript
- **Database**: SQLite at `../../data/events.db` (WAL mode enabled)
- **Transport**: HTTP REST + WebSocket
- **Port**: 4000

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
  chat_transcript TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Event Flow

```
Claude Hook → send_event.py → HTTP POST /events → SQLite → WebSocket Broadcast → Web Clients
```

## Development

### Project Structure

```
apps/observability-server/
├── src/
│   ├── index.ts     # HTTP + WebSocket server
│   ├── db.ts        # SQLite database operations
│   └── types.ts     # TypeScript type definitions
├── package.json
├── tsconfig.json
└── README.md
```

### Testing

```bash
# Test event submission
curl -X POST http://localhost:4000/events \
  -H "Content-Type: application/json" \
  -d '{"timestamp":1234567890,"source_app":"test","session_id":"123","hook_event_type":"PreToolUse","payload":{}}'

# Test WebSocket (in browser console)
const ws = new WebSocket('ws://localhost:4000/stream');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Configuration

No configuration files needed - server uses sensible defaults:
- Port: 4000
- Database: `../../data/events.db`
- CORS: Enabled for all origins (localhost only)

## Integration

### With Root Hooks (../../.claude/hooks/)
Hook scripts send events using `send_event.py`:
```bash
uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PreToolUse
```

### With Web Client (../client/)
Web client connects via:
- WebSocket: `ws://localhost:4000/stream` for real-time updates
- REST API: `http://localhost:4000/events/recent` for historical data

### With Database (../../data/)
Events stored in shared `events.db` at repository root for cross-app access.

## Attribution

Adapted from [Disler's Multi-Agent Observability](https://github.com/disler/claude-code-hooks-multi-agent-observability)

## Troubleshooting

### Port 4000 already in use
```powershell
# Kill process using port 4000
Get-NetTCPConnection -LocalPort 4000 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
```

### Database locked errors
Ensure WAL mode is enabled (should be automatic). If issues persist:
```bash
sqlite3 ../../data/events.db "PRAGMA journal_mode=WAL;"
```

### WebSocket connection fails
1. Verify server is running on port 4000
2. Check browser console for CORS errors
3. Ensure no firewall blocking localhost connections

## Related Documentation

- [CLAUDE.md](CLAUDE.md) - Detailed development instructions
- [../../README.md](../../README.md) - Project overview
- [../client/README.md](../client/README.md) - Web dashboard documentation
