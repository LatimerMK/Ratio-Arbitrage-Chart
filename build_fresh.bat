@echo off
:: ─────────────────────────────────────────────────────────────
:: build_fresh.bat — Clean build from scratch (no existing .venv)
:: Use this if you just cloned the project from Git
:: Run from the project root: .\build_fresh.bat
:: Version is read from version.txt — change it only there
:: ─────────────────────────────────────────────────────────────

:: Read version from version.txt
set /p APP_VERSION=<version.txt
set APP_NAME=RatioArbitrageChart_%APP_VERSION%

:: Check that Python is available
echo [BUILD] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Create new .venv in the project root if it does not exist
echo [BUILD] Creating virtual environment .venv...
if exist ".venv" (
    echo [BUILD] .venv already exists, skipping creation...
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
)

:: Activate .venv
echo [BUILD] Activating virtual environment...
call .venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Failed to activate .venv
    pause
    exit /b 1
)

:: Install dependencies
echo [BUILD] Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

:: Install PyInstaller
echo [BUILD] Installing PyInstaller...
pip install pyinstaller --quiet

:: Build
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