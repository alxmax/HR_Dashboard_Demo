@echo off
setlocal
chcp 65001 >nul 2>&1

:: ============================================================
::  RUN PEOPLE PIPELINE - HR analytics demo
::  [1] build_people_analytics.py  ->  data\*.json
::  [2] open dashboard_demo.html in default browser
:: ============================================================

set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"
set "HTML=%BASE%\dashboard_demo.html"

echo.
echo ============================================================
echo   People Analytics - pipeline rebuild
echo ============================================================
echo   Folder: %BASE%
echo   Date:   %date% %time%
echo ============================================================
echo.

cd /d "%BASE%"

echo [1/2] python scripts\build_people_analytics.py
echo       Regenerating data\*.json...
echo.
python scripts\build_people_analytics.py
set "PY_EXIT=%errorlevel%"
if not "%PY_EXIT%"=="0" (
    echo.
    echo   [ERROR] build_people_analytics.py exited with code %PY_EXIT%.
    echo.
    pause
    exit /b 1
)
echo.
echo   [OK] Pipeline complete.
echo.

if not exist "%HTML%" (
    echo   [ERROR] dashboard_demo.html not found at:
    echo       %HTML%
    pause
    exit /b 1
)

echo [2/2] Opening dashboard_demo.html ...
start "" "%HTML%"

echo.
echo ============================================================
echo   Dashboard launched. Press any key to close this window.
echo ============================================================
pause >nul

endlocal
