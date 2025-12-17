@echo off
title Strategy Price Monitor - Setup
color 0A
cd /d "%~dp0"

echo.
echo ============================================================
echo    STRATEGY PRICE MONITOR - Installation Complete
echo ============================================================
echo.

:: Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python depuis https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detecte
python --version
echo.

:: Installer les dependances directement (sans venv pour simplifier)
echo [INFO] Installation des dependances...
echo.

echo    - PySide6 (interface graphique)...
pip install PySide6 --quiet
echo    [OK] PySide6

echo    - pyqtgraph (graphiques)...
pip install pyqtgraph --quiet
echo    [OK] pyqtgraph

echo    - numpy...
pip install numpy --quiet
echo    [OK] numpy

echo    - pywin32 + winshell (raccourci Windows)...
pip install pywin32 winshell --quiet
echo    [OK] pywin32 + winshell

:: Creer le raccourci via script Python
echo.
echo [INFO] Creation du raccourci...
python src\create_shortcut.py

:: Tentative Bloomberg API
echo.
echo [INFO] Tentative d'installation de blpapi (optionnel)...
if exist "C:\blp\DAPI" (
    set BLPAPI_ROOT=C:\blp\DAPI
    pip install blpapi --quiet 2>nul
    if errorlevel 1 (
        echo    [INFO] blpapi non installe - Mode simulation actif
    ) else (
        echo    [OK] blpapi installe
    )
) else (
    echo    [INFO] Bloomberg SDK non trouve - Mode simulation actif
)

echo.
echo ============================================================
echo    INSTALLATION TERMINEE!
echo ============================================================
echo.
echo    Vous pouvez maintenant:
echo.
echo    1. Lancer depuis le Bureau: "Strategy Monitor"
echo    2. Chercher dans le Menu Demarrer: "Strategy Monitor"
echo    3. Ou double-cliquer sur "run.bat"
echo.
echo    Pour epingler a la barre des taches:
echo    - Clic droit sur l'icone Bureau ^> Epingler
echo.
echo ============================================================
echo.
pause
