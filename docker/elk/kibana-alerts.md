# Kibana Alert Configuration for Error Analysis

This document explains how to configure Kibana alerts to automatically trigger the Error Analysis Agent when high error rates are detected.

## Prerequisites

- ELK stack running (`docker compose up -d` in `docker/elk/`)
- Observability server running on port 4000
- Error Analysis MCP server configured

## Alert Configuration Overview

Kibana alerts will:
1. Monitor error logs in Elasticsearch
2. Detect when error rate exceeds threshold
3. Send webhook to observability server
4. Trigger Error Analysis Agent automatically

## Creating Alert Rules

### Method 1: Via Kibana UI (Recommended)

#### 1. Access Kibana Alerting

1. Open Kibana: `http://localhost:5601`
2. Navigate to **Stack Management** → **Rules and Connectors**
3. Click **Create rule**

#### 2. Configure Error Detection Rule

**Rule Details**:
- **Name**: `High Error Rate - Resume Agent`
- **Tags**: `error-detection`, `automatic-analysis`
- **Check every**: `1 minute`
- **Notify**: `Immediately`

**Rule Type**: Select **Elasticsearch query**

**Index**: `logs-*`

**Time field**: `@timestamp`

**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "log.level": "error"
          }
        },
        {
          "term": {
            "service.name": "resume-agent"
          }
        }
      ]
    }
  }
}
```

**Threshold**:
- **When**: Count of matches
- **IS ABOVE**: `10` (adjust based on your needs)
- **For the last**: `5 minutes`

**Actions**:
1. Click **Add action**
2. Select **Webhook** connector (create if doesn't exist)

#### 3. Create Webhook Connector

**Connector Details**:
- **Name**: `Error Analysis Webhook`
- **URL**: `http://host.docker.internal:4000/alerts/trigger`
- **Method**: `POST`
- **Headers**:
  ```json
  {
    "Content-Type": "application/json"
  }
  ```

**Body** (JSON):
```json
{
  "alert_id": "{{alert.id}}",
  "alert_name": "{{rule.name}}",
  "service": "resume-agent",
  "error_count": "{{context.hits}}",
  "severity": "high",
  "timestamp": "{{date}}",
  "time_range": "5m",
  "query_context": {
    "rule_id": "{{rule.id}}",
    "rule_type": "{{rule.type}}",
    "space_id": "{{rule.spaceId}}"
  }
}
```

#### 4. Save and Enable

1. Click **Save**
2. Ensure rule is **Enabled**
3. Test by triggering errors in your application

### Method 2: Via Kibana API

Use this for automated setup or multiple services.

**Create Connector**:
```bash
curl -X POST "http://localhost:5601/api/actions/connector" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Error Analysis Webhook",
    "connector_type_id": ".webhook",
    "config": {
      "url": "http://host.docker.internal:4000/alerts/trigger",
      "method": "post",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }'
```

**Create Alert Rule**:
```bash
curl -X POST "http://localhost:5601/api/alerting/rule" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Error Rate - Resume Agent",
    "tags": ["error-detection", "automatic-analysis"],
    "rule_type_id": ".es-query",
    "consumer": "alerts",
    "schedule": {
      "interval": "1m"
    },
    "params": {
      "index": ["logs-*"],
      "timeField": "@timestamp",
      "esQuery": "{\"query\":{\"bool\":{\"must\":[{\"term\":{\"log.level\":\"error\"}},{\"term\":{\"service.name\":\"resume-agent\"}}]}}}",
      "size": 100,
      "threshold": [10],
      "timeWindowSize": 5,
      "timeWindowUnit": "m",
      "thresholdComparator": ">"
    },
    "actions": [
      {
        "group": "query matched",
        "id": "<CONNECTOR_ID>",
        "params": {
          "body": "{\"alert_id\":\"{{alert.id}}\",\"alert_name\":\"{{rule.name}}\",\"service\":\"resume-agent\",\"error_count\":\"{{context.hits}}\",\"severity\":\"high\",\"timestamp\":\"{{date}}\",\"time_range\":\"5m\"}"
        }
      }
    ]
  }'
```

## Recommended Alert Rules

### 1. High Error Rate (Any Service)

**Use case**: Detect sudden error spikes across all services

**Query**:
```json
{
  "query": {
    "term": {
      "log.level": "error"
    }
  }
}
```

**Threshold**: > 20 errors in 5 minutes
**Severity**: high
**Service**: Extract from logs dynamically

### 2. Critical Errors (Specific Pattern)

**Use case**: Detect specific critical error types

**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "log.level": "error"
          }
        },
        {
          "terms": {
            "error.type.keyword": [
              "ModuleNotFoundError",
              "ImportError",
              "ConnectionError"
            ]
          }
        }
      ]
    }
  }
}
```

**Threshold**: > 3 errors in 1 minute
**Severity**: high

### 3. New Error Pattern Detected

**Use case**: Detect errors that haven't occurred before

**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "log.level": "error"
          }
        }
      ],
      "must_not": [
        {
          "exists": {
            "field": "error.seen_before"
          }
        }
      ]
    }
  }
}
```

