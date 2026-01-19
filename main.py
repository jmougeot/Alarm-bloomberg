"""
Strategy Price Monitor - Application principale
Monitor de prix en temps réel pour stratégies d'options (butterfly, condor, etc.)
"""
import sys
import os
import signal

# Ajouter les chemins pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration du chemin des plugins Qt (résout l'erreur "Could not find the Qt platform plugin")
try:
    import PySide6
    pyside6_path = os.path.dirname(PySide6.__file__)
    plugins_path = os.path.join(pyside6_path, "plugins")
    if os.path.exists(plugins_path):
        os.environ["QT_PLUGIN_PATH"] = plugins_path
except ImportError:
    pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from src.ui.popups.splash_screen import SplashScreen
from src.ui.main_window import MainWindow
from src.config import ALARM_SERVER_URL


def get_icon_path():
    """Retourne le chemin de l'icône, compatible avec PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Mode PyInstaller - l'icône est dans le bundle
        base_path = sys._MEIPASS
    else:
        # Mode développement
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_path, 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        return icon_path
    
    # Fallback vers build/icons
    icon_path = os.path.join(base_path, 'build', 'icons', 'icon.ico')
    if os.path.exists(icon_path):
        return icon_path
    
    return None


def main():
    # Gérer Ctrl+C proprement
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
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
    
    # Icône de l'application (taskbar, fenêtre, etc.)
    icon_path = get_icon_path()
    if icon_path:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        print(f"[App] Icon loaded from: {icon_path}")
    else:
        print("[App] Warning: Icon not found")
    
    # Variable pour stocker la fenêtre principale
    main_window = None
    
    def on_splash_finished():
        nonlocal main_window
        main_window = MainWindow(server_url=ALARM_SERVER_URL)
        main_window.show()
    
    # Afficher le splash screen
    splash = SplashScreen()
    splash.finished.connect(on_splash_finished)
    splash.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
