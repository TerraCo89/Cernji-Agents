# Kibana Alerts - Quick Reference

## Setup Summary

**Status**: ✅ Ready to configure
**Script**: `scripts/setup-kibana-alerts.ps1`
**Test Errors**: 48 errors generated in Elasticsearch

## Webhook Connector

**Name**: Error Analysis Webhook
**URL**: `http://host.docker.internal:4000/alerts/trigger`
**Method**: POST
**Headers**: `Content-Type: application/json`

## Alert Rules

### 1. High Error Rate - Resume Agent

**Trigger**: > 10 errors in 5 minutes
**Service**: resume-agent
**Check**: Every 1 minute

**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "log.level": "error" } },
        { "term": { "service.name": "resume-agent" } }
      ]
    }
  }
}
```

**Webhook Payload**:
```json
{
  "alert_id": "{{alert.id}}",
  "alert_name": "{{rule.name}}",
  "service": "resume-agent",
  "error_count": "{{context.hits}}",
  "severity": "high",
  "timestamp": "{{date}}",
  "time_range": "5m"
}
```

### 2. Critical Error Patterns

**Trigger**: > 3 critical errors in 1 minute
**Service**: All
**Types**: ModuleNotFoundError, ImportError, ConnectionError, TimeoutError

**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "log.level": "error" } },
        { "terms": { "error.type.keyword": [
          "ModuleNotFoundError",
          "ImportError",
          "ConnectionError",
          "TimeoutError"
        ]}}
      ]
    }
  }
}
```

**Webhook Payload**:
```json
{
  "alert_id": "{{alert.id}}",
  "alert_name": "{{rule.name}}",
  "service": "all",
  "error_count": "{{context.hits}}",
  "severity": "high",
  "timestamp": "{{date}}",
  "time_range": "1m"
}
```

### 3. Agent Chat UI - High Error Rate (Optional)

**Trigger**: > 10 errors in 5 minutes
**Service**: agent-chat-ui
**Check**: Every 1 minute

Same query pattern as #1, but with `"service.name": "agent-chat-ui"`.

## Quick Actions

### Open Kibana
```
http://localhost:5601
```

### Navigate to Rules
```
Stack Management → Rules and Connectors → Rules
```

### Check Execution History
1. Click on rule name
2. Go to "Execution history" tab
3. Look for "active" status

### View Alerts in Observability Server
```powershell
curl http://localhost:4000/events/recent?limit=10
```

### Generate Test Errors
```powershell
uv run scripts/generate_test_errors.py
```

### Trigger Manual Test
```powershell
curl -X POST "http://localhost:4000/alerts/trigger" `
  -H "Content-Type: application/json" `
  -d '{
    "alert_id": "manual-test",
    "alert_name": "Manual Test Alert",
    "service": "resume-agent",
    "error_count": 25,
    "severity": "high",
    "time_range": "5m"
  }'
```

## Verification Checklist

- [ ] Webhook connector created and tested
- [ ] Alert rule #1 created (High Error Rate - Resume Agent)
- [ ] Alert rule #2 created (Critical Error Patterns)
- [ ] Test errors generated (48 errors in Elasticsearch)
- [ ] Waited 90+ seconds for Kibana to check
- [ ] Checked Kibana execution history
- [ ] Verified observability server received webhook
- [ ] Confirmed error analysis ran
- [ ] Reviewed analysis results

## Expected Workflow

```
Error occurs → Elasticsearch indexes → Kibana detects (every 1 min)
                                            ↓
                                  Threshold exceeded?
                                            ↓
                                 Webhook → Observability Server
                                            ↓
                                 Severity check & throttle
                                            ↓
                                   Trigger analysis script
                                            ↓
                                 Query ELK → Classify → Generate Linear issue data
                                            ↓
                                       Log results
```

## Troubleshooting

### Encryption Key Missing Error

**Error**: "Unable to create alerts client because the Encrypted Saved Objects plugin is missing encryption key"

**Symptoms**:
- 500 errors when accessing Kibana alerting features
- Error in Kibana logs: `plugins.streams` or `alerting-plugin` errors
- Cannot create or manage alert rules

**Cause**: Container created before encryption keys were added to docker-compose.yml

**Verify the issue**:
```bash
# Run verification script
bash ./docker/elk/scripts/verify-kibana-config.sh

# Or manually check
docker exec cernji-kibana bash -c 'env | grep XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY'
```

If the command returns nothing, keys are missing.

**Fix**:
```bash
cd docker/elk
docker-compose down kibana
docker-compose up -d kibana

# Wait 30-60 seconds for startup
docker logs -f cernji-kibana
# Press Ctrl+C when you see: "Server running at http://0.0.0.0:5601"
```

**Verify fix**:
```bash
bash ./docker/elk/scripts/verify-kibana-config.sh
# Should show: ✅ All encryption keys configured!
```

**Note**: The encryption keys ARE defined in `docker-compose.yml` (lines 44-46). The issue is that Docker containers only pick up environment variables at creation time, not when restarted.

### Alert Not Triggering

**Check**:
```powershell
# Verify errors exist
curl "http://localhost:9200/logs-resume-agent-*/_search?q=log.level:error" | python -m json.tool
```

**Fix**: Adjust threshold or time window in Kibana rule

### Webhook Not Received

**Check**:
```powershell
# Test webhook manually
curl -X POST "http://localhost:4000/alerts/trigger" `
  -H "Content-Type: application/json" `
  -d '{"alert_id":"test","service":"test","error_count":1,"severity":"high"}'
```

**Fix**: Check observability server is running on port 4000

### Analysis Not Running

**Check**: Observability server logs for error messages

**Fix**: Verify Python script runs manually:
```powershell
uv run apps/observability-server/scripts/trigger_error_analysis.py `
  --alert-json '{"alert_id":"test","service":"resume-agent","error_count":20,"severity":"high"}'
```

## Adjusting Thresholds

### Too Sensitive (Too many alerts)

1. Increase error count threshold (e.g., 10 → 20)
2. Increase time window (e.g., 5m → 10m)
3. Adjust check frequency (e.g., 1m → 5m)

### Not Sensitive Enough (Missing errors)

1. Decrease error count threshold (e.g., 10 → 5)
2. Decrease time window (e.g., 5m → 2m)
3. Add more specific error patterns

## Production Recommendations

1. **Start Conservative**: High thresholds initially
2. **Monitor for 1 week**: Observe normal error rates
3. **Adjust Gradually**: Lower thresholds based on data
4. **Per-Service Rules**: Create separate rules for each service
5. **Business Hours**: Consider time-based rules (higher tolerance at night)

## Files Reference

- **Setup Script**: `scripts/setup-kibana-alerts.ps1`
- **Full Guide**: `docker/elk/kibana-alerts.md`
- **Test Generator**: `scripts/generate_test_errors.py`
- **Observability Server**: `apps/observability-server/src/index.ts`
- **Analysis Script**: `apps/observability-server/scripts/trigger_error_analysis.py`

## Current Status (as of setup)

- ✅ Observability server running on port 4000
- ✅ Elasticsearch running with 48 test errors
- ✅ Kibana running and accessible
- ✅ Test errors generated in `logs-resume-agent-2025.11.17`
- ⏳ Awaiting manual Kibana UI configuration
- ⏳ Awaiting first automatic alert trigger

---

**Next**: Follow the setup script instructions to create the webhook and alert rules in Kibana UI, then monitor for automatic alerts!
