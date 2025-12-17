"""
Fenêtre principale de l'application Strategy Monitor
"""
import json
import winsound
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QLabel, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QMessageBox,
    QApplication, QDialog, QGraphicsDropShadowEffect, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QAction, QKeySequence, QColor, QPixmap

from ..models.strategy import Strategy
from ..services.bloomberg_service import BloombergService
from .strategy_block_widget import StrategyBlockWidget


class AlertPopup(QWidget):
    """Popup d'alerte animé quand une cible est atteinte"""
    
    def __init__(self, strategy_name: str, current_price: float, target_price: float, is_inferior: bool, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool) #type: ignore
        self.setAttribute(Qt.WA_TranslucentBackground) #type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose) #type: ignore
        
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
        shadow.setColor(QColor(0, 255, 0, 150))
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
        title.setAlignment(Qt.AlignCenter) #type: ignore
        container_layout.addWidget(title)
        
        # Image Picsou
        import os
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
        name_label.setAlignment(Qt.AlignCenter)#type: ignore
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
        price_label.setAlignment(Qt.AlignCenter) #type: ignore
        container_layout.addWidget(price_label)
        
        # Condition
        condition_symbol = "≤" if is_inferior else "≥"
        condition_text = "inférieur" if is_inferior else "supérieur"
        target_text = f"Prix {condition_text} à {target_price:.4f}" if target_price else "Cible: --"
        
        condition_label = QLabel(target_text)
        condition_label.setStyleSheet("""
            QLabel {
                color: #88ff88;
                font-size: 14px;
            }
        """)
        condition_label.setAlignment(Qt.AlignCenter) #type: ignore
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
        
        self.setFixedSize(350, 200)
    
    def _setup_animation(self):
        """Configure l'animation d'entrée"""
        # Animation de fondu
        self.setWindowOpacity(0)
        
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic) #type: ignore
        
        # Fermeture automatique après 10 secondes
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self._close_with_animation)
        self.auto_close_timer.start(10000)
    
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
        self.auto_close_timer.stop()
        
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic) # type: ignore
        self.fade_out.finished.connect(self.close)
        self.fade_out.start()


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application.
    Permet d'ajouter/supprimer des blocs de stratégies en permanence.
    """
    
    def __init__(self):
        super().__init__()
        
        self.strategies: dict[str, Strategy] = {}
        self.strategy_widgets: dict[str, StrategyBlockWidget] = {}
        self.bloomberg_service: Optional[BloombergService] = None
        self.current_file: Optional[str] = None
        self._alerted_strategies: set[str] = set()  # Stratégies déjà alertées
        self._bloomberg_started = False  # Pour éviter de démarrer plusieurs fois
        
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_bloomberg()
        self._apply_dark_theme()
    
    def showEvent(self, event):
        """Appelé quand la fenêtre est affichée - démarre Bloomberg automatiquement"""
        super().showEvent(event)
        if not self._bloomberg_started:
            self._bloomberg_started = True
            # Petit délai pour laisser l'UI se charger
            QTimer.singleShot(500, self._start_bloomberg_connection)
    
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
        self.add_strategy_btn = QPushButton("➕ Nouvelle Stratégie")
        self.add_strategy_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2196f3;
            }
        """)
        self.add_strategy_btn.clicked.connect(self._add_new_strategy)
        toolbar_layout.addWidget(self.add_strategy_btn)
        
        toolbar_layout.addStretch()
        
        # Indicateur de connexion Bloomberg
        self.connection_label = QLabel("⚫ Déconnecté")
        self.connection_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                padding: 8px;
            }
        """)
        toolbar_layout.addWidget(self.connection_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # === Zone de scroll pour les stratégies ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) #type: ignore
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #121212;
            }
        """)
        
        # Container pour les blocs de stratégies
        self.strategies_container = QWidget()
        self.strategies_layout = QVBoxLayout(self.strategies_container)
        self.strategies_layout.setContentsMargins(5, 5, 5, 5)
        self.strategies_layout.setSpacing(15)
        self.strategies_layout.addStretch()  # Pousse les blocs vers le haut
        
        scroll_area.setWidget(self.strategies_container)
        main_layout.addWidget(scroll_area)
    
    def _setup_menu(self):
        """Configure la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("&Fichier")
        
        new_action = QAction("&Nouveau", self)
        new_action.setShortcut(QKeySequence.New) #type: ignore
        new_action.triggered.connect(self._new_workspace)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Ouvrir...", self)
        open_action.setShortcut(QKeySequence.Open) #type: ignore
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Sauvegarder", self)
        save_action.setShortcut(QKeySequence.Save) #type: ignore
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Sauvegarder &sous...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs) #type: ignore
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quitter", self)
        quit_action.setShortcut(QKeySequence.Quit) #type: ignore
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Stratégies
        strategy_menu = menubar.addMenu("&Stratégies")
        
        add_strategy_action = QAction("&Ajouter une stratégie", self)
        add_strategy_action.setShortcut("Ctrl+Shift+N")
        add_strategy_action.triggered.connect(self._add_new_strategy)
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
    
    def _setup_bloomberg(self):
        """Configure le service Bloomberg"""
        self.bloomberg_service = BloombergService()
        self.bloomberg_service.price_updated.connect(self._on_price_updated)
        self.bloomberg_service.connection_status.connect(self._on_connection_status)
        self.bloomberg_service.subscription_started.connect(self._on_subscription_started)
        self.bloomberg_service.subscription_failed.connect(self._on_subscription_failed)
    
    def _apply_dark_theme(self):
        """Applique le thème sombre"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QMenuBar {
                background-color: #1e1e1e;
                color: #fff;
            }
            QMenuBar::item:selected {
                background-color: #333;
            }
            QMenu {
                background-color: #1e1e1e;
                color: #fff;
                border: 1px solid #333;
            }
            QMenu::item:selected {
                background-color: #333;
            }
            QStatusBar {
                background-color: #1e1e1e;
                color: #888;
            }
            QLabel {
                color: #fff;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #444;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555;
            }
        """)
    
    def _add_new_strategy(self):
        """Ajoute un nouveau bloc de stratégie"""
        strategy = Strategy(name=f"Stratégie {len(self.strategies) + 1}")
        self._add_strategy_widget(strategy)
        self.statusbar.showMessage(f"Stratégie '{strategy.name}' créée", 3000)
    
    def _add_strategy_widget(self, strategy: Strategy):
        """Ajoute un widget de stratégie"""
        self.strategies[strategy.id] = strategy
        
        widget = StrategyBlockWidget(strategy)
        widget.strategy_deleted.connect(self._on_strategy_deleted)
        widget.strategy_updated.connect(self._on_strategy_updated)
        widget.ticker_added.connect(self._on_ticker_added)
        widget.ticker_removed.connect(self._on_ticker_removed)
        widget.target_reached.connect(self._on_target_reached)
        widget.target_left.connect(self._on_target_left)
        
        self.strategy_widgets[strategy.id] = widget
        
        # Insérer avant le stretch
        self.strategies_layout.insertWidget(
            self.strategies_layout.count() - 1, 
            widget
        )
        
        # S'abonner aux tickers existants
        if self.bloomberg_service and self.bloomberg_service.is_connected:
            for ticker in strategy.get_all_tickers():
                self.bloomberg_service.subscribe(ticker)
    
    def _on_strategy_deleted(self, strategy_id: str):
        """Appelé quand une stratégie est supprimée"""
        if strategy_id in self.strategy_widgets:
            widget = self.strategy_widgets.pop(strategy_id)
            self.strategies_layout.removeWidget(widget)
            widget.deleteLater()
        
        if strategy_id in self.strategies:
            strategy = self.strategies.pop(strategy_id)
            self.statusbar.showMessage(f"Stratégie '{strategy.name}' supprimée", 3000)
    
    def _on_strategy_updated(self, strategy_id: str):
        """Appelé quand une stratégie est mise à jour"""
        # Pour le moment, on ne fait rien de spécial
        pass
    
    def _on_ticker_added(self, ticker: str):
        """Appelé quand un ticker est ajouté"""
        if self.bloomberg_service and self.bloomberg_service.is_connected:
            self.bloomberg_service.subscribe(ticker)
            self.statusbar.showMessage(f"Abonné à {ticker}", 2000)
    
    def _on_ticker_removed(self, ticker: str):
        """Appelé quand un ticker est supprimé"""
        # Vérifier si le ticker est encore utilisé ailleurs
        ticker_still_used = any(
            ticker in strategy.get_all_tickers()
            for strategy in self.strategies.values()
        )
        
        if not ticker_still_used and self.bloomberg_service:
            self.bloomberg_service.unsubscribe(ticker)
    
    def _on_target_reached(self, strategy_id: str):
        """Événement déclenché quand une cible est atteinte"""
        # Éviter de spammer les alertes
        if strategy_id in self._alerted_strategies:
            return
        
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
            self._alerted_strategies.add(strategy_id)
            
            current_price = strategy.calculate_strategy_price()
            from ..models.strategy import TargetCondition
            is_inferior = strategy.target_condition == TargetCondition.INFERIEUR
            
            # Jouer le son d'alerte
            self._play_alert_sound()
            
            # Afficher le popup
            self._show_alert_popup(strategy.name, current_price, strategy.target_price, is_inferior) #type: ignore
            
            condition_text = "inférieur" if is_inferior else "supérieur"
            self.statusbar.showMessage(
                f"🚨 ALARME! '{strategy.name}' - Prix {condition_text} à {strategy.target_price:.4f}!", 
                5000
            )
    
    def _on_target_left(self, strategy_id: str):
        """Appelé quand le prix sort de la zone cible"""
        self._alerted_strategies.discard(strategy_id)
    
    def _play_alert_sound(self):
        """Joue un son d'alerte"""
        import os
        try:
            # Chercher un fichier son personnalisé dans assets/
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            custom_sound = os.path.join(app_dir, "assets", "Epee.wav")
            
            if os.path.exists(custom_sound):
                # Jouer le fichier WAV personnalisé
                winsound.PlaySound(custom_sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Fallback: bips système
                for _ in range(3):
                    winsound.Beep(1000, 200)  # Fréquence 1000Hz, durée 200ms
                    winsound.Beep(1500, 200)  # Fréquence 1500Hz
        except Exception:
            pass  # Ignorer si le son ne fonctionne pas
    
    def _show_alert_popup(self, strategy_name: str, current_price: float, target_price: float, is_inferior: bool):
        """Affiche un popup d'alerte"""
        popup = AlertPopup(strategy_name, current_price, target_price, is_inferior, self)
        popup.show()
    
    def _start_bloomberg_connection(self):
        """Démarre la connexion Bloomberg automatiquement"""
        if not self.bloomberg_service.is_connected: #type: ignore
            self.bloomberg_service.start() #type: ignore
            
            # S'abonner à tous les tickers existants
            for strategy in self.strategies.values():
                for ticker in strategy.get_all_tickers():
                    self.bloomberg_service.subscribe(ticker) #type: ignore
    
    def _on_price_updated(self, ticker: str, last: float, bid: float, ask: float):
        """Appelé quand un prix est mis à jour"""
        for widget in self.strategy_widgets.values():
            widget.update_price(ticker, last, bid, ask)
    
    def _on_connection_status(self, connected: bool, message: str):
        """Appelé quand le status de connexion change"""
        if connected:
            self.connection_label.setText(f"🟢 {message}")
            self.connection_label.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
        else:
            self.connection_label.setText(f"🔴 {message}")
            self.connection_label.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
        
        self.statusbar.showMessage(message, 5000)
    
    def _on_subscription_started(self, ticker: str):
        """Appelé quand une subscription démarre"""
        self.statusbar.showMessage(f"✓ Subscription active: {ticker}", 2000)
    
    def _on_subscription_failed(self, ticker: str, error: str):
        """Appelé quand une subscription échoue"""
        self.statusbar.showMessage(f"✗ Échec subscription {ticker}: {error}", 5000)
    
    def _new_workspace(self):
        """Crée un nouveau workspace"""
        if self.strategies:
            reply = QMessageBox.question(
                self,
                "Nouveau workspace",
                "Voulez-vous sauvegarder avant de créer un nouveau workspace?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel #type: ignore
            )
            
            if reply == QMessageBox.Save: #type: ignore
                self._save_file()
            elif reply == QMessageBox.Cancel: #type: ignore
                return
        
        # Supprimer toutes les stratégies
        for strategy_id in list(self.strategy_widgets.keys()):
            self._on_strategy_deleted(strategy_id)
        
        self.current_file = None
        self.setWindowTitle("Strategy Price Monitor")
        self.statusbar.showMessage("Nouveau workspace créé", 3000)
    
    def _open_file(self):
        """Ouvre un fichier de sauvegarde"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir des stratégies",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Supprimer les stratégies actuelles
            for strategy_id in list(self.strategy_widgets.keys()):
                self._on_strategy_deleted(strategy_id)
            
            # Charger les nouvelles stratégies
            for strategy_data in data.get('strategies', []):
                strategy = Strategy.from_dict(strategy_data)
                self._add_strategy_widget(strategy)
            
            self.current_file = file_path
            self.setWindowTitle(f"Strategy Price Monitor - {Path(file_path).name}")
            self.statusbar.showMessage(f"Fichier chargé: {file_path}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger le fichier:\n{str(e)}"
            )
    
    def _save_file(self):
        """Sauvegarde les stratégies"""
        if not self.current_file:
            self._save_file_as()
            return
        
        self._save_to_file(self.current_file)
    
    def _save_file_as(self):
        """Sauvegarde sous un nouveau nom"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder les stratégies",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            self._save_to_file(file_path)
            self.current_file = file_path
            self.setWindowTitle(f"Strategy Price Monitor - {Path(file_path).name}")
    
    def _save_to_file(self, file_path: str):
        """Sauvegarde dans un fichier"""
        try:
            data = {
                'strategies': [
                    strategy.to_dict() 
                    for strategy in self.strategies.values()
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.statusbar.showMessage(f"Sauvegardé: {file_path}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de sauvegarder:\n{str(e)}"
            )
    
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
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel #type: ignore
            )
            
            if reply == QMessageBox.Save: #type: ignore
                self._save_file()
                event.accept()
            elif reply == QMessageBox.Discard: #type: ignore
                event.accept()
            else:
                event.ignore()
                # Redémarrer Bloomberg si on annule
                if not self.bloomberg_service.is_connected: #type: ignore
                    self._start_bloomberg_connection()
        else:
            event.accept()
