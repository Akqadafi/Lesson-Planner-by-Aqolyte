@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Missing .venv. Run setup_and_run.bat first.
    exit /b 1
)

".venv\Scripts\python.exe" app.py
