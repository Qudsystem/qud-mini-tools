@echo off
setlocal
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul 2>&1
cd server
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run DragonS1_Universal_Setup.exe first.
    pause
    exit /b 1
)
call .venv\Scripts\activate
python run.py
