# Cernji Logging Guide

Complete reference for Cernji-Logging libraries (Python & TypeScript).

## Overview

Cernji-Logging provides structured JSON logging libraries for both Python and TypeScript applications with:
- Elastic Common Schema (ECS) format
- Correlation ID tracking for distributed tracing
- Performance timing decorators
- Environment-based configuration
- Unified log aggregation across languages

## Available Libraries

### Python Library

**Location**: `libs/cernji-logging-py/`

**Installation**:
```bash
# From a Python app directory (e.g., apps/my-app/)
uv add cernji-logging --path ../../libs/cernji-logging-py --editable
```

**Quick Example**:
```python
from cernji_logging import get_logger, with_correlation_id, timed

logger = get_logger(__name__)

# Basic logging
logger.info("Application started", version="1.0.0")

# With correlation ID
with with_correlation_id("req-12345"):
    logger.info("Processing request")  # Includes trace.id

# Time expensive operations
@timed(logger)
async def expensive_function():
    # ... code ...
    pass
```

### TypeScript Library

**Location**: `libs/cernji-logging-ts/`

**Installation**:
```bash
# First, add workspace to root package.json
# "workspaces": ["apps/*", "libs/*"]

# From a TypeScript app directory
bun add @cernji/logging@workspace:*
```

**Quick Example**:
```typescript
import { getLogger, withCorrelationId, Timed } from '@cernji/logging';

const logger = getLogger('my-service');

// Basic logging
logger.info({ userId: 123 }, 'User logged in');

// With correlation ID
await withCorrelationId('req-12345', async () => {
  logger.info('Processing request'); // Includes trace.id
});

// Time class methods
class MyService {
  @Timed()
  async expensiveOperation() {
    // ... code ...
  }
}
```

## Unified Log Structure

Both libraries produce identical JSON structure:

```json
{
  "@timestamp": "2025-11-15T10:30:00.123Z",
  "log.level": "info",
  "message": "Processing request",
  "ecs.version": "8.11.0",
  "service.name": "my-service",
  "service.version": "1.0.0",
  "service.environment": "production",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "event.duration": 1234567890,
  "event.module": "my_service.module"
}
```

## Configuration

### Environment Variables

Both libraries use the same environment variable names:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Log level | `INFO` | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `LOG_FORMAT` | Output format | `json` | `json`, `text` (Python), `pretty` (TypeScript) |
| `LOG_FILE` | Log file path | stdout | `/var/log/app/app.json.log` |
| `SERVICE_NAME` | Service identifier | Required | `my-service` |
| `SERVICE_VERSION` | Service version | Optional | `1.0.0` |
| `ENVIRONMENT` | Environment name | `dev` | `dev`, `staging`, `prod` |

### Example .env

```bash
# Logging configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/my-app/app.json.log
SERVICE_NAME=my-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
```

## Correlation ID Best Practices

### Generate at Entry Points

**Python**:
```python
from cernji_logging import generate_correlation_id, set_correlation_id

# HTTP endpoint
@app.post("/api/endpoint")
async def endpoint(request):
    correlation_id = request.headers.get('X-Correlation-ID') or generate_correlation_id()
    set_correlation_id(correlation_id)
    # All logs in this request will include trace.id
```

**TypeScript**:
```typescript
import { generateCorrelationId, withCorrelationId } from '@cernji/logging';

// HTTP middleware
app.use(async (req, res, next) => {
  const correlationId = req.headers['x-correlation-id'] || generateCorrelationId();
  await withCorrelationId(correlationId, async () => {
    next();
  });
});
```

### Propagate Across Services

Always include `X-Correlation-ID` header when making HTTP requests:

**Python**:
```python
import httpx
from cernji_logging import get_correlation_id

async def call_service():
    headers = {}
    correlation_id = get_correlation_id()
    if correlation_id:
        headers['X-Correlation-ID'] = correlation_id

    async with httpx.AsyncClient() as client:
        await client.get('http://other-service/api', headers=headers)
```

**TypeScript**:
```typescript
import { getCorrelationId } from '@cernji/logging';

async function callService() {
  const correlationId = getCorrelationId();
  const headers = correlationId ? { 'X-Correlation-ID': correlationId } : {};

  await fetch('http://other-service/api', { headers });
}
```

## Performance Timing

### Python - Function Decorator

```python
from cernji_logging import get_logger, timed

logger = get_logger(__name__)

@timed(logger)  # Default: info level
async def slow_operation():
    # ... code ...
    pass

@timed(logger, level="debug")  # Custom level
def another_operation():
    # ... code ...
    pass
```

### Python - Context Manager

```python
from cernji_logging import TimingContext

with TimingContext(logger, "database_query"):
    # ... code to time ...
    pass
# Automatically logs duration when exiting context
```

