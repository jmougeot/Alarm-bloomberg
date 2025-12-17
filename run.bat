@echo off
cd /d "%~dp0"

:: Activer l'environnement virtuel si present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Lancer l'application SANS console (pythonw)
start "" pythonw main.py
