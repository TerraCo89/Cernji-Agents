---
name: cernji-logging
description: Add structured JSON logging with ECS format, correlation ID tracking, and performance timing to Python or TypeScript projects. This skill should be used when implementing observability, replacing print/console.log statements, adding structured logging, or improving log aggregation for ELK stack integration.
---

# Cernji-Logging Implementation Skill

## Purpose

Add Cernji-Logging to existing Python or TypeScript projects to enable:
- Structured JSON logging in Elastic Common Schema (ECS) format
- Distributed tracing with correlation IDs
- Performance timing for functions and operations
- Unified log aggregation across services
- ELK stack compatibility for centralized monitoring

## When to Use This Skill

Use this skill when:
- Implementing structured logging in a new or existing project
- Replacing `print()` statements in Python or `console.log()` in TypeScript
- Adding observability and monitoring capabilities
- Migrating from basic logging to production-grade structured logging
- Setting up distributed tracing across microservices
- Preparing applications for ELK stack log aggregation
- Improving log searchability and analysis

## Implementation Workflow

### Step 1: Determine Project Language

Identify whether the target project is Python or TypeScript to select the appropriate library variant.

### Step 2: Install the Library

**For Python projects:**

```bash
# From the Python app directory (e.g., apps/my-app/)
uv add cernji-logging --path ../../libs/cernji-logging-py --editable
```

**For TypeScript projects:**

```bash
# Ensure workspace configuration in root package.json
# "workspaces": ["apps/*", "libs/*"]

# From the TypeScript app directory
bun add @cernji/logging@workspace:*
# OR
npm add @cernji/logging@workspace:*
```

### Step 3: Configure Environment Variables

Copy the `.env.example` file from `assets/examples/.env.example` to the project root and customize:

**Minimum required configuration:**
```bash
SERVICE_NAME=my-service-name
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Full configuration options:**
```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARN, ERROR
LOG_FORMAT=json             # json, text (Python), pretty (TypeScript)
LOG_FILE=logs/app.json.log  # Optional, defaults to stdout
SERVICE_NAME=my-service     # Required
SERVICE_VERSION=1.0.0       # Optional
ENVIRONMENT=production      # Optional: dev, staging, production
```

**Development vs Production:**
- Development: Use `LOG_FORMAT=text` (Python) or `LOG_FORMAT=pretty` (TypeScript) for readable output
- Production: Use `LOG_FORMAT=json` for log aggregation and `LOG_FILE` to write to disk

### Step 4: Create Log Directory (if using LOG_FILE)

If `LOG_FILE` is configured, create the log directory:

```bash
mkdir -p logs
```

### Step 5: Replace Existing Logging

**Python - Replace print() statements:**

Before:
```python
print(f"Processing user {user_id}")
print(f"Error: {error}")
```

After:
```python
from cernji_logging import get_logger

logger = get_logger(__name__)

logger.info("Processing user", user_id=user_id)
logger.error("Error occurred", error=str(error), exc_info=True)
```

**Python - Replace logging.basicConfig:**

Before:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

After:
```python
from cernji_logging import get_logger
logger = get_logger(__name__)  # Environment variables configure everything
```

**TypeScript - Replace console.log:**

Before:
```typescript
console.log('[Service] Processing request:', requestId);
console.error('Error occurred:', error);
```

After:
```typescript
import { getLogger } from '@cernji/logging';

const logger = getLogger('my-service');

logger.info({ requestId }, 'Processing request');
logger.error({ error }, 'Error occurred');
```

### Step 6: Add Correlation ID Support

For distributed tracing, implement correlation ID tracking at application entry points (HTTP endpoints, message handlers, etc.).

**Python HTTP endpoint example:**

```python
from cernji_logging import get_logger, with_correlation_id, generate_correlation_id

logger = get_logger(__name__)

@app.post("/api/endpoint")
async def endpoint(request):
    correlation_id = request.headers.get('X-Correlation-ID') or generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info("Processing request")
        # All logs within this context will include trace.id
        result = await process_request()
        logger.info("Request completed")

    return result
```

**TypeScript HTTP middleware example:**

```typescript
import { getLogger, withCorrelationId, generateCorrelationId } from '@cernji/logging';

const logger = getLogger('my-service');

app.use(async (req, res, next) => {
  const correlationId = req.headers['x-correlation-id'] || generateCorrelationId();

  res.setHeader('X-Correlation-ID', correlationId);

  await withCorrelationId(correlationId, async () => {
    next();
  });
});
```

### Step 7: Propagate Correlation IDs Across Services

When making HTTP requests to other services, propagate the correlation ID:

**Python:**

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

**TypeScript:**

```typescript
import { getCorrelationId } from '@cernji/logging';

