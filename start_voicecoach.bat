@echo off
cd /d %~dp0
set PYTHONIOENCODING=utf-8
echo Starting VoiceCoach API on port 8000...
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause
