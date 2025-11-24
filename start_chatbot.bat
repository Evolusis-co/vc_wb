@echo off
cd /d %~dp0\web_chatbot-main
set PYTHONIOENCODING=utf-8
set FLASK_APP=app.py
echo Starting Web Chatbot on port 5001...
python app.py
pause
