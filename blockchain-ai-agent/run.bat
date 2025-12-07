@echo off
REM Uvicorn startup script for Sui Blockchain AI Agent (Windows)

echo Starting Sui Blockchain AI Agent with Uvicorn...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Start uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
