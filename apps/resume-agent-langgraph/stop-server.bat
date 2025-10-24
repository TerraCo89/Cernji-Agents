@echo off
REM Stop LangGraph Resume Agent Server
REM Windows Batch Script

echo =========================================
echo   Stopping LangGraph Resume Agent
echo =========================================
echo.

REM Find langgraph processes
echo [INFO] Looking for langgraph processes...

REM Method 1: Kill by process name
tasklist | findstr /I "langgraph" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Found langgraph processes. Stopping...
    taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq *langgraph*" 2>NUL
    timeout /t 2 /nobreak >NUL
)

REM Method 2: Kill by port (if listening on 2024)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":2024" ^| findstr "LISTENING"') do (
    echo [INFO] Killing process on port 2024: %%a
    taskkill /F /PID %%a 2>NUL
)

REM Verify server is stopped
timeout /t 1 /nobreak >NUL
netstat -aon | findstr ":2024" | findstr "LISTENING" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARNING] Server may still be running on port 2024
    echo Try running: netstat -ano | findstr :2024
) else (
    echo [SUCCESS] LangGraph server stopped successfully.
)

echo.
pause
