@echo off
echo Starting Japanese Tutor Screenshot Watcher...
echo.

REM Check if ANTHROPIC_API_KEY is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY environment variable is not set!
    echo Please set it first with: set ANTHROPIC_API_KEY=your_key_here
    echo.
    pause
    exit /b 1
)

REM Run the watcher
python screenshot_watcher.py

pause
