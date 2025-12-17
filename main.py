"""
Strategy Price Monitor - Application principale
Monitor de prix en temps réel pour stratégies d'options (butterfly, condor, etc.)
"""
import sys
import os

# Ajouter les chemins pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.ui.main_window import MainWindow


def main():
    # Configuration pour High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # Configuration de la police par défaut
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Nom de l'application
    app.setApplicationName("Strategy Price Monitor")
    app.setOrganizationName("Bloomberg Tools")
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
