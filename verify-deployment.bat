@echo off
REM Pre-Deployment Verification Script for Windows
REM Run this before deploying to Render

echo ========================================
echo Pre-Deployment Verification
echo ========================================
echo.

set ERRORS=0
set WARNINGS=0
set SUCCESS=0

REM Check 1: .gitignore has .env
echo Checking .gitignore contains .env...
findstr /C:".env" .gitignore >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] .env in .gitignore
    set /a SUCCESS+=1
) else (
    echo [ERROR] .env NOT in .gitignore!
    set /a ERRORS+=1
)

REM Check 2: requirements.txt exists
echo Checking requirements.txt files...
if exist "requirements.txt" (
    echo [OK] VoiceCoach requirements.txt found
    set /a SUCCESS+=1
) else (
    echo [ERROR] requirements.txt missing
    set /a ERRORS+=1
)

if exist "web_chatbot-main\requirements.txt" (
    echo [OK] Chatbot requirements.txt found
    set /a SUCCESS+=1
) else (
    echo [ERROR] Chatbot requirements.txt missing
    set /a ERRORS+=1
)

REM Check 3: render.yaml exists
echo Checking render.yaml...
if exist "render.yaml" (
    echo [OK] render.yaml found
    set /a SUCCESS+=1
) else (
    echo [ERROR] render.yaml missing
    set /a ERRORS+=1
)

REM Check 4: Main Python files
echo Checking main Python files...
if exist "server.py" (
    echo [OK] server.py found
    set /a SUCCESS+=1
) else (
    echo [ERROR] server.py missing
    set /a ERRORS+=1
)

if exist "web_chatbot-main\app.py" (
    echo [OK] app.py found
    set /a SUCCESS+=1
) else (
    echo [ERROR] app.py missing
    set /a ERRORS+=1
)

REM Check 5: Database files
echo Checking database configuration...
if exist "core\database.py" (
    echo [OK] VoiceCoach database.py found
    set /a SUCCESS+=1
) else (
    echo [ERROR] core\database.py missing
    set /a ERRORS+=1
)

if exist "web_chatbot-main\database.py" (
    echo [OK] Chatbot database.py found
    set /a SUCCESS+=1
) else (
    echo [ERROR] web_chatbot-main\database.py missing
    set /a ERRORS+=1
)

REM Check 6: Gunicorn in requirements
echo Checking gunicorn in chatbot requirements...
findstr /C:"gunicorn" web_chatbot-main\requirements.txt >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] gunicorn found
    set /a SUCCESS+=1
) else (
    echo [WARN] gunicorn not found in requirements
    set /a WARNINGS+=1
)

REM Check 7: No .db files
echo Checking for database files...
if exist "*.db" (
    echo [WARN] Found .db files - make sure they're in .gitignore
    set /a WARNINGS+=1
) else (
    echo [OK] No .db files in root
    set /a SUCCESS+=1
)

REM Check 8: .env file should exist for local testing but not committed
echo Checking .env status...
if exist ".env" (
    echo [OK] .env exists for local testing
    set /a SUCCESS+=1
) else (
    echo [WARN] No .env file ^(OK if deploying without local testing^)
    set /a WARNINGS+=1
)

echo.
echo ========================================
echo Summary
echo ========================================
echo Passed: %SUCCESS%
echo Warnings: %WARNINGS%
echo Errors: %ERRORS%
echo.

if %ERRORS% GTR 0 (
    echo [FAILED] DEPLOYMENT BLOCKED - Fix errors above
    exit /b 1
) else if %WARNINGS% GTR 0 (
    echo [WARNING] Ready with warnings - Review before deploying
    echo.
    echo Next steps:
    echo 1. Review warnings above
    echo 2. git add .
    echo 3. git commit -m "Ready for Render deployment"
    echo 4. git push origin main
    echo 5. Deploy via Render Blueprint
    exit /b 0
) else (
    echo [SUCCESS] READY FOR DEPLOYMENT!
    echo.
    echo Next steps:
    echo 1. git add .
    echo 2. git commit -m "Ready for Render deployment"
    echo 3. git push origin main
    echo 4. Go to https://dashboard.render.com
    echo 5. New -^> Blueprint -^> Select your repo
    echo 6. Add API keys in environment variables
    exit /b 0
)
