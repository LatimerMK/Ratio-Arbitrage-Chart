# ratio_arb_chart.spec
# ─────────────────────────────────────────────────────────────
# PyInstaller spec for Ratio Arbitrage Chart
# Run build: pyinstaller ratio_arb_chart.spec
# Version is read from version.txt — change it only there
# ─────────────────────────────────────────────────────────────

import os
block_cipher = None

# Read version from version.txt
with open('version.txt', 'r') as _f:
    APP_VERSION = _f.read().strip()

APP_NAME    = f"RatioArbitrageChart_{APP_VERSION}"
PROJECT_DIR = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[
        # Bundled resources — placed into _MEIPASS
        ('core',        'core'),
        ('ui',          'ui'),
        ('version.txt', '.'),
    ],
    hiddenimports=[
        # pywebview backend for Windows
        'webview.platforms.winforms',
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
    console=False,      # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
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
