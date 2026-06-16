# PyInstaller spec for SnowTrip Desktop
# Build with:  pyinstaller desktop_app/build.spec --noconfirm --clean

# Note: this file is interpreted by PyInstaller; don't run as plain Python.
# Run from repo root so paths resolve cleanly.

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# SPECPATH is set by PyInstaller to the dir containing this .spec file (desktop_app/).
# Resolve repo root one level up so bundled data + scripts are correctly located.
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

# Bundled read-only resources copied into _MEIPASS root
datas = [
    (os.path.join(REPO_ROOT, 'urls.json'), '.'),
    (os.path.join(REPO_ROOT, 'http_scraper.py'), '.'),
    (os.path.join(REPO_ROOT, 'scraper.py'), '.'),
    (os.path.join(REPO_ROOT, 'flight_search'), 'flight_search'),
    (os.path.join(REPO_ROOT, 'web', 'airport_codes.py'), '.'),
]

hidden = [
    'httpx', 'bs4', 'openpyxl', 'tkinter',
    # flight_search backends loaded by name
    'flight_search.backends.fast_flights_backend',
    'flight_search.backends.serpapi_backend',
    'flight_search.backends.amadeus_backend',
    'flight_search.backends.travelpayouts_backend',
    'flight_search.backends.mock_backend',
] + collect_submodules('openpyxl') + collect_submodules('desktop_app')

# Also bundle the desktop_app package as data (PyInstaller sometimes drops the
# __init__.py in frozen mode when only loaded via absolute import).
datas.append((os.path.join(REPO_ROOT, 'desktop_app'), 'desktop_app'))

a = Analysis(
    [os.path.join(REPO_ROOT, 'desktop_app', 'main.py')],
    pathex=[REPO_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'playwright',  # http_scraper uses httpx only; we skip Playwright to shrink exe
        'pytest', 'sphinx', 'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='snowtrip_desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # windowed app — no console flash
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