async function callService() {
  const correlationId = getCorrelationId();
  const headers = correlationId ? { 'X-Correlation-ID': correlationId } : {};

  await fetch('http://other-service/api', { headers });
}
```

### Step 8: Add Performance Timing (Optional)

For performance monitoring, add timing decorators to expensive operations:

**Python:**

```python
from cernji_logging import get_logger, timed, TimingContext

logger = get_logger(__name__)

# Decorator approach
@timed(logger)
async def expensive_operation():
    # ... code ...
    pass

# Context manager approach
with TimingContext(logger, "database_query"):
    # ... code to time ...
    pass
```

**TypeScript:**

```typescript
import { getLogger, Timed, TimingContext } from '@cernji/logging';

class MyService {
  private logger = getLogger('my-service');

  // Decorator approach (requires logger property on class)
  @Timed()
  async expensiveOperation() {
    // ... code ...
  }

  // Manual timing approach
  async complexQuery() {
    const timer = new TimingContext(this.logger, 'complex_query');
    try {
      // ... code to time ...
    } finally {
      timer.end();
    }
  }
}
```

### Step 9: Test the Implementation

Verify the logging implementation:

1. **Check log output format:**
   - Development: Human-readable text/pretty format
   - Production: Valid JSON with ECS fields

2. **Verify correlation IDs:**
   - All logs within a request context should have the same `trace.id`
   - Correlation IDs should propagate across service calls

3. **Confirm timing metrics:**
   - Functions decorated with `@timed` should log `event.duration` in nanoseconds

4. **Test log levels:**
   - Ensure `DEBUG` logs only appear when `LOG_LEVEL=DEBUG`
   - Verify `ERROR` logs include stack traces when `exc_info=True` (Python)

### Step 10: Configure Log Aggregation (Optional)

For production environments with ELK stack:

1. Ensure `LOG_FORMAT=json` and `LOG_FILE` is set
2. Configure Filebeat to ship logs from `LOG_FILE` to Elasticsearch
3. Use correlation IDs to search logs: `trace.id: "550e8400-e29b-41d4-a716-446655440000"`

Refer to the project's `docker/elk/README.md` for ELK stack setup instructions.

## Usage Examples

### Quick Start Examples

Refer to the bundled example files for complete, copy-paste ready code:

- **`assets/examples/python_example.py`** - Comprehensive Python examples including:
  - Basic logging setup and usage
  - Correlation ID patterns
  - HTTP endpoint integration
  - Service-to-service communication
  - Performance timing
  - Class-based service examples
  - Migration patterns from print/logging

- **`assets/examples/typescript_example.ts`** - Comprehensive TypeScript examples including:
  - Basic logging setup and usage
  - Correlation ID patterns
  - Express and Fastify integration
  - Service-to-service communication
  - Performance timing with decorators
  - Class-based service examples
  - Migration patterns from console.log

### Environment Configuration

Copy `assets/examples/.env.example` to the project root as `.env` and customize the values.

## Common Patterns

### Pattern 1: HTTP Request Handling

**Python (FastAPI):**
```python
from cernji_logging import get_logger, with_correlation_id, generate_correlation_id

logger = get_logger(__name__)

@app.post("/api/endpoint")
async def endpoint(request):
    correlation_id = request.headers.get('X-Correlation-ID') or generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info("Processing request", path=request.url.path)
        result = await process()
        logger.info("Request completed")
        return result
```

**TypeScript (Express):**
```typescript
import { getLogger, withCorrelationId, generateCorrelationId } from '@cernji/logging';

const logger = getLogger('api-server');

app.use(async (req, res, next) => {
  const correlationId = req.headers['x-correlation-id'] || generateCorrelationId();
  await withCorrelationId(correlationId, async () => next());
});
```

### Pattern 2: Background Jobs/Workers

**Python:**
```python
from cernji_logging import get_logger, with_correlation_id, generate_correlation_id, timed

logger = get_logger(__name__)

@timed(logger)
async def process_job(job_data):
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info("Job started", job_id=job_data['id'])
        # ... processing ...
        logger.info("Job completed", job_id=job_data['id'])
```

**TypeScript:**
```typescript
import { getLogger, withCorrelationId, generateCorrelationId, Timed } from '@cernji/logging';

class JobProcessor {
  private logger = getLogger('job-processor');

