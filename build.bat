@echo off
:: ─────────────────────────────────────────────────────────────
:: build.bat — збірка Tick Chart Pro у .exe
:: Запускати з папки deploy\: .\build.bat
:: Версія береться з version.txt — змінюй тільки там
:: ─────────────────────────────────────────────────────────────

:: Читаємо версію з version.txt
set /p APP_VERSION=<version.txt
set APP_NAME=TickChartPro_%APP_VERSION%

:: Активуємо .venv з кореня проекту
echo [BUILD] Активація віртуального середовища...
call ..\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Не вдалося активувати .venv. Перевір шлях: ..\.venv\Scripts\activate.bat
    pause
    exit /b 1
)

echo [BUILD] Встановлення залежностей з requirements.txt...
pip install -r ..\requirements.txt --quiet

echo [BUILD] Встановлення/оновлення PyInstaller...
pip install pyinstaller --quiet

echo [BUILD] Збірка %APP_NAME%...
pyinstaller tick_chart.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] Помилка збірки PyInstaller
    pause
    exit /b 1
)

:: Копіюємо конфіг-файли поруч з .exe
echo [BUILD] Копіювання конфіг-файлів...
if not exist "dist\%APP_NAME%\config.json"  copy /Y "config.json"  "dist\%APP_NAME%\"
if not exist "dist\%APP_NAME%\proxies.json" copy /Y "proxies.json" "dist\%APP_NAME%\"

:: Прибираємо тимчасову папку build\
echo [BUILD] Очищення тимчасової папки build\...
rmdir /s /q build

echo.
echo [BUILD] Готово!
echo Результат: dist\%APP_NAME%\%APP_NAME%.exe
echo.
pause