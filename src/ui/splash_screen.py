"""
Splash Screen pour Strategy Price Monitor
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QBrush


class SplashScreen(QWidget):
    """Splash screen animé avec logo"""
    
    finished = Signal()
    
    def __init__(self):
        super().__init__(None, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)  # type: ignore
        self.setAttribute(Qt.WA_TranslucentBackground)  # type: ignore
        self.setFixedSize(500, 350)
        
        self._progress = 0
        self._setup_ui()
        self._center_on_screen()
        self._start_loading()
    
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Titre avec icône
        self.title_label = QLabel("📊 STRATEGY MONITOR")
        self.title_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.title_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 32px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                letter-spacing: 3px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Sous-titre
        subtitle = QLabel("Real-Time Options Strategy Pricing")
        subtitle.setAlignment(Qt.AlignCenter)  # type: ignore
        subtitle.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
            }
        """)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Logo ASCII art stylisé
        logo_text = """
    ╔══════════════════════════════╗
    ║   ┌─────┐  ┌─────┐  ┌─────┐  ║
    ║   │ BUY │──│ SELL│──│ BUY │  ║
    ║   └──┬──┘  └──┬──┘  └──┬──┘  ║
    ║      │        │        │     ║
    ║   ───┴────────┴────────┴───  ║
    ║        B U T T E R F L Y     ║
    ╚══════════════════════════════╝
        """
        
        logo_label = QLabel(logo_text)
        logo_label.setAlignment(Qt.AlignCenter)  # type: ignore
        logo_label.setStyleSheet("""
            QLabel {
                color: #00aaff;
                font-size: 11px;
                font-family: 'Consolas', 'Courier New', monospace;
                line-height: 1.2;
            }
        """)
        layout.addWidget(logo_label)
        
        layout.addSpacing(10)
        
        # Status de chargement
        self.status_label = QLabel("Initialisation...")
        self.status_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:0.5 #00aaff, stop:1 #00ff88);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Version
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignCenter)  # type: ignore
        version_label.setStyleSheet("""
            QLabel {
                color: #444;
                font-size: 10px;
            }
        """)
        layout.addWidget(version_label)
    
    def paintEvent(self, event):
        """Dessine le fond avec dégradé"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # type: ignore
        
        # Fond avec dégradé
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(20, 20, 30))
        gradient.setColorAt(1, QColor(10, 10, 15))
        
        # Rectangle arrondi
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(0, 170, 255, 100), 2))
        painter.drawRoundedRect(10, 10, self.width() - 20, self.height() - 20, 15, 15)
        
        # Ligne décorative en haut
        painter.setPen(QPen(QColor(0, 255, 136), 3))
        painter.drawLine(30, 15, self.width() - 30, 15)
    
    def _center_on_screen(self):
        """Centre le splash screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _start_loading(self):
        """Démarre l'animation de chargement"""
        self.loading_steps = [
            (10, "Chargement des modules..."),
            (25, "Initialisation de l'interface..."),
            (40, "Configuration du thème..."),
            (55, "Préparation du service Bloomberg..."),
            (70, "Chargement des stratégies..."),
            (85, "Finalisation..."),
            (100, "Prêt!")
        ]
        self.current_step = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(400)
    
    def _update_progress(self):
        """Met à jour la progression"""
        if self.current_step < len(self.loading_steps):
            progress, status = self.loading_steps[self.current_step]
            self.progress_bar.setValue(progress)
            self.status_label.setText(status)
            self.current_step += 1
        else:
            self.timer.stop()
            # Petit délai avant de fermer
            QTimer.singleShot(500, self._finish)
    
    def _finish(self):
        """Termine le splash screen"""
        self.finished.emit()
        self.close()


def show_splash_and_run():
    """Affiche le splash screen puis lance l'app"""
    import sys
    from src.ui.main_window import MainWindow
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Configuration
    app.setApplicationName("Strategy Price Monitor")
    
    # Splash screen
    splash = SplashScreen()
    
    # Fenêtre principale (créée mais pas affichée)
    main_window = None
    
    def on_splash_finished():
        nonlocal main_window
        main_window = MainWindow()
        main_window.show()
    
    splash.finished.connect(on_splash_finished)
    splash.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    show_splash_and_run()
