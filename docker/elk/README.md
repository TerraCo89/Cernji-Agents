# ELK Stack for Cernji Agents

Elasticsearch, Logstash, Kibana (ELK) stack for centralized logging and observability.

## Quick Start

### Start the Stack

```bash
cd docker/elk
docker-compose up -d
```

### Check Status

```bash
# Check all services
docker-compose ps

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health?pretty

# Check Kibana
curl http://localhost:5601/api/status
```

### Verify Encryption Keys

Kibana requires encryption keys for alerting and security features. Verify they're loaded:

**Linux/Mac**:
```bash
./docker/elk/scripts/verify-kibana-config.sh
```

**Windows (Git Bash)**:
```bash
bash ./docker/elk/scripts/verify-kibana-config.sh
```

**Windows (PowerShell - Manual Check)**:
```powershell
docker exec cernji-kibana bash -c 'env | grep XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY'
```

**Expected output**: Three XPACK_*_ENCRYPTIONKEY variables with values

**If keys are missing**:

The encryption keys are defined in `docker-compose.yml` (lines 44-46) but not loaded in the running container. This happens when the container was created before the keys were added.

**Fix**: Recreate the Kibana container:
```bash
cd docker/elk
docker-compose down kibana
docker-compose up -d kibana

# Wait 30-60 seconds for Kibana to start
docker logs -f cernji-kibana
# Look for: "Server running at http://0.0.0.0:5601"
```

Then verify again with the verification script.

### Access UIs

- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200
- **APM Server**: http://localhost:8200

### View Logs

```bash
# Elasticsearch logs
docker logs cernji-elasticsearch

# Kibana logs
docker logs cernji-kibana

# Filebeat logs
docker logs cernji-filebeat
```

## First Time Setup

### 1. Create Index Lifecycle Management Policy

After starting the stack, create the 30-day retention policy:

```bash
curl -X PUT "localhost:9200/_ilm/policy/logs-30day-retention?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_size": "50gb",
            "max_age": "1d"
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "14d",
        "actions": {
          "set_priority": {
            "priority": 0
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'
```

### 2. Access Kibana

1. Navigate to http://localhost:5601
2. Go to **Management** > **Stack Management** > **Index Management**
3. Verify logs indices are being created (logs-resume-agent-*, etc.)
4. Go to **Analytics** > **Discover** to explore logs

### 3. Create Data View

1. Go to **Management** > **Stack Management** > **Data Views**
2. Click **Create data view**
3. Name: `Cernji Logs`
4. Index pattern: `logs-*`
5. Time field: `@timestamp`
6. Click **Save**

### 4. Search Logs by Correlation ID

In Discover:

```
trace.id: "550e8400-e29b-41d4-a716-446655440000"
```

Or by service:

```
service.name: "resume-agent"
```

Or by error level:

```
log.level: "error"
```

## Kibana Alerting Setup

### Create Webhook Connector

1. Go to **Stack Management** > **Connectors**
2. Click **Create connector**
3. Select **Webhook**
4. Configure:
   - **Name**: Observability Server
   - **URL**: http://host.docker.internal:4000/alerts/trigger
   - **Method**: POST
   - **Authentication**: None
5. Click **Save**

### Create Alert Rule

1. Go to **Observability** > **Alerts**
2. Click **Create rule**
3. Configure:
   - **Name**: High Error Rate - Resume Agent
   - **Check every**: 1 minute
   - **Condition**: Custom KQL
   - **KQL**: `log.level:error AND service.name:resume-agent`
   - **Threshold**: Count > 10 in last 5 minutes
4. Under **Actions**:
   - Select **Webhook - Observability Server**
   - **Body**:
     ```json
     {
       "alert_id": "{{alert.id}}",
       "alert_name": "{{rule.name}}",
       "service": "{{context.service.name}}",
       "error_count": "{{context.hits.total}}",
       "timestamp": "{{context.timestamp}}",
       "severity": "high"
     }
     ```
5. Click **Save**

## Troubleshooting

### Elasticsearch won't start

Check memory limits:

```bash
# Increase Docker memory to at least 8GB
# On Windows: Docker Desktop > Settings > Resources
```

Check logs:

```bash
docker logs cernji-elasticsearch
```

### Filebeat not shipping logs

Check Filebeat logs:

```bash
docker logs cernji-filebeat
```

Test Filebeat configuration:

```bash
docker exec cernji-filebeat filebeat test config
docker exec cernji-filebeat filebeat test output
```

### No logs appearing in Kibana

1. Check if indices exist:
   ```bash
   curl localhost:9200/_cat/indices?v
   ```

2. Verify log files are being created in app directories

3. Check Filebeat is running:
   ```bash
   docker ps | grep filebeat
   ```

4. Manually create a test log:
   ```bash
   echo '{"@timestamp":"2025-11-15T10:00:00.000Z","message":"test","service.name":"test"}' \
     >> ../../apps/resume-agent/logs/app.json.log
   ```

## Stopping the Stack

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove all data (WARNING: deletes all logs!)
docker-compose down -v
```

## Resource Usage

| Service | Memory | CPU | Storage |
|---------|--------|-----|---------|
| Elasticsearch | 4 GB | 2 cores | 50 GB+ |
| Kibana | 2 GB | 1 core | 1 GB |
| Filebeat | 200 MB | 0.5 core | 100 MB |
| APM Server | 1 GB | 1 core | 1 GB |
| **Total** | **7.2 GB** | **4.5 cores** | **52+ GB** |

## Production Notes

For production deployment:

1. **Enable security**:
   ```yaml
   - xpack.security.enabled=true
   - ELASTIC_PASSWORD=your_strong_password
   ```

2. **Use multi-node cluster** (3+ nodes)

3. **Configure SSL/TLS**

4. **Set up monitoring and alerting**

5. **Configure backup/restore**

6. **Use dedicated storage volumes**

See [DEPLOYMENT.md](../../DEPLOYMENT.md) for production deployment guide.
