# Reliable backend startup script
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot "..\venv\Scripts\python.exe"
$Uvicorn = Join-Path $ProjectRoot "..\venv\Scripts\uvicorn.exe"

if (-not (Test-Path $Uvicorn)) {
    Write-Error "uvicorn not found. Run: pip install -r requirements.txt"
    exit 1
}

$env:PYTHONPATH = $ProjectRoot
$Port = 8002

Write-Host "Starting Zoho Project Chatbot on http://127.0.0.1:$Port"
Write-Host "PYTHONPATH=$ProjectRoot"
Write-Host "Press Ctrl+C to stop"
Write-Host ""

& $Uvicorn backend.main:app --host 127.0.0.1 --port $Port --reload --reload-dir "$ProjectRoot\backend"
