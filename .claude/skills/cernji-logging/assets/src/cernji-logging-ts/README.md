# Cernji Logging (TypeScript)

Standardized structured logging library for Cernji Agents ecosystem.

## Features

- **Structured JSON logging** with Elastic Common Schema (ECS) format
- **Correlation ID tracking** for distributed tracing via AsyncLocalStorage
- **Performance timing** decorators and middleware
- **Environment-based configuration** (dev vs. production)
- **High performance** with Pino (5x-10x faster than Winston)

## Installation

```bash
# From within a Cernji Agents app
bun add @cernji/logging@workspace:*
```

## Quick Start

```typescript
import { getLogger, withCorrelationId, Timed } from '@cernji/logging';

// Get a logger instance
const logger = getLogger('my-service');

// Basic logging
logger.info({ userId: 123 }, 'User logged in');

// With correlation ID context
await withCorrelationId('req-12345', async () => {
  logger.info('Processing request'); // Automatically includes trace.id
});

// Time class methods
class MyService {
  @Timed()
  async expensiveOperation() {
    // Your code here
  }
}

// Time functions manually
import { TimingContext } from '@cernji/logging';

const timer = new TimingContext(logger, 'database_query');
// ... code to time ...
timer.end();
```

## Configuration

Set via environment variables:

- `LOG_LEVEL` - Log level (trace, debug, info, warn, error, fatal) [default: info]
- `LOG_FORMAT` - Output format (json, pretty) [default: json]
- `LOG_FILE` - Log file path [default: stdout]
- `SERVICE_NAME` - Service name for ECS format [required]
- `SERVICE_VERSION` - Service version [optional]
- `ENVIRONMENT` - Environment name (dev, staging, prod) [default: dev]

## API Reference

### `getLogger(name?: string): Logger`

Get a Pino logger instance configured with ECS format.

### `withCorrelationId(correlationId: string | null, fn: () => Promise<T>): Promise<T>`

Execute an async function with a correlation ID in context.

### `getCorrelationId(): string | undefined`

Get the current correlation ID from AsyncLocalStorage.

### `@Timed(level?: string)`

Class method decorator that logs execution time.

### `class TimingContext`

Manual timing for code blocks.

## Output Format

All logs are output in ECS (Elastic Common Schema) format:

```json
{
  "@timestamp": 1700000000000,
  "log.level": "info",
  "message": "Processing request",
  "ecs": { "version": "8.11.0" },
  "service": {
    "name": "observability-server",
    "version": "1.0.0",
    "environment": "production"
  },
  "trace": { "id": "req-12345" },
  "event": { "duration": 1234567890 }
}
```

## Examples

See `examples/` directory for complete usage examples.
