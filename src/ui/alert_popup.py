"""
Popup d'alerte pour les stratégies
"""
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPixmap


class AlertPopup(QWidget):
    """Popup d'alerte animé quand une cible est atteinte"""
    
    def __init__(self, strategy_name: str, current_price: float, target_price: float, is_inferior: bool, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool) # type: ignore
        self.setAttribute(Qt.WA_TranslucentBackground) # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose) # type: ignore
        
        self._setup_ui(strategy_name, current_price, target_price, is_inferior)
        self._setup_animation()
        self._position_popup()
    
    def _setup_ui(self, strategy_name: str, current_price: float, target_price: float, is_inferior: bool):
        """Configure l'interface du popup"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container avec style
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1a5f1a;
                border: 3px solid #00ff00;
                border-radius: 15px;
            }
        """)
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 0))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(10)
        
        # Titre avec icône selon la condition
        icon = "⬇️" if is_inferior else "⬆️"
        title = QLabel(f"{icon} ALARME!")
        title.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter) # type: ignore
        container_layout.addWidget(title)
        
        # Image Picsou
        picsou_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "picsou.jpg")
        if os.path.exists(picsou_path):
            picsou_label = QLabel()
            pixmap = QPixmap(picsou_path)
            pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # type: ignore
            picsou_label.setPixmap(pixmap)
            picsou_label.setAlignment(Qt.AlignCenter)  # type: ignore
            container_layout.addWidget(picsou_label)
        
        # Nom de la stratégie
        name_label = QLabel(strategy_name)
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        name_label.setAlignment(Qt.AlignCenter) # type: ignore
        container_layout.addWidget(name_label)
        
        # Prix actuel
        price_text = f"Prix actuel: {current_price:.4f}" if current_price else "Prix: --"
        price_label = QLabel(price_text)
        price_label.setStyleSheet("""
            QLabel {
                color: #aaffaa;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        price_label.setAlignment(Qt.AlignCenter) # type: ignore
        container_layout.addWidget(price_label)
        
        # Condition
        condition_text = "inférieur" if is_inferior else "supérieur"
        target_text = f"Prix {condition_text} à {target_price:.4f}" if target_price else "Cible: --"
        
        condition_label = QLabel(target_text)
        condition_label.setStyleSheet("""
            QLabel {
                color: #88ff88;
                font-size: 14px;
            }
        """)
        condition_label.setAlignment(Qt.AlignCenter) # type: ignore
        container_layout.addWidget(condition_label)
        
        # Bouton fermer
        close_btn = QPushButton("✓ OK")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc00;
            }
        """)
        close_btn.clicked.connect(self._close_with_animation)
        container_layout.addWidget(close_btn, alignment=Qt.AlignCenter) # type: ignore
        
        layout.addWidget(container)
        
        self.setFixedSize(400, 400)
    
    def _setup_animation(self):
        """Configure l'animation d'entrée"""
        # Animation de fondu
        self.setWindowOpacity(0)
        
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic) # type: ignore
        
        # Fermeture automatique après 10 secondes
        # self.auto_close_timer = QTimer(self)
        # self.auto_close_timer.setSingleShot(True)
        # self.auto_close_timer.timeout.connect(self._close_with_animation)
        # self.auto_close_timer.start(10000)
    
    def _position_popup(self):
        """Positionne le popup au centre de l'écran"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def showEvent(self, event):
        """Appelé quand le popup est affiché"""
        super().showEvent(event)
        self.fade_in.start()
    
    def _close_with_animation(self):
        """Ferme le popup avec animation"""
        # self.auto_close_timer.stop()
        
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic) # type: ignore
        self.fade_out.finished.connect(self.close)
        self.fade_out.start()
