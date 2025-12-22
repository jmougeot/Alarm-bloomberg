"""
Test du popup d'alerte
Lance ce fichier pour voir le popup avec les deux boutons
"""
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from src.ui.alert_popup import AlertPopup


class TestWindow(QMainWindow):
    """Fenêtre de test pour le popup"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Alert Popup")
        self.setGeometry(100, 100, 400, 200)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Bouton pour tester le popup "Inférieur"
        btn_inf = QPushButton("🔔 Test Alarme Inférieur")
        btn_inf.setStyleSheet("""
            QPushButton {
                background-color: #2d5a27;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3d7a37;
            }
        """)
        btn_inf.clicked.connect(self.show_popup_inferior)
        layout.addWidget(btn_inf)
        
        # Bouton pour tester le popup "Supérieur"
        btn_sup = QPushButton("🔔 Test Alarme Supérieur")
        btn_sup.setStyleSheet("""
            QPushButton {
                background-color: #5a272d;
                color: white;
                padding: 15px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7a373d;
            }
        """)
        btn_sup.clicked.connect(self.show_popup_superior)
        layout.addWidget(btn_sup)
        
        self.setStyleSheet("background-color: #1e1e1e;")
    
    def show_popup_inferior(self):
        """Affiche un popup pour condition inférieure"""
        popup = AlertPopup(
            strategy_name="SFRF6 96.50/96.625/96.75 Call Fly",
            current_price=0.0125,
            target_price=0.0150,
            is_inferior=True,
            strategy_id="test-strategy-1",
            continue_callback=self.on_continue_alarm,
            parent=self
        )
        popup.show()
    
    def show_popup_superior(self):
        """Affiche un popup pour condition supérieure"""
        popup = AlertPopup(
            strategy_name="EUR/USD Put Spread",
            current_price=0.0875,
            target_price=0.0800,
            is_inferior=False,
            strategy_id="test-strategy-2",
            continue_callback=self.on_continue_alarm,
            parent=self
        )
        popup.show()
    
    def on_continue_alarm(self, strategy_id: str):
        """Callback quand on clique sur 'Continuer l'alarme'"""
        print(f"✅ Alarme réactivée pour la stratégie: {strategy_id}")


def main():
    app = QApplication(sys.argv)
    
    # Style sombre pour l'application
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
    """)
    
    window = TestWindow()
    window.show()
    
    print("=" * 50)
    print("Test du popup d'alerte")
    print("=" * 50)
    print("Cliquez sur un bouton pour afficher le popup")
    print("- '✓ OK' : ferme le popup (alarme reste désactivée)")
    print("- '🔔 Continuer l'alarme' : réactive l'alarme et ferme")
    print("=" * 50)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
