@echo off
REM VoiceCoach Platform - Local Development Startup Script
REM This script starts both services for local development

echo.
echo ========================================
echo VoiceCoach Platform - Starting Services
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file:
    echo   1. Copy .env.example to .env
    echo   2. Fill in required API keys
    echo.
    pause
    exit /b 1
)

echo [INFO] Loading environment from .env file...
for /f "tokens=*" %%a in ('type .env ^| findstr /v "^#" ^| findstr /v "^$"') do set %%a

echo.
echo ========================================
echo Starting VoiceCoach API (Port 8000)
echo ========================================
echo.
start "VoiceCoach API" cmd /k "set PORT=8000 && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Starting Web Chatbot (Port 5001)
echo ========================================
echo.
start "Web Chatbot" cmd /k "cd web_chatbot-main && set PORT=5001 && set FLASK_DEBUG=True && python app.py"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Services Started!
echo ========================================
echo.
echo VoiceCoach API:  http://localhost:8000
echo Web Chatbot:     http://localhost:5001
echo.
echo Press any key to open services in browser...
pause >nul

start http://localhost:8000
start http://localhost:5001

echo.
echo [INFO] To stop services, close both terminal windows
echo.
pause
