@echo off
echo Starting Japanese Tutor Screenshot Watcher...
echo.

REM Note: ANTHROPIC_API_KEY can be set in .env file or environment
REM The script will automatically load from .env via python-dotenv

REM Run the watcher with UV (handles dependencies automatically)
uv run screenshot_watcher.py

pause
