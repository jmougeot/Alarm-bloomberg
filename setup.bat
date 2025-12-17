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
    echo [INFO] Python n'est pas detecte, installation en cours...
    echo.
    
    :: Telecharger Python 3.13
    echo [INFO] Telechargement de Python 3.13...
    curl -L -o "%TEMP%\python-3.13.exe" https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe
    
    if not exist "%TEMP%\python-3.13.exe" (
        echo [ERREUR] Echec du telechargement de Python
        echo Veuillez installer Python manuellement depuis https://www.python.org/
        pause
        exit /b 1
    )
    
    :: Installer Python silencieusement avec PATH
    echo [INFO] Installation de Python 3.13 ^(cela peut prendre quelques minutes^)...
    "%TEMP%\python-3.13.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    
    :: Rafraichir le PATH
    echo [INFO] Rafraichissement du PATH...
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python313\;%LOCALAPPDATA%\Programs\Python\Python313\Scripts\;%PATH%"
    
    :: Nettoyer
    del "%TEMP%\python-3.13.exe" >nul 2>&1
    
    :: Verifier l'installation
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERREUR] L'installation de Python a echoue
        echo Veuillez installer Python manuellement depuis https://www.python.org/
        pause
        exit /b 1
    )
    
    echo [OK] Python 3.13 installe avec succes!
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
echo [INFO] Tentative d'installation de blpapi 
python -m pip install blpapi `
  --index-url https://blpapi.bloomberg.com/repository/releases/python/simple/ `
  --trusted-host blpapi.bloomberg.comecho [OK]

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
