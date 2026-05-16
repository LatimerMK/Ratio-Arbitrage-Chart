@echo off
:: ─────────────────────────────────────────────────────────────
:: build.bat — Build Ratio Arbitrage Chart into .exe
:: Run from the project root: .\build.bat
:: Version is read from version.txt — change it only there
:: ─────────────────────────────────────────────────────────────

:: Read version from version.txt
set /p APP_VERSION=<version.txt
set APP_NAME=RatioArbitrageChart_%APP_VERSION%

:: Activate .venv from the project root
echo [BUILD] Activating virtual environment...
call .venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Failed to activate .venv. Check path: .venv\Scripts\activate.bat
    pause
    exit /b 1
)

echo [BUILD] Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet

echo [BUILD] Installing/updating PyInstaller...
pip install pyinstaller --quiet

echo [BUILD] Building %APP_NAME%...
pyinstaller ratio_arb_chart.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

:: Remove temporary build\ folder
echo [BUILD] Cleaning up temporary build\ folder...
rmdir /s /q build

echo.
echo [BUILD] Done!
echo Output: dist\%APP_NAME%\%APP_NAME%.exe
echo.
pause