### TypeScript - Class Decorator

```typescript
import { Timed } from '@cernji/logging';

class DatabaseService {
  @Timed()
  async queryUsers() {
    // ... code ...
  }

  @Timed('debug')
  async internalOperation() {
    // ... code ...
  }
}
```

### TypeScript - Manual Timing

```typescript
import { TimingContext } from '@cernji/logging';

const timer = new TimingContext(logger, 'database_query');
// ... code to time ...
timer.end();  // Logs duration
```

## Migration Guide

### From Python print() to cernji-logging

**Before**:
```python
print(f"Processing job {job_id}")
print(f"Error: {error}")
```

**After**:
```python
from cernji_logging import get_logger

logger = get_logger(__name__)

logger.info("Processing job", job_id=job_id)
logger.error("Error occurred", error=str(error), exc_info=True)
```

### From Python logging.basicConfig to cernji-logging

**Before**:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**After**:
```python
from cernji_logging import get_logger

# Environment variables configure everything
logger = get_logger(__name__)
```

### From TypeScript console.log to cernji-logging

**Before**:
```typescript
console.log('[Service] Processing request:', requestId);
console.error('Error occurred:', error);
```

**After**:
```typescript
import { getLogger } from '@cernji/logging';

const logger = getLogger('my-service');

logger.info({ requestId }, 'Processing request');
logger.error({ error }, 'Error occurred');
```

## Troubleshooting

### Correlation IDs not appearing in logs

**Python**: Ensure you're using `with_correlation_id()` context manager:
```python
with with_correlation_id("my-id"):
    logger.info("test")  # Will include trace.id
```

**TypeScript**: Ensure you're using `withCorrelationId()` with async function:
```typescript
await withCorrelationId('my-id', async () => {
  logger.info('test');  // Will include trace.id
});
```

### Performance timing not working

**Python**: Logger must be passed to decorator:
```python
@timed(logger)  # ✓ Correct
async def func(): pass

@timed  # ✗ Wrong - no logger
async def func(): pass
```

**TypeScript**: Class must have `logger` property:
```typescript
class MyService {
  logger = getLogger('my-service');  // Required!

  @Timed()
  async method() { }
}
```

## ELK Stack Integration

Cernji-Logging libraries are designed to work with the ELK (Elasticsearch, Logstash, Kibana) stack for unified log aggregation and analysis.

### Architecture

```
Your Apps (Python/TypeScript)
  ↓ JSON logs to files
Filebeat (log shipper)
  ↓ bulk ingestion
Elasticsearch (search & storage)
  ↓ visualization
Kibana (dashboards & alerting)
```

### Integration Notes

1. Configure apps to write JSON logs to files using `LOG_FILE` environment variable
2. Set up Filebeat to ship logs to Elasticsearch
3. Access Kibana for visualization and searching
4. Search logs by correlation ID: `trace.id: "550e8400-e29b-41d4-a716-446655440000"`

For full ELK stack setup instructions, refer to the project's `docker/elk/README.md` documentation.

## Complete Examples

### Complete Python Example

```python
# apps/my-app/my_app.py
import os
from cernji_logging import get_logger, with_correlation_id, timed

# Configure via environment variables
os.environ['SERVICE_NAME'] = 'my-app'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['LOG_FORMAT'] = 'json'
os.environ['LOG_FILE'] = 'logs/app.json.log'

logger = get_logger(__name__)

@timed(logger)
async def process_data(data: dict, correlation_id: str):
    with with_correlation_id(correlation_id):
        logger.info("Starting data processing", data_id=data['id'])

        try:
            # ... processing logic ...
            logger.info("Data processing complete", success=True)
        except Exception as e:
            logger.error("Data processing failed", error=str(e), exc_info=True)
            raise
```

### Complete TypeScript Example

```typescript
// apps/my-app/src/index.ts
import { getLogger, withCorrelationId, timingMiddleware } from '@cernji/logging';

// Configure via environment variables
process.env.SERVICE_NAME = 'my-app';
process.env.LOG_LEVEL = 'info';
process.env.LOG_FORMAT = 'json';
process.env.LOG_FILE = 'logs/app.json.log';

const logger = getLogger('my-app');

// Add timing middleware
app.use(timingMiddleware(logger));

// Handle requests with correlation ID
app.post('/events', async (req) => {
  const correlationId = req.headers['x-correlation-id'] || generateCorrelationId();

  await withCorrelationId(correlationId, async () => {
    logger.info({ eventType: req.body.event_type }, 'Received event');

    try {
      // ... event processing ...
      logger.info({ success: true }, 'Event processed');
    } catch (error) {
      logger.error({ error }, 'Event processing failed');
      throw error;
    }
  });
});
```
