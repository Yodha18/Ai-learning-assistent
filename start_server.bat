@echo off
cd /d C:\Users\tanmay\ai_learning_assistant
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
