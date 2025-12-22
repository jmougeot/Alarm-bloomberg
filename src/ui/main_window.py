"""
Fenêtre principale de l'application Strategy Monitor
"""
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QLabel, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence

from ..models.strategy import Strategy
from ..services.bloomberg_service import BloombergService
from .strategy_block_widget import StrategyBlockWidget
from ..handlers import FileHandler, AlertHandler, BloombergHandler, StrategyHandler
from .styles.dark_theme import (
    DARK_THEME_STYLESHEET, 
    BUTTON_PRIMARY_STYLE, 
    CONNECTION_LABEL_DISCONNECTED,
    SCROLL_AREA_STYLE
)

if TYPE_CHECKING:
    from ..handlers.file_handler import FileHandler
    from ..handlers.alert_handler import AlertHandler
    from ..handlers.bloomberg_handler import BloombergHandler
    from ..handlers.strategy_handler import StrategyHandler


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application.
    Permet d'ajouter/supprimer des blocs de stratégies en permanence.
    """
    
    # Déclaration des types pour Pylance
    file_handler: 'FileHandler'
    alert_handler: 'AlertHandler'
    bloomberg_handler: 'BloombergHandler'
    strategy_handler: 'StrategyHandler'
    
    def __init__(self):
        super().__init__()
        
        # État
        self.strategies: dict[str, Strategy] = {}
        self.strategy_widgets: dict[str, StrategyBlockWidget] = {}
        self.bloomberg_service: Optional[BloombergService] = None
        self.current_file: Optional[str] = None
        self._bloomberg_started = False
        
        # Handlers
        self.file_handler = FileHandler(self)
        self.alert_handler = AlertHandler(self)
        self.bloomberg_handler = BloombergHandler(self)
        self.strategy_handler = StrategyHandler(self)
        
        # Setup
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self.bloomberg_handler.setup_bloomberg()
        self._apply_dark_theme()
    
    def showEvent(self, event):
        """Appelé quand la fenêtre est affichée - démarre Bloomberg automatiquement"""
        super().showEvent(event)
        if not self._bloomberg_started:
            self._bloomberg_started = True
            QTimer.singleShot(500, self.bloomberg_handler.start_connection)
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Strategy Price Monitor")
        self.setMinimumSize(1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === Toolbar ===
        toolbar_layout = QHBoxLayout()
        
        # Bouton ajouter stratégie
        self.add_strategy_btn = QPushButton("Nouvelle Stratégie")
        self.add_strategy_btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.add_strategy_btn.clicked.connect(self.strategy_handler.add_new_strategy)
        toolbar_layout.addWidget(self.add_strategy_btn)
        
        toolbar_layout.addStretch()
        
        # Indicateur de connexion Bloomberg
        self.connection_label = QLabel("⚫ Déconnecté")
        self.connection_label.setStyleSheet(CONNECTION_LABEL_DISCONNECTED)
        toolbar_layout.addWidget(self.connection_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # === Zone de scroll pour les stratégies ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore
        scroll_area.setStyleSheet(SCROLL_AREA_STYLE)
        
        # Container pour les blocs de stratégies
        self.strategies_container = QWidget()
        self.strategies_layout = QVBoxLayout(self.strategies_container)
        self.strategies_layout.setContentsMargins(0, 0, 0, 0)
        self.strategies_layout.setSpacing(0)
        self.strategies_layout.addStretch()
        
        scroll_area.setWidget(self.strategies_container)
        main_layout.addWidget(scroll_area)
    
    def _setup_menu(self):
        """Configure la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("&Fichier")
        
        new_action = QAction("&Nouveau", self)
        new_action.setShortcut(QKeySequence.New)  # type: ignore
        new_action.triggered.connect(self.file_handler.new_workspace)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Ouvrir...", self)
        open_action.setShortcut(QKeySequence.Open)  # type: ignore
        open_action.triggered.connect(self.file_handler.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Sauvegarder", self)
        save_action.setShortcut(QKeySequence.Save)  # type: ignore
        save_action.triggered.connect(self.file_handler.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Sauvegarder &sous...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)  # type: ignore
        save_as_action.triggered.connect(self.file_handler.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quitter", self)
        quit_action.setShortcut(QKeySequence.Quit)  # type: ignore
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Stratégies
        strategy_menu = menubar.addMenu("&Stratégies")
        
        add_strategy_action = QAction("&Ajouter une stratégie", self)
        add_strategy_action.setShortcut("Ctrl+Shift+N")
        add_strategy_action.triggered.connect(self.strategy_handler.add_new_strategy)
        strategy_menu.addAction(add_strategy_action)
        
        # Menu Aide
        help_menu = menubar.addMenu("&Aide")
        
        about_action = QAction("À &propos", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self):
        """Configure la barre de status"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Prêt")
    
    def _apply_dark_theme(self):
        """Applique le thème sombre"""
        self.setStyleSheet(DARK_THEME_STYLESHEET)
    
    def _show_about(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(
            self,
            "À propos",
            "<h2>Strategy Price Monitor</h2>"
            "<p>Monitor de prix en temps réel pour stratégies d'options.</p>"
            "<p>Supporte: Butterfly, Condor, et stratégies personnalisées.</p>"
            "<p>Version 1.0</p>"
        )
    
    def closeEvent(self, event):
        """Appelé à la fermeture de la fenêtre"""
        # Arrêter Bloomberg en premier
        if self.bloomberg_service:
            try:
                self.bloomberg_service.stop()
            except Exception:
                pass
        
        if self.strategies:
            reply = QMessageBox.question(
                self,
                "Quitter",
                "Voulez-vous sauvegarder avant de quitter?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel  # type: ignore
            )
            
            if reply == QMessageBox.Save:  # type: ignore
                self.file_handler.save_file()
                event.accept()
            elif reply == QMessageBox.Discard:  # type: ignore
                event.accept()
            else:
                event.ignore()
                # Redémarrer Bloomberg si on annule
                if self.bloomberg_service and not self.bloomberg_service.is_connected:
                    self.bloomberg_handler.start_connection()
        else:
            event.accept()
