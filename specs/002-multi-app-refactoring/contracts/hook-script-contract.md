# Hook Script Contract

## Purpose

This document defines the contract for hook scripts (`.claude/hooks/send_event.py`) that send events to the observability server.

## Script Signature

### Command Line Interface

```bash
uv run .claude/hooks/send_event.py \
  --source-app <app_name> \
  --event-type <event_type> \
  [--summarize] \
  [--session-id <uuid>] \
  [--metadata <json_string>]
```

### Parameters

| Parameter | Required | Type | Description | Example |
|-----------|----------|------|-------------|---------|
| `--source-app` | Yes | string | Application identifier | `resume-agent` |
| `--event-type` | Yes | enum | Event type | `PreToolUse` |
| `--summarize` | No | flag | Use AI to summarize payload | N/A (flag) |
| `--session-id` | No | UUID | Session identifier | `550e8400-e29b-41d4-a716-446655440000` |
| `--metadata` | No | JSON | Additional context as JSON string | `'{"query": "SELECT *"}'` |

### Event Types

Valid values for `--event-type`:

- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - User submitted a prompt
- `SessionStart` - Claude Code session started
- `SessionEnd` - Claude Code session ended
- `Notification` - General notification
- `Stop` - Session stopped
- `SubagentStop` - Subagent stopped
- `PreCompact` - Before context compaction

## Input

### Environment Variables (provided by Claude Code hooks)

The hook script receives stdin data from Claude Code that varies by hook type:

```json
// PreToolUse hook stdin
{
  "tool_name": "mcp__sqlite__query",
  "parameters": {
    "sql": "SELECT * FROM portfolio_library WHERE technologies LIKE '%RAG%'",
    "values": []
  }
}

// PostToolUse hook stdin
{
  "tool_name": "mcp__sqlite__query",
  "result": {
    "rows": [...],
    "columns": [...]
  }
}

// UserPromptSubmit hook stdin
{
  "prompt": "Help me apply to this job: https://example.com/job"
}
```

### Reading Input

```python
import sys
import json

# Read from stdin
input_data = json.loads(sys.stdin.read())
```

## Output

### Exit Codes

| Exit Code | Meaning | Impact |
|-----------|---------|--------|
| 0 | Success - event sent | Continue normally |
| 1-255 | Error - event not sent | Log error, continue (non-blocking) |

### Stdout/Stderr

