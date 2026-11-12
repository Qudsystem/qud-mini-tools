@echo off
chcp 65001 >nul
color 0E
echo ===================================================
echo 🐉 Dragon S1 Installer Compiler (PyInstaller)
echo ===================================================
echo.
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Compiling gui_installer.py to a single EXE...
pyinstaller --onefile --noconsole --clean --name="DragonS1_Setup" --icon=NONE gui_installer.py

echo.
if exist "dist\DragonS1_Setup.exe" (
    move /Y "dist\DragonS1_Setup.exe" "."
    echo.
    echo ===================================================
    echo ✅ SUCCESS! Created "DragonS1_Setup.exe" in root.
    echo ===================================================
) else (
    echo.
    echo ❌ FAILED to build the installer executable.
)
pause
