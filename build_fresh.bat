@echo off
:: ─────────────────────────────────────────────────────────────
:: build_fresh.bat — збірка з нуля (без існуючого .venv)
:: Використовуй якщо щойно склонував проект з Git
:: Запускати з папки deploy\: .\build_fresh.bat
:: Версія береться з version.txt — змінюй тільки там
:: ─────────────────────────────────────────────────────────────

:: Читаємо версію з version.txt
set /p APP_VERSION=<version.txt
set APP_NAME=TickChartPro_%APP_VERSION%

:: Перевіряємо що Python доступний
echo [BUILD] Перевірка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не знайдено. Встанови Python 3.10+ та додай до PATH.
    pause
    exit /b 1
)

:: Створюємо нове .venv в корені проекту якщо не існує
echo [BUILD] Створення віртуального середовища .venv...
if exist "..\.venv" (
    echo [BUILD] .venv вже існує, пропускаємо створення...
) else (
    python -m venv ..\.venv
    if errorlevel 1 (
        echo [ERROR] Не вдалося створити .venv
        pause
        exit /b 1
    )
)

:: Активуємо .venv
echo [BUILD] Активація віртуального середовища...
call ..\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Не вдалося активувати .venv
    pause
    exit /b 1
)

:: Встановлюємо залежності
echo [BUILD] Встановлення залежностей з requirements.txt...
pip install -r ..\requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Помилка встановлення залежностей
    pause
    exit /b 1
)

:: Встановлюємо PyInstaller
echo [BUILD] Встановлення PyInstaller...
pip install pyinstaller --quiet

:: Збірка
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