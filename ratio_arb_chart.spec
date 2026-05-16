# tick_chart.spec
# ─────────────────────────────────────────────────────────────
# PyInstaller spec для Tick Chart Pro
# Запуск збірки: pyinstaller tick_chart.spec
# Версія береться з version.txt — змінюй тільки там
# ─────────────────────────────────────────────────────────────

import os
block_cipher = None

# Читаємо версію з version.txt
with open('version.txt', 'r') as _f:
    APP_VERSION = _f.read().strip()

APP_NAME    = f"TickChartPro_{APP_VERSION}"
PROJECT_DIR = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[
        # Вбудовані ресурси — потрапляють в _MEIPASS
        ('index_main.html', '.'),
        ('style.css',       '.'),
        ('script.js',       '.'),
        ('alert_sound',     'alert_sound'),
        ('version.txt',     '.'),
    ],
    hiddenimports=[
        # pywebview backends для Windows
        'webview.platforms.winforms',
        # python-socks
        'python_socks',
        'python_socks.async_',
        'python_socks.async_.asyncio',
        # aiohttp
        'aiohttp',
        'aiohttp.connector',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,       # без консольного вікна
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',   # розкоментуй якщо є іконка
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
