@echo off
REM Start LangGraph Resume Agent Server
REM Windows Batch Script

echo =========================================
echo   Starting LangGraph Resume Agent
echo =========================================
echo.

REM Check if already running
tasklist /FI "WINDOWTITLE eq LangGraph*" 2>NUL | find /I /N "langgraph">NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARNING] LangGraph server may already be running.
    echo Check with: tasklist | findstr langgraph
    echo.
)

REM Navigate to script directory
cd /d "%~dp0"

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and configure your API keys.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import anthropic" 2>NUL
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    python -m pip install -e .
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [INFO] Starting LangGraph server...
echo.
echo API:       http://127.0.0.1:2024
echo Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
echo API Docs:  http://127.0.0.1:2024/docs
echo.
echo Press Ctrl+C to stop the server
echo =========================================
echo.

REM Start the server (this will block)
langgraph dev

REM If server exits
echo.
echo [INFO] LangGraph server stopped.
pause
