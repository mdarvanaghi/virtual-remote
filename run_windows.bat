@echo off
setlocal

set INPUT_BACKEND=windows

pip install -r requirements-windows.txt --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
