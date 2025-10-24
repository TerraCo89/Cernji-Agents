#!/bin/bash
# Start LangGraph Resume Agent Server
# Unix/Linux/macOS Shell Script

set -e

echo "========================================="
echo "  Starting LangGraph Resume Agent"
echo "========================================="
echo

# Navigate to script directory
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Check if already running
if lsof -Pi :2024 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[WARNING] Port 2024 is already in use. Server may already be running."
    echo "Check with: lsof -i :2024"
    echo
fi

# Check if dependencies are installed
if ! python -c "import anthropic" 2>/dev/null; then
    echo "[INFO] Installing dependencies..."
    python -m pip install -e .
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies"
        exit 1
    fi
fi

echo "[INFO] Starting LangGraph server..."
echo
echo "API:       http://127.0.0.1:2024"
echo "Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo "API Docs:  http://127.0.0.1:2024/docs"
echo
echo "Press Ctrl+C to stop the server"
echo "========================================="
echo

# Start the server (this will block)
langgraph dev

# If server exits
echo
echo "[INFO] LangGraph server stopped."