**Threshold**: > 0 (any new error)
**Severity**: medium

## Alert Severity Mapping

The observability server triggers error analysis based on severity:

| Condition | Severity | Triggers Analysis? |
|-----------|----------|-------------------|
| `severity === "high"` | high | ✅ Yes |
| `error_count > 10` | medium/high | ✅ Yes |
| `alert_name` contains "Critical" | high | ✅ Yes |
| All others | low/medium | ❌ No (but logged) |

## Throttling

To prevent spam, the observability server throttles analysis triggers:

- **Throttle window**: 5 minutes per service
- **Logic**: If analysis was triggered for a service < 5 minutes ago, skip
- **Per-service**: Throttling is independent per service

Example:
```
11:00:00 - resume-agent error spike → Analysis triggered
11:02:00 - resume-agent error spike → Throttled (2 min ago)
11:06:00 - resume-agent error spike → Analysis triggered (6 min ago)
11:03:00 - agent-chat-ui error → Analysis triggered (different service)
```

## Testing Alerts

### 1. Trigger Test Error

Create a test error in your application:

```python
# In any Python app
import logging
logging.error("TEST ERROR: This is a test error for Kibana alerting")
```

Or via curl:
```bash
# Send test error log to Filebeat
echo '{"@timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'","log.level":"error","message":"TEST ERROR","service.name":"resume-agent"}' >> /var/log/resume-agent/app.json.log
```

### 2. Trigger Multiple Errors

Use a script to generate error spike:

```bash
for i in {1..15}; do
  curl -X POST "http://localhost:4000/events" \
    -H "Content-Type: application/json" \
    -d "{
      \"source_app\": \"resume-agent\",
      \"session_id\": \"test-session-$i\",
      \"hook_event_type\": \"Error\",
      \"payload\": {
        \"error\": \"Test error $i\",
        \"level\": \"error\"
      }
    }"
done
```

### 3. Monitor Alert Execution

**Via Kibana**:
1. Go to **Stack Management** → **Rules and Connectors**
2. Click on your rule
3. View **Execution history**

**Via Observability Server**:
```bash
# Watch logs
cd apps/observability-server
bun run dev

# Look for:
# [Kibana Alert] Received alert: High Error Rate - Resume Agent
# [Kibana Alert] Triggering error analysis for alert: ...
# [Error Analysis] Analysis complete for resume-agent: { total_errors: 15, ... }
```

**Via Elasticsearch**:
```bash
# Check if analysis event was created
curl "http://localhost:4000/events/recent?limit=10" | python -m json.tool
```

### 4. Verify Analysis Results

Check observability server logs for:
```
[Error Analysis] Analysis complete for resume-agent: {
  total_errors: 15,
  patterns: 3,
  root_cause: 'configuration'
}
[Error Analysis] Linear issue ready: {
  title: '[CONFIGURATION] resume-agent: High Error Rate - Resume Agent',
  labels: [ 'error-prevention', 'automatic-detection', 'configuration' ]
}
```

## Troubleshooting

### Alert Not Triggering

**Check 1: Verify logs are indexed**
```bash
curl "http://localhost:9200/logs-*/_search?size=1&q=log.level:error&pretty"
```

**Check 2: Verify rule is enabled**
- Kibana → Rules and Connectors → Check status

**Check 3: Check rule execution history**
- Click on rule → View execution history
- Look for errors or conditions not met

### Webhook Not Received

**Check 1: Verify observability server is running**
```bash
curl http://localhost:4000/events/recent
```

**Check 2: Check Docker network**
```bash
# From inside Kibana container
docker exec -it <kibana-container> curl http://host.docker.internal:4000/events/recent
```

**Check 3: Check observability server logs**
```bash
# Should see:
# [Kibana Alert] Received alert: ...
```

### Analysis Not Triggered

**Check 1: Verify alert severity**
```bash
# In observability server logs, look for:
# [Kibana Alert] Alert stored with ID: X (analysis not triggered)
# vs
# [Kibana Alert] Triggering error analysis for alert: ...
```

**Check 2: Check throttling**
```bash
# Look for:
# [Error Analysis] Throttled analysis for resume-agent (triggered XXs ago)
```

**Check 3: Verify Python script works**
```bash
uv run apps/observability-server/scripts/trigger_error_analysis.py \
  --alert-json '{"alert_id":"test","service":"resume-agent","error_count":15,"severity":"high","timestamp":"2025-11-17T10:00:00Z"}'
```

## Next Steps

Once alerts are working:

1. **Phase 3**: Auto-create Linear issues (currently manual)
2. **Add more alert rules**: For different services and error patterns
3. **Tune thresholds**: Based on actual error rates
4. **Add Slack notifications**: For critical errors
5. **Create Kibana dashboards**: Visualize error trends

## Related Files

- `apps/observability-server/src/index.ts` - Webhook handler
- `apps/observability-server/scripts/trigger_error_analysis.py` - Analysis script
- `apps/error-analysis-mcp/error_analysis_mcp.py` - MCP server
- `.claude/skills/error-analyzer/skill.md` - Analysis workflow
