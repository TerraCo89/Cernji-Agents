# Observability Server - Claude Code Instructions

## Purpose
Real-time event tracking server for monitoring Claude Code agents.

## Tech Stack
- **Runtime**: Bun (fast JavaScript/TypeScript)
- **Language**: TypeScript
- **Database**: SQLite with WAL mode
- **Transport**: HTTP REST + WebSocket

## Key Commands

```bash
# Install dependencies
bun install

# Development (hot reload)
bun run dev

# Production
bun run start

# Type checking
bun run typecheck
```

## Architecture

### Database (src/db.ts)
- SQLite database with WAL mode for concurrent access
- Automatic schema migrations
- Event storage with indexing for fast queries
- Located at: `../../data/events.db`

### Server (src/index.ts)
- HTTP server for REST API
- WebSocket server for real-time broadcasting
- CORS enabled for web client
- Port: 4000 (default)

### Types (src/types.ts)
- TypeScript interfaces for events
- Type safety across the application

## Event Flow

```
Claude Hook → send_event.py → HTTP POST /events → SQLite → WebSocket Broadcast → Web Clients
```

## Development Guidelines

### When Adding Features
1. Update types in `src/types.ts` first
2. Add database migration in `src/db.ts` if needed
3. Implement endpoint in `src/index.ts`
4. Test with curl or web client

### When Debugging
1. Check server logs in terminal
2. Verify database with: `sqlite3 ../../data/events.db "SELECT * FROM events LIMIT 5;"`
3. Test WebSocket with browser console
4. Check CORS headers for web client issues

### Code Style
- Use TypeScript strict mode
- Prefer explicit types over `any`
- Use async/await for database operations
- Handle errors gracefully with try/catch
- Log important events to console

## Common Tasks

### Add New Endpoint
```typescript
// src/index.ts
server.get('/events/stats', async (req) => {
  const stats = await getEventStats();
  return new Response(JSON.stringify(stats), {
    headers: { 'Content-Type': 'application/json' }
  });
});
```

### Add Database Query
```typescript
// src/db.ts
export function getEventStats() {
  const stmt = db.prepare(`
    SELECT hook_event_type, COUNT(*) as count
    FROM events
    GROUP BY hook_event_type
  `);
  return stmt.all();
}
```

### Update Event Schema
```typescript
// src/types.ts
export interface HookEvent {
  id?: number;
  timestamp: number;
  source_app: string;
  session_id: string;
  hook_event_type: string;
  payload: any;
  ai_summary?: string;
  chat_transcript?: string;
  // Add new field here
  new_field?: string;
}

// src/db.ts - Add migration
db.exec(`
  ALTER TABLE events ADD COLUMN new_field TEXT;
`);
```

## Testing

### Manual Tests
```bash
# Test event submission
curl -X POST http://localhost:4000/events \
  -H "Content-Type: application/json" \
  -d '{"source_app":"test","session_id":"123","hook_event_type":"PreToolUse","payload":{}}'

# Test event retrieval
curl http://localhost:4000/events/recent?limit=10

# Test filter options
curl http://localhost:4000/events/filter-options
```

### WebSocket Test
```javascript
// Run in browser console
const ws = new WebSocket('ws://localhost:4000/stream');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Integration Points

### With Root Hooks (.claude/hooks/)
Hook scripts send events to this server using HTTP POST.

### With Web Client (../client/)
Web client connects via WebSocket for real-time updates and REST API for historical data.

### With Database (../../data/)
Stores events in `events.db` at project root for cross-app access.

## Important Notes

- Always use WAL mode for SQLite (enables concurrent reads)
- Broadcast all events to WebSocket clients immediately
- Return CORS headers for web client compatibility
- Log errors but don't crash the server
- Validate event payloads before storing

## Related Files

- `../../.claude/hooks/send_event.py` - Hook script that sends events
- `../client/src/composables/useWebSocket.ts` - Client WebSocket connection
- `../../data/events.db` - SQLite database
