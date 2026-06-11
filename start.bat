@echo off
echo Killing port 8000...
PowerShell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { taskkill /PID $_.OwningProcess /F }"
timeout /t 2 /nobreak

echo Starting Backend...
start cmd /k "cd /d C:\Users\nithi\OneDrive\Desktop\skysecure project\zoho-project-chatbot && set PYTHONPATH=%CD% && ..\venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak

echo Starting Frontend...
start cmd /k "cd /d C:\Users\nithi\OneDrive\Desktop\skysecure project\frontend && npm run dev"

echo Done! Open http://localhost:5173
pause