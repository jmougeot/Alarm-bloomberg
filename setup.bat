@echo off
title Strategy Price Monitor - Setup
color 0A

echo ============================================================
echo    Strategy Price Monitor - Installation automatique
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

:: Creer un environnement virtuel si necessaire
if not exist ".venv" (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv .venv
    echo [OK] Environnement virtuel cree
) else (
    echo [OK] Environnement virtuel existant
)
echo.

:: Activer l'environnement virtuel
echo [INFO] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

:: Mettre a jour pip
echo [INFO] Mise a jour de pip...
python -m pip install --upgrade pip --quiet

:: Installer les dependances
echo.
echo [INFO] Installation des dependances...
echo.

echo    - Installation de PySide6 (interface graphique)...
pip install PySide6 --quiet
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation de PySide6
) else (
    echo    [OK] PySide6 installe
)

echo    - Installation de pyqtgraph (graphiques temps reel)...
pip install pyqtgraph --quiet
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation de pyqtgraph
) else (
    echo    [OK] pyqtgraph installe
)

echo    - Installation de numpy...
pip install numpy --quiet
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation de numpy
) else (
    echo    [OK] numpy installe
)

:: Tentative d'installation de blpapi
echo.
echo [INFO] Tentative d'installation de blpapi (Bloomberg API)...
echo    Note: Necessite Bloomberg Terminal installe

:: Essayer avec BLPAPI_ROOT
if exist "C:\blp\DAPI" (
    set BLPAPI_ROOT=C:\blp\DAPI
    echo    [INFO] Bloomberg SDK detecte dans C:\blp\DAPI
    pip install blpapi --quiet 2>nul
    if errorlevel 1 (
        echo    [ATTENTION] Installation de blpapi echouee
        echo    L'application fonctionnera en mode simulation
    ) else (
        echo    [OK] blpapi installe
    )
) else (
    echo    [INFO] Bloomberg SDK non trouve
    echo    L'application fonctionnera en mode simulation
)

echo.
echo ============================================================
echo    Installation terminee!
echo ============================================================
echo.
echo Pour lancer l'application:
echo    1. Double-cliquez sur "run.bat"
echo    ou
echo    2. Executez: python main.py
echo.
echo ============================================================
pause
