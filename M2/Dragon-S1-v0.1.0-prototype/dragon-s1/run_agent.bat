@echo off
setlocal
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul
cd agent
if not exist .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run the DragonS1_Universal_Setup.exe first to install all dependencies.
    pause
    exit /b 1
)
call .venv\Scripts\activate
python main.py
pause
