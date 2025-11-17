# Cernji Logging (Python)

Standardized structured logging library for Cernji Agents ecosystem.

## Features

- **Structured JSON logging** with Elastic Common Schema (ECS) format
- **Correlation ID tracking** for distributed tracing
- **Performance timing** decorator for instrumentation
- **Environment-based configuration** (dev vs. production)
- **Async-safe** context management

## Installation

```bash
# From within a Cernji Agents app
uv add cernji-logging --path ../../libs/cernji-logging-py --editable
```

## Quick Start

```python
from cernji_logging import get_logger, with_correlation_id, timed

# Get a logger instance
logger = get_logger(__name__)

# Basic logging
logger.info("Application started", service_version="1.0.0")

# With correlation ID context
with with_correlation_id("req-12345"):
    logger.info("Processing request")  # Automatically includes correlation_id

# Time expensive operations
@timed(logger)
async def expensive_operation():
    # Your code here
    pass
```

## Configuration

Set via environment variables:

- `LOG_LEVEL` - Log level (DEBUG, INFO, WARN, ERROR) [default: INFO]
- `LOG_FORMAT` - Output format (json, text) [default: json]
- `LOG_FILE` - Log file path [default: stdout]
- `SERVICE_NAME` - Service name for ECS format [required]
- `SERVICE_VERSION` - Service version [optional]
- `ENVIRONMENT` - Environment name (dev, staging, prod) [default: dev]

## API Reference

### `get_logger(name: str) -> BoundLogger`

Get a logger instance for the given name (typically `__name__`).

### `with_correlation_id(correlation_id: str) -> ContextManager`

Context manager that sets correlation ID for all logs within the context.

### `@timed(logger: BoundLogger, level: str = "info")`

Decorator that logs function execution time.

### `configure_logging(**kwargs)`

Manually configure logging (usually not needed, auto-configured from env vars).

## Output Format

All logs are output in ECS (Elastic Common Schema) format:

```json
{
  "@timestamp": "2025-11-15T10:30:00.123Z",
  "log.level": "info",
  "message": "Processing request",
  "ecs.version": "8.11.0",
  "service.name": "resume-agent",
  "service.version": "1.0.0",
  "service.environment": "production",
  "trace.id": "req-12345",
  "event.duration": 1234567890,
  "event.module": "resume_agent.analyzer",
  "custom_field": "custom_value"
}
```

## Examples

See `examples/` directory for complete usage examples.
