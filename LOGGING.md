# Logging & Observability Guide

Centralized logging infrastructure for Cernji Agents using ELK Stack and standardized logging libraries.

## Overview

This project uses a **hybrid observability architecture**:

- **ELK Stack** (Elasticsearch + Kibana + Filebeat) for powerful log search, visualization, and historical analytics
- **Cernji Logging Libraries** (Python + TypeScript) for structured JSON logging with correlation tracking
- **Observability Server** for real-time event streaming and workflow triggering

## Quick Start (5 minutes)

### 1. Start the ELK Stack

```bash
cd docker/elk
docker-compose up -d

# Wait ~30 seconds for services to start
docker-compose ps
```

Verify Elasticsearch is healthy:
```bash
curl http://localhost:9200/_cluster/health?pretty
```

### 2. Add Logging to Your App

#### Python App

```bash
# From your app directory (e.g., apps/resume-agent/)
uv add cernji-logging --path ../../libs/cernji-logging-py --editable
```

```python
# app.py
import os
from cernji_logging import get_logger, with_correlation_id

# Configure
os.environ['SERVICE_NAME'] = 'resume-agent'
os.environ['LOG_FILE'] = 'logs/app.json.log'

logger = get_logger(__name__)

# Use it
logger.info("Application started", version="1.0.0")

# With correlation ID for request tracking
with with_correlation_id("req-12345"):
    logger.info("Processing request")
```

#### TypeScript App

```bash
# From your app directory (e.g., apps/observability-server/)
bun add @cernji/logging@workspace:*
```

```typescript
// app.ts
import { getLogger, withCorrelationId } from '@cernji/logging';

// Configure
process.env.SERVICE_NAME = 'observability-server';
process.env.LOG_FILE = 'logs/app.json.log';

const logger = getLogger('observability-server');

// Use it
logger.info({ userId: 123 }, 'User logged in');

// With correlation ID
await withCorrelationId('req-12345', async () => {
  logger.info('Processing request');
});
```

### 3. Create Log Directory

```bash
# From your app directory
mkdir -p logs
```

### 4. View Logs in Kibana

1. Open http://localhost:5601
2. Go to **Analytics** > **Discover**
3. Create Data View:
   - Pattern: `logs-*`
   - Time field: `@timestamp`
4. Search your logs!

**Search by correlation ID**:
```
trace.id: "req-12345"
```

**Search by service**:
```
service.name: "resume-agent"
```

**Search for errors**:
```
log.level: "error"
```

## Architecture

### Log Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Applications                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Python Apps  │  │TypeScript Apps│  │ Other Apps   │     │
│  │ (structlog)  │  │   (pino)      │  │              │     │
│  └──────┬───────┘  └──────┬────────┘  └──────┬───────┘     │
│         │                  │                   │             │
│         └──────────────────┼───────────────────┘             │
│                            │                                 │
│                  Write JSON logs to files                    │
│                  (logs/app.json.log)                         │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Filebeat (Docker)   │
                  │   Watches log files   │
                  │   Ships to ES         │
                  └──────────┬────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Elasticsearch         │
                  │ Indexes & stores logs │
                  │ 30-day retention      │
                  └──────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │               │
              ▼              ▼               ▼
      ┌──────────┐   ┌──────────┐  ┌────────────────┐
      │  Kibana  │   │   APM    │  │ Alerting       │
      │ Search & │   │ Tracing  │  │ → Webhooks     │
      │  Dashboards│  │          │  │ → Workflows    │
      └──────────┘   └──────────┘  └────────┬───────┘
                                             │
                                             ▼
                                  ┌──────────────────┐
                                  │ Observability    │
                                  │ Server           │
                                  │ (WebSocket)      │
                                  └──────────────────┘
```

### Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Elasticsearch** | Search & analytics engine | 9200 |
| **Kibana** | Visualization & alerting UI | 5601 |
| **Filebeat** | Log shipper (files → ES) | - |
| **APM Server** | Distributed tracing | 8200 |
| **Observability Server** | Real-time events & workflows | 4000 |

## Features

### 1. Structured JSON Logging

All logs use Elastic Common Schema (ECS) format:

```json
{
  "@timestamp": "2025-11-15T10:30:00.123Z",
  "log.level": "info",
  "message": "Processing request",
  "ecs.version": "8.11.0",
  "service.name": "resume-agent",
  "service.version": "1.0.0",
  "service.environment": "production",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "custom_field": "custom_value"
}
```

### 2. Correlation ID Tracking

Track requests across services with correlation IDs:

```python
# Python
from cernji_logging import with_correlation_id, get_correlation_id

with with_correlation_id("req-12345"):
    logger.info("Service A")
    call_service_b(correlation_id=get_correlation_id())
```

```typescript
// TypeScript
import { withCorrelationId, getCorrelationId } from '@cernji/logging';

await withCorrelationId('req-12345', async () => {
  logger.info('Service B');
  await callServiceC({ correlationId: getCorrelationId() });
});
```

Then search in Kibana:
```
trace.id: "req-12345"
```

### 3. Performance Timing

Automatically log function execution time:

```python
# Python
from cernji_logging import timed

@timed(logger)
async def expensive_operation():
    # ... code ...
    pass
# Logs: { "function": "expensive_operation", "duration_ms": 1234.5 }
```

```typescript
// TypeScript
import { Timed } from '@cernji/logging';

