@echo off
REM Start script for Sui Blockchain AI Agent (Windows)

echo 🚀 Starting Sui Blockchain AI Agent...

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo 📋 Copying .env.example to .env...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your OPENAI_API_KEY
    echo ℹ️  Then run this script again
    exit /b 1
)

REM Start the server
echo 🎯 Starting FastAPI server...
python main.py

pause
