@echo off
REM Build snowtrip_desktop.exe via PyInstaller.
REM Run from repo root: .\desktop_app\build_exe.bat

setlocal ENABLEDELAYEDEXPANSION

REM Prefer the project venv
set PY=.venv\Scripts\python.exe
if not exist %PY% (
    echo .venv 不存在，改用系統 python
    set PY=python
)

echo === ensuring PyInstaller is installed ===
%PY% -m pip install --quiet --upgrade pyinstaller pyinstaller-hooks-contrib

echo === building exe via desktop_app\build.spec ===
%PY% -m PyInstaller desktop_app\build.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo ❌ build 失敗
    exit /b 1
)

echo.
echo ✅ build 完成
echo   exe:  dist\snowtrip_desktop.exe
echo   執行: dist\snowtrip_desktop.exe
echo   排程: dist\snowtrip_desktop.exe --headless --task ski
endlocal
