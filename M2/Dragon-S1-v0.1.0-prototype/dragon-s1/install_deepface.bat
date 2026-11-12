@echo off
setlocal
cd /d "%~dp0server"
if not exist .venv (
  echo Run run_server.bat once first.
  exit /b 1
)
call .venv\Scripts\activate
pip install -r requirements-deepface.txt