class MyService {
  @Timed()
  async expensiveOperation() {
    // ... code ...
  }
}
// Logs: { "function": "expensiveOperation", "duration_ms": 1234.5 }
```

### 4. Kibana Alerting → Agent Workflows

Set up alerts in Kibana that trigger agent workflows:

1. **Create Alert Rule** in Kibana (Stack Management > Alerts)
2. **Condition**: `log.level:error AND service.name:resume-agent`
3. **Threshold**: > 10 errors in 5 minutes
4. **Action**: Webhook to `http://host.docker.internal:4000/alerts/trigger`

The observability server receives the webhook and can trigger agent workflows to investigate and remediate issues.

## Configuration

### Environment Variables

Set these in your app's `.env` or environment:

```bash
# Required
SERVICE_NAME=resume-agent

# Optional (defaults shown)
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/app.json.log
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
```

### Log Levels

- **TRACE** - Very detailed debugging (rarely used)
- **DEBUG** - Detailed debugging information
- **INFO** - General informational messages (default)
- **WARN** - Warning messages (potential issues)
- **ERROR** - Error messages (failures)
- **FATAL** - Critical errors (application crash)

## Common Tasks

### Search for Errors Across All Services

```
log.level: "error" AND @timestamp >= "now-1h"
```

### Find All Logs for a Specific Request

```
trace.id: "550e8400-e29b-41d4-a716-446655440000"
```

### Monitor Performance of Slow Operations

```
duration_ms > 1000 AND @timestamp >= "now-1h"
```

### View Logs from Specific Service

```
service.name: "resume-agent" AND @timestamp >= "now-1h"
```

### Create Dashboard for Service Health

1. Go to **Analytics** > **Dashboard**
2. Create new dashboard
3. Add visualizations:
   - **Line chart**: Error rate over time
   - **Metric**: Total requests
   - **Data table**: Top errors
   - **Bar chart**: Requests by service

## Troubleshooting

### Logs not appearing in Kibana

**Check 1: Are log files being created?**
```bash
ls -la apps/*/logs/
tail -f apps/resume-agent/logs/app.json.log
```

**Check 2: Is Filebeat running?**
```bash
docker ps | grep filebeat
docker logs cernji-filebeat
```

**Check 3: Can Filebeat reach Elasticsearch?**
```bash
docker exec cernji-filebeat filebeat test output
```

**Check 4: Are indices being created?**
```bash
curl localhost:9200/_cat/indices?v | grep logs
```

### Correlation IDs not showing up

**Python**: Make sure you're using the context manager:
```python
# ✓ Correct
with with_correlation_id("my-id"):
    logger.info("test")

# ✗ Wrong
set_correlation_id("my-id")
logger.info("test")  # Won't work without context manager
```

**TypeScript**: Make sure you're using async function:
```typescript
// ✓ Correct
await withCorrelationId('my-id', async () => {
  logger.info('test');
});

// ✗ Wrong
withCorrelationId('my-id', () => {  // Missing async
  logger.info('test');
});
```

### Elasticsearch out of memory

Increase Docker memory:
- **Windows/Mac**: Docker Desktop > Settings > Resources > Memory (set to 8+ GB)
- **Linux**: Edit `/etc/docker/daemon.json`

### Filebeat permission errors

Make sure log directories are readable:
```bash
chmod -R 755 apps/*/logs/
```

## Best Practices

### 1. Always Use Correlation IDs

Generate at entry points (HTTP endpoints, message queue consumers):

```python
# HTTP endpoint
correlation_id = request.headers.get('X-Correlation-ID') or generate_correlation_id()
with with_correlation_id(correlation_id):
    # All logs will include trace.id
    process_request()
```

### 2. Log Structured Data

**Good** - Structured fields:
```python
logger.info("User created", user_id=123, email="user@example.com")
```

**Bad** - String interpolation:
```python
logger.info(f"User created: {user_id}, {email}")  # Hard to search!
```

### 3. Use Appropriate Log Levels

- `INFO` for normal business operations
- `WARN` for potential issues (degraded performance, retries)
- `ERROR` for failures that need attention
- `DEBUG` for troubleshooting information

### 4. Include Context in Errors

```python
try:
    process_job(job_id)
except Exception as e:
    logger.error(
        "Job processing failed",
        job_id=job_id,
        error=str(e),
        exc_info=True  # Include stack trace
    )
    raise
```

### 5. Time Expensive Operations

```python
@timed(logger)
async def database_query():
    # ... slow operation ...
    pass
```

This helps identify performance bottlenecks.

## Resources

- **Libraries Documentation**: [libs/README.md](libs/README.md)
- **Python Library**: [libs/cernji-logging-py/README.md](libs/cernji-logging-py/README.md)
- **TypeScript Library**: [libs/cernji-logging-ts/README.md](libs/cernji-logging-ts/README.md)
- **ELK Stack Setup**: [docker/elk/README.md](docker/elk/README.md)
- **Elasticsearch Documentation**: https://www.elastic.co/guide/
- **Kibana Documentation**: https://www.elastic.co/guide/en/kibana/

## Next Steps

1. ✅ Start ELK Stack (`cd docker/elk && docker-compose up -d`)
2. ✅ Add cernji-logging to your apps
3. ✅ Configure environment variables
4. ✅ Create log directories
5. ✅ Run your apps and generate logs
6. ✅ Create Kibana data view (`logs-*`)
7. ⬜ Set up Kibana dashboards
8. ⬜ Configure alerting rules
9. ⬜ Integrate with agent workflows

Happy logging! 🚀
