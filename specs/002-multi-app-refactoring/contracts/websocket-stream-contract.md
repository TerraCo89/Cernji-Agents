# WebSocket Stream Contract

## Purpose

This document defines the WebSocket protocol for real-time event streaming from observability-server to web dashboard clients.

## Connection

### Endpoint

```
ws://localhost:4000/stream
```

### Protocol

- **Transport**: WebSocket (RFC 6455)
- **Upgrade**: From HTTP GET request
- **Reconnection**: Client must implement auto-reconnect on disconnect

### Connection Handshake

**Client Request**:

```http
GET /stream HTTP/1.1
Host: localhost:4000
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

**Server Response**:

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

## Message Format

### Server → Client (Event Broadcast)

**Message Type**: Text (UTF-8 JSON)

**Schema**:

```typescript
interface WebSocketMessage {
  type: "event";
  data: Event;
}

interface Event {
  id: number;
  timestamp: string;              // ISO 8601
  source_app: string;
  event_type: string;
  tool_name?: string;
  summary?: string;
  session_id?: string;
  metadata?: string;              // JSON string
  created_at: string;             // ISO 8601
}
```

**Example Message**:

```json
{
  "type": "event",
  "data": {
    "id": 123,
    "timestamp": "2025-10-21T10:30:45.123Z",
    "source_app": "resume-agent",
    "event_type": "PreToolUse",
    "tool_name": "mcp__sqlite__query",
    "summary": "Querying portfolio_library table for RAG examples",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": "{\"query\": \"SELECT * FROM portfolio_library WHERE technologies LIKE '%RAG%'\"}",
    "created_at": "2025-10-21T10:30:45.456Z"
  }
}
```

### Client → Server (Control Messages)

**Ping Message** (optional, for keep-alive):

```json
{
  "type": "ping"
}
```

**Server Response** (pong):

```json
{
  "type": "pong",
  "timestamp": "2025-10-21T10:30:50.000Z"
}
```

## Client Behavior Contract

### Connection Lifecycle

```
[Disconnected]
    ↓
  connect()
    ↓
[Connecting] → (on error) → [Disconnected]
    ↓
  (on open)
    ↓
[Connected]
    ↓
  (on message) → handleEvent(message)
    ↓
  (on close) → reconnect after 1s delay
    ↓
[Disconnected]
```

### Auto-Reconnect

**Requirements**:

1. **Exponential Backoff**: Retry delays: 1s, 2s, 4s, 8s, max 30s
2. **Infinite Retries**: Never give up reconnecting
3. **Visual Indicator**: Show "Reconnecting..." in UI
4. **Resume State**: After reconnect, fetch recent events to fill gap

**Example (JavaScript)**:

```typescript
class EventStream {
  private ws: WebSocket | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;

  connect() {
    this.ws = new WebSocket('ws://localhost:4000/stream');

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectDelay = 1000; // Reset delay on successful connect
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'event') {
        this.handleEvent(message.data);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      setTimeout(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
        this.connect();
      }, this.reconnectDelay);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.ws?.close();
    };
  }

  handleEvent(event: Event) {
    // Update UI with new event
  }
}
```

### Message Handling

**Requirements**:

1. **Parse JSON**: All messages are JSON, parse before processing
2. **Validate Type**: Check `message.type === 'event'` before handling
3. **Idempotency**: Handle duplicate events gracefully (same ID)
4. **Order**: Events may arrive out-of-order, use timestamp for sorting

**Example**:

```typescript
onmessage(event: MessageEvent) {
  try {
    const message = JSON.parse(event.data);

    if (message.type === 'event') {
      // Validate event has required fields
      if (!message.data || !message.data.id) {
        console.error('Invalid event message:', message);
        return;
      }

      // Check for duplicate (if event.id already in state)
      if (this.events.has(message.data.id)) {
        console.warn('Duplicate event received:', message.data.id);
        return;
      }

      // Add to state
      this.addEvent(message.data);
    } else if (message.type === 'pong') {
      // Handle pong (if using ping/pong)
      this.lastPong = Date.now();
    }
  } catch (error) {
    console.error('Failed to parse WebSocket message:', error);
  }
}
```

## Server Behavior Contract

### Broadcasting

**Requirements**:

1. **Immediate Broadcast**: After event is saved to database, broadcast to all connected clients
2. **All Clients**: Broadcast to ALL connected WebSocket clients (no filtering)
3. **No Acknowledgement**: Fire-and-forget, don't wait for client response
4. **Error Handling**: If client connection is broken, remove from client list

**Example (TypeScript/Bun)**:

```typescript
import { ServerWebSocket } from 'bun';

