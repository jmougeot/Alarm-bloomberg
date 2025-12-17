@echo off
title Strategy Price Monitor - Installation Complete
color 0A

echo.
echo ============================================================
echo    STRATEGY PRICE MONITOR - Installation Automatique
echo ============================================================
echo.
echo    Ce script va:
echo    1. Installer Python 3.13 (si necessaire)
echo    2. Telecharger l'application depuis GitHub
echo    3. Installer toutes les dependances
echo    4. Creer un raccourci sur le Bureau
echo.
echo ============================================================
echo.
pause

:: Definir le dossier d'installation
set "INSTALL_DIR=%USERPROFILE%\StrategyMonitor"

:: ============================================================
:: ETAPE 1: Verifier/Installer Python
:: ============================================================
echo.
echo [ETAPE 1/4] Verification de Python...
echo.

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
        echo Veuillez redemarrer l'ordinateur et relancer ce script
        pause
        exit /b 1
    )
    
    echo [OK] Python 3.13 installe avec succes!
) else (
    echo [OK] Python detecte
    python --version
)

:: ============================================================
:: ETAPE 2: Verifier/Installer Git et cloner le repo
:: ============================================================
echo.
echo [ETAPE 2/4] Telechargement de l'application...
echo.

:: Creer le dossier d'installation
if exist "%INSTALL_DIR%" (
    echo [INFO] Mise a jour de l'application existante...
    cd /d "%INSTALL_DIR%"
    
    :: Verifier si git est disponible
    git --version >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Git non disponible, telechargement direct...
        goto :download_zip
    )
    
    git pull origin main
    if errorlevel 1 (
        echo [INFO] Echec git pull, telechargement complet...
        cd /d "%USERPROFILE%"
        rmdir /s /q "%INSTALL_DIR%" 2>nul
        goto :download_zip
    )
    echo [OK] Application mise a jour!
    goto :install_deps
)

:download_zip
:: Telecharger le ZIP depuis GitHub (pas besoin de git)
echo [INFO] Telechargement depuis GitHub...

:: Utiliser PowerShell pour le telechargement (plus fiable que curl sur Windows)
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/jmougeot/Alarm-bloomberg/archive/refs/heads/main.zip' -OutFile '%TEMP%\strategy-monitor.zip'"

if not exist "%TEMP%\strategy-monitor.zip" (
    echo [INFO] Tentative avec curl...
    curl -L -k -o "%TEMP%\strategy-monitor.zip" https://github.com/jmougeot/Alarm-bloomberg/archive/refs/heads/main.zip
)

if not exist "%TEMP%\strategy-monitor.zip" (
    echo [ERREUR] Echec du telechargement
    pause
    exit /b 1
)

:: Extraire le ZIP
echo [INFO] Extraction des fichiers...
powershell -Command "Expand-Archive -Path '%TEMP%\strategy-monitor.zip' -DestinationPath '%TEMP%\strategy-extract' -Force"

:: Deplacer vers le dossier final
if exist "%TEMP%\strategy-extract\Alarm-bloomberg-main" (
    move "%TEMP%\strategy-extract\Alarm-bloomberg-main" "%INSTALL_DIR%" >nul
) else (
    echo [ERREUR] Structure du ZIP inattendue
    pause
    exit /b 1
)

:: Nettoyer
del "%TEMP%\strategy-monitor.zip" >nul 2>&1
rmdir /s /q "%TEMP%\strategy-extract" 2>nul

echo [OK] Application telechargee!

:install_deps
:: ============================================================
:: ETAPE 3: Installer les dependances Python
:: ============================================================
echo.
echo [ETAPE 3/4] Installation des dependances...
echo.

cd /d "%INSTALL_DIR%"

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

:: Tentative Bloomberg API (optionnel)
echo.
echo [INFO] Tentative d'installation de Bloomberg API (optionnel)...
python -m pip install blpapi --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ --trusted-host blpapi.bloomberg.com --quiet 2>nul
if errorlevel 1 (
    echo    [INFO] Bloomberg API non disponible - l'app fonctionnera sans
) else (
    echo    [OK] Bloomberg API
)

:: ============================================================
:: ETAPE 4: Creer les raccourcis
:: ============================================================
echo.
echo [ETAPE 4/4] Creation des raccourcis...
echo.

:: Creer le raccourci via Python
python src\create_shortcut.py 2>nul
if errorlevel 1 (
    echo [INFO] Creation du raccourci manuel...
    
    :: Creer un fichier .bat sur le bureau comme fallback
    echo @echo off > "%USERPROFILE%\Desktop\Strategy Monitor.bat"
    echo cd /d "%INSTALL_DIR%" >> "%USERPROFILE%\Desktop\Strategy Monitor.bat"
    echo start pythonw main.py >> "%USERPROFILE%\Desktop\Strategy Monitor.bat"
    
    echo [OK] Raccourci cree sur le Bureau
) else (
    echo [OK] Raccourcis crees!
)

:: ============================================================
:: FIN
:: ============================================================
echo.
echo ============================================================
echo    INSTALLATION TERMINEE AVEC SUCCES!
echo ============================================================
echo.
echo    L'application a ete installee dans:
echo    %INSTALL_DIR%
echo.
echo    Pour lancer l'application:
echo    - Double-cliquez sur "Strategy Monitor" sur le Bureau
echo    - Ou lancez run.bat dans le dossier d'installation
echo.
echo ============================================================
echo.

:: Proposer de lancer l'application
set /p LAUNCH="Voulez-vous lancer l'application maintenant? (O/N): "
if /i "%LAUNCH%"=="O" (
    cd /d "%INSTALL_DIR%"
    start pythonw main.py
)

echo.
echo Appuyez sur une touche pour fermer...
pause >nul