  @Timed()
  async processJob(jobData: any) {
    const correlationId = generateCorrelationId();

    await withCorrelationId(correlationId, async () => {
      this.logger.info({ job_id: jobData.id }, 'Job started');
      // ... processing ...
      this.logger.info({ job_id: jobData.id }, 'Job completed');
    });
  }
}
```

### Pattern 3: Error Handling with Context

**Python:**
```python
logger = get_logger(__name__)

try:
    result = await risky_operation()
except ValueError as e:
    logger.error("Validation failed", error=str(e), exc_info=True)
    raise
except Exception as e:
    logger.error("Unexpected error", error=str(e), exc_info=True)
    raise
```

**TypeScript:**
```typescript
const logger = getLogger('my-service');

try {
  const result = await riskyOperation();
} catch (error) {
  logger.error({ error, context: 'additional_info' }, 'Operation failed');
  throw error;
}
```

## Troubleshooting

### Correlation IDs Not Appearing

**Python:** Ensure `with_correlation_id()` context manager is used:
```python
with with_correlation_id("my-id"):
    logger.info("test")  # Will include trace.id
```

**TypeScript:** Ensure `withCorrelationId()` is used with async function:
```typescript
await withCorrelationId('my-id', async () => {
  logger.info('test');  // Will include trace.id
});
```

### Performance Timing Not Working

**Python:** Logger must be passed to decorator:
```python
@timed(logger)  # Correct
async def func(): pass
```

**TypeScript:** Class must have `logger` property:
```typescript
class MyService {
  logger = getLogger('my-service');  // Required!

  @Timed()
  async method() { }
}
```

### Logs Not in JSON Format

Verify `LOG_FORMAT=json` in environment variables and restart the application.

### Logs Not Writing to File

1. Ensure `LOG_FILE` is set in environment variables
2. Verify log directory exists: `mkdir -p logs`
3. Check file permissions: `chmod 755 logs`

## Bundled Resources

### References

- **`references/cernji-logging-guide.md`**: Complete documentation covering installation, configuration, usage patterns, migration guides, and troubleshooting. Reference this file when implementing advanced features or resolving issues.

### Assets

#### Examples

- **`assets/examples/.env.example`**: Template environment configuration file. Copy this to the project root as `.env` and customize the values for the specific application.

- **`assets/examples/python_example.py`**: Comprehensive Python usage examples including basic logging, correlation IDs, HTTP integration, timing decorators, service patterns, and migration examples. Copy relevant sections to the application code.

- **`assets/examples/typescript_example.ts`**: Comprehensive TypeScript usage examples including basic logging, correlation IDs, Express/Fastify integration, timing decorators, service patterns, and migration examples. Copy relevant sections to the application code.

## Integration Notes

### Workspace Structure

The Cernji-Logging libraries are designed for monorepo structures with libraries in `libs/` directory:

```
project/
   libs/
      cernji-logging-py/   # Python library
      cernji-logging-ts/   # TypeScript library
   apps/
       my-python-app/
       my-typescript-app/
```

When installing the library, adjust the relative path based on the project structure.

### Dependencies

**Python requirements:**
- Python 3.10+
- structlog (automatically installed)

**TypeScript requirements:**
- Node.js 16+ or Bun
- pino (automatically installed)
- pino-pretty (dev dependency, automatically installed)

### ELK Stack Compatibility

Cernji-Logging outputs logs in Elastic Common Schema (ECS) format, compatible with:
- Elasticsearch for storage and search
- Filebeat for log shipping
- Kibana for visualization and dashboards
- Logstash for advanced log processing (optional)

For ELK stack setup, refer to the project's `docker/elk/` documentation.

## Best Practices

1. **Always use correlation IDs** - Generate at entry points (HTTP handlers, message processors)
2. **Propagate correlation IDs** - Include `X-Correlation-ID` header in service-to-service calls
3. **Use structured fields** - Pass data as key-value pairs, not formatted strings
4. **Time expensive operations** - Use `@timed` decorator for database queries, API calls
5. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARN: Warning messages for unusual conditions
   - ERROR: Error messages for failures (include `exc_info=True` in Python)
6. **Include context in errors** - Add relevant data to help with debugging
7. **Configure for environment** - Use text/pretty format in dev, JSON in production
8. **Create log directories** - Ensure LOG_FILE path exists before starting app

## Version Compatibility

This skill is compatible with:
- **cernji-logging-py**: All versions
- **@cernji/logging**: All versions

Both libraries maintain API compatibility and produce identical log structures.
