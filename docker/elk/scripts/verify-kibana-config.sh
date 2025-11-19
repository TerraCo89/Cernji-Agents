#!/bin/bash
# Kibana Configuration Verification Script
# Verifies that required encryption keys are loaded in the running Kibana container
#
# Usage: ./docker/elk/scripts/verify-kibana-config.sh
#
# Exit codes:
#   0 - All encryption keys configured correctly
#   1 - One or more encryption keys missing
#   2 - Kibana container not running

set -e

CONTAINER_NAME="cernji-kibana"
MISSING_KEYS=0

echo "=================================="
echo "Kibana Configuration Verification"
echo "=================================="
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ ERROR: Kibana container '${CONTAINER_NAME}' is not running"
    echo ""
    echo "Start the container with:"
    echo "  cd docker/elk"
    echo "  docker-compose up -d kibana"
    echo ""
    exit 2
fi

echo "✅ Kibana container is running"
echo ""
echo "Checking encryption keys..."
echo ""

# Check XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY
if docker exec "$CONTAINER_NAME" bash -c 'test -n "$XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY"' 2>/dev/null; then
    KEY_VALUE=$(docker exec "$CONTAINER_NAME" bash -c 'echo $XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY' 2>/dev/null)
    echo "✅ XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY: ${KEY_VALUE:0:8}... (${#KEY_VALUE} chars)"
else
    echo "❌ XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY: NOT SET"
    MISSING_KEYS=1
fi

# Check XPACK_REPORTING_ENCRYPTIONKEY
if docker exec "$CONTAINER_NAME" bash -c 'test -n "$XPACK_REPORTING_ENCRYPTIONKEY"' 2>/dev/null; then
    KEY_VALUE=$(docker exec "$CONTAINER_NAME" bash -c 'echo $XPACK_REPORTING_ENCRYPTIONKEY' 2>/dev/null)
    echo "✅ XPACK_REPORTING_ENCRYPTIONKEY: ${KEY_VALUE:0:8}... (${#KEY_VALUE} chars)"
else
    echo "❌ XPACK_REPORTING_ENCRYPTIONKEY: NOT SET"
    MISSING_KEYS=1
fi

# Check XPACK_SECURITY_ENCRYPTIONKEY
if docker exec "$CONTAINER_NAME" bash -c 'test -n "$XPACK_SECURITY_ENCRYPTIONKEY"' 2>/dev/null; then
    KEY_VALUE=$(docker exec "$CONTAINER_NAME" bash -c 'echo $XPACK_SECURITY_ENCRYPTIONKEY' 2>/dev/null)
    echo "✅ XPACK_SECURITY_ENCRYPTIONKEY: ${KEY_VALUE:0:8}... (${#KEY_VALUE} chars)"
else
    echo "❌ XPACK_SECURITY_ENCRYPTIONKEY: NOT SET"
    MISSING_KEYS=1
fi

echo ""

if [ $MISSING_KEYS -eq 0 ]; then
    echo "=================================="
    echo "✅ All encryption keys configured!"
    echo "=================================="
    echo ""
    exit 0
else
    echo "=================================="
    echo "❌ Missing encryption keys!"
    echo "=================================="
    echo ""
    echo "The encryption keys are defined in docker-compose.yml but not loaded"
    echo "in the running container. This happens when the container was created"
    echo "before the keys were added to the configuration."
    echo ""
    echo "FIX: Recreate the Kibana container:"
    echo ""
    echo "  cd docker/elk"
    echo "  docker-compose down kibana"
    echo "  docker-compose up -d kibana"
    echo ""
    echo "  # Wait 30-60 seconds for Kibana to start"
    echo "  docker logs -f cernji-kibana"
    echo ""
    echo "Then run this script again to verify."
    echo ""
    exit 1
fi
