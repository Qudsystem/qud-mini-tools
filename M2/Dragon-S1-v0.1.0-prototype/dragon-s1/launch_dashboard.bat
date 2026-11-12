@echo off
setlocal
cd /d "%~dp0"

:: Check if server .venv is installed
if not exist "server\.venv\Scripts\python.exe" (
    echo [ERROR] Server is not installed yet.
    echo Please run DragonS1_Universal_Setup.exe first.
    pause
    exit /b 1
)

:: Read PORT from .env (default 3001)
set PORT=3001
if exist ".env" (
    for /f "tokens=1,2 delims==" %%i in (.env) do (
        if "%%i"=="PORT" set PORT=%%j
    )
)

echo Starting Dragon S1 Security Server on port %PORT%...

:: Start server in a new minimized window
start "Dragon S1 Server" /MIN cmd /c "cd /d %~dp0 && server\.venv\Scripts\python.exe server\run.py"

echo Waiting for server to be ready...
timeout /t 3 /nobreak >nul

:: Wait until server responds (up to 30 seconds)
set RETRIES=0
:wait_loop
server\.venv\Scripts\python.exe -c "import urllib.request; urllib.request.urlopen('http://localhost:%PORT%/api/health')" >nul 2>&1
if not errorlevel 1 goto server_ready
set /a RETRIES=%RETRIES%+1
if %RETRIES% geq 10 goto server_timeout
timeout /t 2 /nobreak >nul
goto wait_loop

:server_timeout
echo [WARNING] Server took too long. Opening browser anyway...
goto open_browser

:server_ready
echo Server is ready!

:open_browser
echo Opening Dashboard at http://localhost:%PORT%
start http://localhost:%PORT%