const clients = new Set<ServerWebSocket>();

// WebSocket server
Bun.serve({
  websocket: {
    open(ws) {
      clients.add(ws);
      console.log('Client connected, total:', clients.size);
    },
    close(ws) {
      clients.delete(ws);
      console.log('Client disconnected, total:', clients.size);
    },
    message(ws, message) {
      // Handle ping if needed
      const data = JSON.parse(message as string);
      if (data.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
      }
    }
  }
});

// Broadcast function (called after saving event to DB)
function broadcastEvent(event: Event) {
  const message = JSON.stringify({ type: 'event', data: event });

  clients.forEach((client) => {
    try {
      client.send(message);
    } catch (error) {
      console.error('Failed to send to client:', error);
      clients.delete(client); // Remove broken connection
    }
  });
}
```

### Connection Limits

**Requirements**:

1. **No Hard Limit**: Support unlimited concurrent clients (for development)
2. **Memory Consideration**: Each client consumes ~1KB memory
3. **Graceful Degradation**: If server overloaded, new connections may fail (client will auto-reconnect)

## Performance Requirements

### Latency

- **Target**: <100ms from event save to client receive
- **Measurement**: `client_receive_time - event.created_at`
- **Acceptable**: <1s (per spec success criteria)

### Throughput

- **Events per Second**: Support 10 events/second sustained
- **Burst Capacity**: Support 100 events/second for 10 seconds
- **Client Count**: Support 10 concurrent clients without degradation

## Error Handling

### Client Errors

| Error | Cause | Client Action |
|-------|-------|---------------|
| Connection Refused | Server not running | Show error, retry with backoff |
| Connection Timeout | Network issue | Show error, retry with backoff |
| Message Parse Error | Invalid JSON from server | Log error, ignore message, continue |
| WebSocket Close Code 1006 | Abnormal closure | Reconnect immediately |

### Server Errors

| Error | Cause | Server Action |
|-------|-------|---------------|
| Client Send Failure | Client disconnected | Remove from client list, log error |
| JSON Stringify Error | Invalid event data | Log error, skip broadcast |
| Too Many Clients | Memory exhausted | Reject new connections (return 503) |

## Contract Tests

### Test Cases

#### 1. Client Connection

**Given**: Server is running
**When**: Client connects to ws://localhost:4000/stream
**Then**: WebSocket connection is established (status 101)

#### 2. Event Broadcast

**Given**: 2 clients are connected
**When**: New event is posted to /events endpoint
**Then**: Both clients receive event via WebSocket within 100ms

#### 3. Client Disconnect/Reconnect

**Given**: Client is connected
**When**: Server is stopped
**Then**: Client detects disconnect and attempts reconnect every 1s

#### 4. Duplicate Event Handling

**Given**: Client receives event with id=123
**When**: Client receives same event again (id=123)
**Then**: Client ignores duplicate, doesn't add to state

#### 5. Out-of-Order Events

**Given**: Events with timestamps T1, T2, T3 are broadcast
**When**: Client receives in order T1, T3, T2
**Then**: Client sorts by timestamp, displays in correct order

### Sample Test (Playwright)

```typescript
test('WebSocket receives events in real-time', async ({ page }) => {
  // Connect to dashboard
  await page.goto('http://localhost:5173');

  // Wait for WebSocket connection
  await page.waitForSelector('.status-connected');

  // Submit event via HTTP
  const response = await fetch('http://localhost:4000/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      timestamp: new Date().toISOString(),
      source_app: 'test-app',
      event_type: 'PreToolUse',
      tool_name: 'test_tool',
      summary: 'Test event'
    })
  });

  expect(response.status).toBe(201);

  // Verify event appears in dashboard within 1 second
  await page.waitForSelector('.event:has-text("Test event")', { timeout: 1000 });
});
```

## Version

**Version**: 1.0.0
**Last Updated**: 2025-10-21
