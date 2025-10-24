#!/bin/bash
# Stop LangGraph Resume Agent Server
# Unix/Linux/macOS Shell Script

echo "========================================="
echo "  Stopping LangGraph Resume Agent"
echo "========================================="
echo

# Find process listening on port 2024
PID=$(lsof -ti:2024)

if [ -z "$PID" ]; then
    echo "[INFO] No server found running on port 2024."
else
    echo "[INFO] Found server process: $PID"
    echo "[INFO] Stopping gracefully..."

    # Try graceful shutdown first (SIGTERM)
    kill $PID 2>/dev/null

    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! kill -0 $PID 2>/dev/null; then
            echo "[SUCCESS] Server stopped gracefully."
            exit 0
        fi
        sleep 1
    done

    # Force kill if still running (SIGKILL)
    if kill -0 $PID 2>/dev/null; then
        echo "[WARNING] Graceful shutdown failed. Force killing..."
        kill -9 $PID 2>/dev/null
        sleep 1

        if ! kill -0 $PID 2>/dev/null; then
            echo "[SUCCESS] Server force stopped."
        else
            echo "[ERROR] Failed to stop server. Please check manually."
            exit 1
        fi
    fi
fi

# Verify server is stopped
if lsof -Pi :2024 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[WARNING] Port 2024 is still in use."
    echo "Check with: lsof -i :2024"
    exit 1
else
    echo "[SUCCESS] Port 2024 is now free."
fi

echo
