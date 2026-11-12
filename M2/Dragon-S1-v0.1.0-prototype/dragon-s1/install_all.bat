@echo off
color 0B
echo ===================================================
echo Dragon S1 Master Installer
echo ===================================================
echo.
echo What do you want to install?
echo 1) Server (Backend, API, Dashboard)
echo 2) Agent (Endpoint Client)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo Starting Server setup...
    call setup_server.bat
) else if "%choice%"=="2" (
    echo Starting Agent setup...
    call setup_agent.bat
) else (
    echo Invalid choice. Exiting.
    pause
    exit /b 1
)