**Stdout**: Should be empty or contain debug info (not displayed to user)
**Stderr**: Error messages (logged but don't block execution)

### Example Output (Stderr)

```
[ERROR] Failed to send event to observability-server: Connection refused (http://localhost:4000/events)
[WARNING] Observability server not running, event discarded
```

## Behavior Contract

### Performance Requirements

- **Timeout**: Script MUST complete within 100ms
- **Non-blocking**: Script MUST NOT block agent operation if observability-server is down
- **Retry**: No retries - fire-and-forget pattern

### Error Handling

```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post(
        'http://localhost:4000/events',
        json=event_data,
        timeout=0.1  # 100ms timeout
    )
    response.raise_for_status()
except RequestException as e:
    # Log error to stderr, exit with 0 (don't fail agent operation)
    print(f"[ERROR] Failed to send event: {e}", file=sys.stderr)
    sys.exit(0)  # Non-zero would fail the hook
```

### AI Summarization (--summarize flag)

When `--summarize` flag is present:

1. Extract payload from stdin
2. Use Claude API to generate concise summary (max 200 characters)
3. Include summary in event payload
4. If summarization fails, use raw data or generic message

**Example**:

```python
if args.summarize:
    # Use Claude API to summarize tool parameters
    summary = summarize_with_claude(input_data)  # "Querying portfolio for RAG examples"
else:
    # Use tool name or generic message
    summary = f"{input_data.get('tool_name', 'Unknown')} called"
```

## HTTP Request Contract

### Request to Observability Server

```http
POST /events HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "timestamp": "2025-10-21T10:30:45.123Z",
  "source_app": "resume-agent",
  "event_type": "PreToolUse",
  "tool_name": "mcp__sqlite__query",
  "summary": "Querying portfolio_library table for RAG examples",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": "{\"query\": \"SELECT * FROM portfolio_library WHERE technologies LIKE '%RAG%'\"}"
}
```

### Expected Response

**Success (201 Created)**:

```json
{
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
```

**Error (400 Bad Request)**:

```json
{
  "error": "ValidationError",
  "message": "Invalid event_type: must be one of [PreToolUse, PostToolUse, ...]"
}
```

## Example Implementation

### Full Script Example

```python
#!/usr/bin/env python3
"""
Hook script to send events to observability server.

Usage:
  uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PreToolUse [--summarize]
"""

import sys
import json
import argparse
from datetime import datetime, timezone
import requests
from requests.exceptions import RequestException

SERVER_URL = "http://localhost:4000/events"
TIMEOUT = 0.1  # 100ms


def parse_args():
    parser = argparse.ArgumentParser(description="Send event to observability server")
    parser.add_argument("--source-app", required=True, help="Application identifier")
    parser.add_argument("--event-type", required=True, help="Event type")
    parser.add_argument("--summarize", action="store_true", help="Use AI to summarize payload")
    parser.add_argument("--session-id", help="Session UUID")
    parser.add_argument("--metadata", help="Additional metadata as JSON string")
    return parser.parse_args()


def read_stdin():
    """Read and parse stdin data from Claude Code hook."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return {}


def generate_summary(input_data, event_type, summarize=False):
    """Generate event summary."""
    if summarize:
        # TODO: Implement AI summarization with Claude API
        pass

    # Fallback: extract tool name or use generic message
    tool_name = input_data.get("tool_name", "")
    if tool_name:
        return f"{tool_name} - {event_type}"
    return f"{event_type} event"


def send_event(event_data):
    """Send event to observability server."""
    try:
        response = requests.post(SERVER_URL, json=event_data, timeout=TIMEOUT)
        response.raise_for_status()
        return True
    except RequestException as e:
        print(f"[ERROR] Failed to send event: {e}", file=sys.stderr)
        return False


def main():
    args = parse_args()
    input_data = read_stdin()

    # Build event payload
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_app": args.source_app,
        "event_type": args.event_type,
        "summary": generate_summary(input_data, args.event_type, args.summarize),
    }

    # Add optional fields
    if "tool_name" in input_data:
        event["tool_name"] = input_data["tool_name"]
    if args.session_id:
        event["session_id"] = args.session_id
    if args.metadata:
        event["metadata"] = args.metadata
    elif input_data:
        # Use input_data as metadata if no explicit metadata provided
        event["metadata"] = json.dumps(input_data)

    # Send event (non-blocking, don't fail on error)
    send_event(event)
    sys.exit(0)  # Always exit 0 (success) to not block agent


if __name__ == "__main__":
    main()
```

## Contract Tests

### Test Cases

1. **Successful Event Send**
   - Given: Observability server is running
   - When: Hook script is called with valid parameters
   - Then: Event is received by server, script exits with 0

2. **Server Unavailable**
   - Given: Observability server is NOT running
   - When: Hook script is called
   - Then: Error logged to stderr, script exits with 0 (non-blocking)

3. **Timeout**
   - Given: Observability server is slow (>100ms response)
   - When: Hook script is called
   - Then: Request times out, error logged, script exits with 0

4. **Invalid Parameters**
   - Given: Hook script called with missing required parameter
   - When: Script runs
   - Then: Argument parser error, script exits with 2 (argparse default)

5. **Stdin Parsing**
   - Given: Hook receives valid JSON on stdin
   - When: Script reads stdin
   - Then: Data correctly parsed and included in event metadata

### Sample Test (pytest)

```python
def test_send_event_success(mock_requests, capsys):
    """Test successful event send."""
    # Mock successful HTTP response
    mock_requests.post.return_value.status_code = 201

    # Run script
    sys.argv = ["send_event.py", "--source-app", "resume-agent", "--event-type", "PreToolUse"]
    main()

    # Verify
    assert mock_requests.post.called
    captured = capsys.readouterr()
    assert captured.err == ""  # No errors
```

## Version

**Version**: 1.0.0
**Last Updated**: 2025-10-21
