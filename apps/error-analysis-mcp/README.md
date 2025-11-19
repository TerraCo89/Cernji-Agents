# Error Analysis MCP Server

Elasticsearch integration for error pattern detection and analysis.

## Overview

Single-file MCP server that provides tools for querying Elasticsearch to analyze application errors, detect patterns, and identify trends. Used by the **Error Analysis & Prevention Agent** to understand and prevent recurring errors.

## Architecture

```
ELK Stack (Elasticsearch) ←→ Error Analysis MCP ←→ Claude Desktop/Code
                                        ↓
                            Error Analyzer Skill
                                        ↓
                        ┌───────────────┼───────────────┐
                        ▼               ▼               ▼
                   Immediate Fix   Linear Issue   Knowledge Base
```

## Features

### Tools Provided

1. **`search_errors`** - Search for errors in logs
   - Filter by time range, service, log level
   - Returns sorted error list with context

2. **`get_error_patterns`** - Detect recurring error patterns
   - Aggregates similar error messages
   - Identifies most common patterns
   - Helps distinguish systemic issues from one-offs

3. **`get_error_context`** - Get full context for an error
   - Uses trace ID (correlation ID) to find related logs
   - Provides complete execution flow
   - Essential for root cause analysis

4. **`analyze_error_trend`** - Time-series analysis of errors
   - Creates histogram of error counts
   - Identifies spikes and trends
   - Helps detect when problems started

5. **`compare_errors`** - Compare two errors for similarity
   - Finds common attributes
   - Identifies if errors are related
   - Useful for pattern recognition

6. **`health_check`** - Verify Elasticsearch connection
   - Tests connectivity
   - Returns cluster information
   - Helps diagnose integration issues

## Installation

### Prerequisites

- Elasticsearch 9.x running on `http://localhost:9200`
- ELK stack configured (see `docker/elk/docker-compose.yml`)
- UV package manager (for running MCP server)

### Configuration

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "error-analysis": {
      "type": "stdio",
      "command": "cmd",
      "args": [
        "/c",
        "uv",
        "run",
        "apps\\error-analysis-mcp\\error_analysis_mcp.py"
      ],
      "env": {
        "ELASTICSEARCH_URL": "http://localhost:9200"
      }
    }
  }
}
```

### Dependencies

Managed via UV inline script dependencies:
- `fastmcp>=2.0` - MCP server framework
- `httpx>=0.28.0` - HTTP client for Elasticsearch
- `python-dotenv>=1.0.0` - Environment configuration

## Usage

### Manual Testing

Run the MCP server directly:

```bash
uv run apps/error-analysis-mcp/error_analysis_mcp.py
```

### With Claude Desktop/Code

Once configured in `.mcp.json`, use via MCP tools:

```python
# Search for recent errors
mcp__error_analysis__search_errors(
    time_range="1h",
    service="resume-agent",
    log_level="error"
)

# Get error patterns
mcp__error_analysis__get_error_patterns(
    time_range="24h",
    min_occurrences=3
)

# Get full error context
mcp__error_analysis__get_error_context(
    trace_id="abc-123-def-456"
)
```

### With Error Analyzer Skill

The primary use case is via the `error-analyzer` skill:

```bash
# In Claude Code session
/analyze-error
Error: ModuleNotFoundError: No module named 'fastmcp'
Service: resume-agent
```

The skill will:
1. Use MCP tools to query ELK stack
2. Analyze error patterns and trends
3. Search knowledge base for solutions
4. Propose fixes and create Linear issues

## Log Format

Expected Elastic Common Schema (ECS) format:

```json
{
  "@timestamp": "2025-11-17T10:00:00.000Z",
  "log.level": "error|warn|info|debug",
  "message": "Error message",
  "service.name": "resume-agent",
  "service.type": "python|typescript",
  "trace.id": "correlation-id",
  "error.type": "ModuleNotFoundError",
  "error.stack_trace": "...",
  "host.name": "...",
  "process.pid": 12345,
  "ecs.version": "8.11.0"
}
```

## Elasticsearch Query Patterns

### Time Range Parsing

Supports human-readable time ranges:
- `15m` - Last 15 minutes
- `1h` - Last 1 hour
- `24h` - Last 24 hours
- `7d` - Last 7 days

### Index Pattern

Searches across all log indices: `logs-*`

Daily indices format: `.ds-logs-{service-name}-YYYY.MM.DD-000001`

### Aggregations

Uses Elasticsearch aggregations for:
- Error pattern detection (terms aggregation on `message.keyword`)
- Error type distribution (terms aggregation on `error.type.keyword`)
- Time-series histograms (date histogram on `@timestamp`)

## Development

### Adding New Tools

Follow this pattern:

```python
@mcp.tool()
async def my_new_tool(
    param1: str,
    param2: Optional[int] = None
) -> dict:
    """
    Tool description for Claude.

    Args:
        param1: Description
        param2: Optional description

    Returns:
        Dictionary with result data
    """
    # Build Elasticsearch query
    query = {...}

    # Execute query
    result = await query_elasticsearch(query)

    # Format and return results
    return {...}
