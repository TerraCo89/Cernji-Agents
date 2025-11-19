# Logging Setup for Agent Chat UI

This document describes the logging implementation for the agent-chat-ui application.

## Overview

The agent-chat-ui application uses the Cernji Logging infrastructure for structured JSON logging with:

- **ECS (Elastic Common Schema) format** - Industry-standard log format for Elasticsearch
- **Correlation ID tracking** - Track requests across async boundaries using AsyncLocalStorage
- **Centralized log collection** - Logs are shipped to Elasticsearch via Filebeat for searching and analysis
- **High performance** - Built on Pino, one of the fastest logging libraries for Node.js

## Quick Start

### 1. Install Dependencies

```bash
cd apps/agent-chat-ui
pnpm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and adjust logging settings:

```bash
# Logging Configuration
SERVICE_NAME=agent-chat-ui
LOG_LEVEL=info              # trace, debug, info, warn, error, fatal
LOG_FORMAT=json             # json (production), pretty (development)
LOG_FILE=logs/app.json.log  # Path to log file
SERVICE_VERSION=1.0.0
ENVIRONMENT=development     # development, staging, production
```

### 3. Start the Application

```bash
pnpm dev
```

Logs will be written to `logs/app.json.log` in structured JSON format.

### 4. View Logs in Kibana (Optional)

If you have the ELK stack running (see [root LOGGING.md](../../LOGGING.md)):

1. Open http://localhost:5601
2. Go to **Analytics** > **Discover**
3. Search for logs from `agent-chat-ui`:
   ```
   service.name: "agent-chat-ui"
   ```

## Usage

### Basic Logging

```typescript
import { getLogger } from '@/lib/logger';

const logger = getLogger('MyComponent');

// Info logging
logger.info({ userId: 123, action: 'login' }, 'User logged in');

// Error logging
logger.error({ error: err.message, userId: 123 }, 'Login failed');

// Warning logging
logger.warn({ threadId: 'abc' }, 'Thread taking longer than expected');
```

### With Correlation IDs

Track related operations across async boundaries:

```typescript
import { withCorrelation, getLogger } from '@/lib/logger';

const logger = getLogger('StreamHandler');

// Generate or extract correlation ID from request
const correlationId = requestHeaders['x-correlation-id'] || generateId();

await withCorrelation(correlationId, async () => {
  logger.info('Processing stream request');

  // All logs within this context will include trace.id
  await processStream();

  logger.info('Stream processing completed');
});
```

Then search in Kibana:
```
trace.id: "your-correlation-id"
```

### Log Levels

Use appropriate log levels:

- **info** - Normal application flow (user actions, API calls)
- **warn** - Potential issues (slow responses, retries)
- **error** - Failures requiring attention (API errors, exceptions)
- **debug** - Detailed debugging information (development only)

## Implementation Details

### Logger Utility

The centralized logger utility is at `src/lib/logger.ts`:

```typescript
export function getLogger(name?: string)
export async function withCorrelation<T>(correlationId: string | null, fn: () => Promise<T>): Promise<T>
export function getCurrentCorrelationId(): string | undefined
export const logger // Default logger instance
```

### Modified Files

Logging has been added to:

- **API Routes** (`src/app/api/[..._path]/route.ts`) - API passthrough logging
- **Stream Provider** (`src/providers/Stream.tsx`) - Graph status checks, thread management
- **Thread History** (`src/components/thread/history/index.tsx`) - Thread loading
- **Agent Inbox** (`src/components/thread/agent-inbox/`) - All interrupt handling and user actions
  - `index.tsx` - Side panel state management
  - `hooks/use-interrupted-actions.tsx` - Human response submission
  - `utils.ts` - Response validation
  - `components/inbox-item-input.tsx` - Input validation

All `console.log`, `console.error`, and `console.warn` calls have been replaced with structured logging.

### Log Output Format

Logs are written in ECS format:

```json
{
  "@timestamp": "2025-11-15T10:30:00.123Z",
  "log.level": "info",
  "message": "Thread ID changed",
  "ecs.version": "8.11.0",
  "service": {
    "name": "agent-chat-ui",
    "version": "1.0.0",
    "environment": "development"
  },
  "trace": {
    "id": "req-12345"
  },
  "threadId": "abc123"
}
```

## Best Practices

### 1. Always Use Structured Fields

**Good** - Structured data for easy searching:
```typescript
logger.info({ threadId: 'abc', messageCount: 5 }, 'Thread messages loaded');
```

**Bad** - String interpolation (hard to search):
```typescript
logger.info(`Thread ${threadId} loaded ${messageCount} messages`);
```

### 2. Include Context in Errors

```typescript
try {
  await processThread(threadId);
} catch (error) {
  logger.error({
    threadId,
    error: error instanceof Error ? error.message : String(error),
    // Include relevant context
    userId,
    assistantId
  }, 'Failed to process thread');
  throw error;
}
```

### 3. Use Correlation IDs for User Sessions

```typescript
// At session start
const sessionId = generateSessionId();

await withCorrelation(sessionId, async () => {
  // All user actions in this session will be correlated
  logger.info('User started new chat');
  await handleUserMessages();
});
```

## Troubleshooting

### Logs Not Appearing in Files

**Check 1**: Ensure logs directory exists
```bash
ls -la logs/
```

**Check 2**: Verify environment variables
```bash
echo $SERVICE_NAME
echo $LOG_FILE
```

**Check 3**: Check file permissions
```bash
chmod 755 logs/
```

### Development vs Production

For development, use pretty logging:
```bash
LOG_FORMAT=pretty
```

For production, always use JSON:
```bash
LOG_FORMAT=json
```

## Next Steps

1. ✅ Logging infrastructure set up
2. ✅ All console.* calls replaced with structured logging
3. ⬜ Set up ELK stack (optional, see [root LOGGING.md](../../LOGGING.md))
4. ⬜ Create Kibana dashboards for monitoring
5. ⬜ Set up alerting for error rates

## Resources

- **Project Logging Guide**: [../../LOGGING.md](../../LOGGING.md)
- **TypeScript Logging Library**: [../../libs/cernji-logging-ts/README.md](../../libs/cernji-logging-ts/README.md)
- **ELK Stack Setup**: [../../docker/elk/README.md](../../docker/elk/README.md)
- **Pino Documentation**: https://getpino.io/
- **ECS Specification**: https://www.elastic.co/guide/en/ecs/current/index.html
