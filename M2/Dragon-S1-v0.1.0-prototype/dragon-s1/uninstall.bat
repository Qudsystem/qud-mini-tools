@echo off
color 0C
echo ===================================================
echo Dragon S1 Uninstaller
echo ===================================================
echo.
echo WARNING: This will remove virtual environments and scheduled tasks.
echo.
set /p confirm="Are you sure you want to proceed? (Y/N): "
if /I "%confirm%" NEQ "Y" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo Removing Agent Scheduled Task (if exists)...
powershell -ExecutionPolicy Bypass -File scripts\uninstall_agent_task.ps1

echo Removing Server Virtual Environment...
if exist "server\.venv" (
    rmdir /S /Q "server\.venv"
    echo Removed server\.venv
)

echo Removing Agent Virtual Environment...
if exist "agent\.venv" (
    rmdir /S /Q "agent\.venv"
    echo Removed agent\.venv
)

set /p removedb="Do you want to delete the database file? (Y/N): "
if /I "%removedb%"=="Y" (
    if exist "server\dragon_s1.db" (
        del /Q "server\dragon_s1.db"
        echo Removed database.
    )
)

echo Uninstallation complete!
pause
