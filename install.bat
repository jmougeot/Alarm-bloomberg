@echo off
echo ========================================
echo Bloomberg Alarm - Installation
echo ========================================
echo.

echo [1/3] Installation des dependances...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Installation des dependances echouee
    pause
    exit /b 1
)

echo.
echo [2/3] Test de connexion au serveur...
python test_server.py
if %errorlevel% neq 0 (
    echo.
    echo ATTENTION: Serveur non accessible
    echo Vous pouvez continuer en mode hors ligne
    echo ou demarrer le serveur avant de lancer l'app.
    echo.
)

echo.
echo [3/3] Installation terminee!
echo.
echo ========================================
echo Prochaines etapes:
echo ========================================
echo.
echo 1. Demarrer le serveur (optionnel):
echo    cd alarm-server
echo    uvicorn app.main:app --reload --port 8080
echo.
echo 2. Lancer l'application:
echo    python main.py
echo.
echo Documentation:
echo    - SERVER_INTEGRATION.md (guide utilisateur)
echo    - server.md (deploiement serveur)
echo    - INTEGRATION_SUMMARY.md (technique)
echo.
pause
