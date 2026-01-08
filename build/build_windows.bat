@echo off
REM =============================================================================
REM Build Script for Strategy Monitor - Windows
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
set APP_NAME=Strategy Monitor
set BUILD_DIR=%~dp0
set PROJECT_ROOT=%BUILD_DIR%..
set DIST_DIR=%PROJECT_ROOT%\dist
set SPEC_FILE=%BUILD_DIR%strategy_monitor.spec

echo ================================================
echo    Building %APP_NAME% for Windows
echo ================================================
echo.

REM 1. Check Python
echo [1/5] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo   + %PYTHON_VERSION%

REM 2. Check/install PyInstaller
echo [2/5] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo   Installing PyInstaller...
    pip install pyinstaller
)
echo   + PyInstaller ready

REM 3. Install dependencies
echo [3/5] Checking dependencies...
cd /d "%PROJECT_ROOT%"
pip install -r requirements.txt -q
echo   + Dependencies installed

REM 4. Clean previous builds
echo [4/5] Cleaning previous builds...
if exist "%BUILD_DIR%temp" rmdir /s /q "%BUILD_DIR%temp"
if exist "%DIST_DIR%\%APP_NAME%.exe" del /q "%DIST_DIR%\%APP_NAME%.exe"
if exist "%DIST_DIR%\%APP_NAME%" rmdir /s /q "%DIST_DIR%\%APP_NAME%"
echo   + Cleaned

REM 5. Build with PyInstaller
echo [5/5] Building application...
echo.

cd /d "%PROJECT_ROOT%"
python -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --workpath "%BUILD_DIR%temp" ^
    --distpath "%DIST_DIR%" ^
    "%SPEC_FILE%"

echo.

REM Check result
if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo ================================================
    echo    + Build successful!
    echo ================================================
    echo.
    echo Application: %DIST_DIR%\%APP_NAME%.exe
    echo.
    echo To run:
    echo   "%DIST_DIR%\%APP_NAME%.exe"
    echo.
) else (
    echo ================================================
    echo    X Build failed!
    echo ================================================
    exit /b 1
)

endlocal