```

### Testing Queries

Test Elasticsearch queries directly:

```bash
# Test connection
curl http://localhost:9200

# Search errors
curl -X POST "http://localhost:9200/logs-*/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{"size": 10, "query": {"term": {"log.level": "error"}}}'
```

## Integration with ELK Stack

### Log Collection Flow

```
Application (Python/TypeScript)
    ↓ (writes JSON logs)
Filebeat (log shipper)
    ↓ (ingests logs)
Elasticsearch (indexes logs)
    ↓ (queried by)
Error Analysis MCP
    ↓ (used by)
Claude Code Agent
```

### Required ELK Components

- **Elasticsearch**: Document store and search engine
- **Filebeat**: Log shipper (collects logs from `/var/log/*/`)
- **Kibana**: Visualization and alerting (optional for MCP, required for automatic monitoring)

### Kibana Alerting

For automatic error detection:

1. Create Kibana alert rule (high error rate)
2. Configure webhook to `http://localhost:4000/alerts/trigger`
3. Observability server triggers Error Analysis Agent
4. Agent uses this MCP server to analyze errors

## Troubleshooting

### Connection Errors

```bash
# Check Elasticsearch is running
docker ps | grep elasticsearch

# Test connection
curl http://localhost:9200

# Check MCP server health
# (via Claude Desktop MCP inspector or direct tool call)
mcp__error_analysis__health_check()
```

### No Errors Found

Verify logs are being indexed:

```bash
# List indices
curl "http://localhost:9200/_cat/indices/logs-*?v"

# Check document count
curl "http://localhost:9200/logs-*/_count"
```

### Query Timeout

Adjust timeout in `query_elasticsearch()`:

```python
async with httpx.AsyncClient(timeout=30.0) as client:  # Increase if needed
```

## Related Components

- **`.claude/skills/error-analyzer/`** - Error analysis workflow
- **`.claude/commands/analyze-error.md`** - Slash command for manual analysis
- **`apps/observability-server/`** - Event tracking and Kibana alert webhook
- **`docker/elk/`** - ELK stack configuration
- **`libs/cernji-logging-{py,ts}/`** - Structured logging libraries

## Security

**Development Mode**: Elasticsearch security disabled for local development

**Production Recommendations**:
1. Enable `xpack.security.enabled=true` in Elasticsearch
2. Configure authentication (API key or basic auth)
3. Update MCP server to include credentials:
   ```json
   "env": {
     "ELASTICSEARCH_URL": "https://elasticsearch:9200",
     "ELASTICSEARCH_API_KEY": "${ES_API_KEY}"
   }
   ```
4. Use HTTPS for Elasticsearch endpoint

## Performance

### Query Optimization

- Uses `size` parameter to limit results (default: 100)
- Sorts by `@timestamp` for faster queries
- Uses aggregations instead of retrieving all documents
- Leverages Elasticsearch index sharding

### Caching

Future enhancement: Add Redis caching for:
- Frequently queried error patterns
- Error trend data
- Recent error searches

## Future Enhancements

- [ ] Add machine learning for automatic error classification
- [ ] Implement error clustering (group similar errors automatically)
- [ ] Add anomaly detection (detect unusual error patterns)
- [ ] Create error dashboards (pre-built Kibana visualizations)
- [ ] Add multi-cluster support (query multiple Elasticsearch clusters)
- [ ] Implement error correlation (find related errors across services)

## License

Part of Cernji-Agents monorepo. See root LICENSE file.

## Author

Christopher Ernjiezer

## Version History

- **1.0.0** (2025-11-17): Initial release
  - 6 MCP tools for error analysis
  - ECS log format support
  - Integration with error-analyzer skill
