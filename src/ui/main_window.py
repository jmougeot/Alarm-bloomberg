"""
Fenêtre principale de l'application Strategy Monitor
"""
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import asyncio

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QMessageBox, QStackedWidget
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QKeySequence

from ..models.page import Page
from ..models.strategy import Strategy
from ..services.bloomberg_service import BloombergService
from ..services.auth_service import AuthService
from ..services.alarm_server_service import AlarmServerService
from .sidebar_widget import SidebarWidget
from .page_widget import PageWidget
from .strategy_block_widget import StrategyBlockWidget
from .login_dialog import LoginDialog
from ..handlers import FileHandler, AlertHandler, BloombergHandler, StrategyHandler
from .styles.dark_theme import DARK_THEME_STYLESHEET

if TYPE_CHECKING:
    from ..handlers.file_handler import FileHandler
    from ..handlers.alert_handler import AlertHandler
    from ..handlers.bloomberg_handler import BloombergHandler
    from ..handlers.strategy_handler import StrategyHandler


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application.
    Gère plusieurs pages de stratégies via une sidebar.
    """
    
    # Déclaration des types pour Pylance
    file_handler: 'FileHandler'
    alert_handler: 'AlertHandler'
    bloomberg_handler: 'BloombergHandler'
    strategy_handler: 'StrategyHandler'
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        super().__init__()
        
        # État global
        self.pages: dict[str, PageWidget] = {}
        self.current_page_id: Optional[str] = None
        self.bloomberg_service: Optional[BloombergService] = None
        self.current_file: Optional[str] = None
        self._bloomberg_started = False
        self._loading_workspace = False  # Flag pour éviter création page par défaut
        
        # Services de synchronisation
        self.auth_service = AuthService(server_url)
        self.alarm_server: Optional[AlarmServerService] = None
        self._online_mode = False
        
        # Propriétés de compatibilité pour les handlers
        self._strategies_cache: dict[str, Strategy] = {}
        self._strategy_widgets_cache: dict[str, StrategyBlockWidget] = {}
        
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
        
        # Tenter la connexion au serveur
        QTimer.singleShot(500, self._attempt_server_connection)
        
        # Charger automatiquement le dernier workspace ou créer une page par défaut
        self._loading_workspace = True
        if not self.file_handler.auto_load_last_workspace():
            self._create_default_page()
        self._loading_workspace = False
    
    @property
    def strategies(self) -> dict[str, Strategy]:
        """Retourne toutes les stratégies de toutes les pages"""
        all_strategies = {}
        for page in self.pages.values():
            all_strategies.update(page.strategies)
        return all_strategies
    
    @property
    def strategy_widgets(self) -> dict[str, StrategyBlockWidget]:
        """Retourne tous les widgets de stratégies"""
        all_widgets = {}
        for page in self.pages.values():
            all_widgets.update(page.strategy_widgets)
        return all_widgets
    
    @property
    def strategies_layout(self):
        """Retourne le layout de la page courante (compatibilité)"""
        if self.current_page_id and self.current_page_id in self.pages:
            return self.pages[self.current_page_id].strategies_layout
        return None
    
    def showEvent(self, event):
        """Appelé quand la fenêtre est affichée"""
        super().showEvent(event)
        if not self._bloomberg_started:
            self._bloomberg_started = True
            QTimer.singleShot(500, self.bloomberg_handler.start_connection)
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Strategy Price Monitor")
        self.setMinimumSize(1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === Sidebar ===
        self.sidebar = SidebarWidget()
        self.sidebar.page_selected.connect(self._on_page_selected)
        self.sidebar.page_added.connect(self._on_page_added)
        self.sidebar.page_renamed.connect(self._on_page_renamed)
        self.sidebar.page_deleted.connect(self._on_page_deleted)
        main_layout.addWidget(self.sidebar)
        
        # === Zone de contenu (pages empilées) ===
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Stack de pages
        self.page_stack = QStackedWidget()
        content_layout.addWidget(self.page_stack)
        
        main_layout.addWidget(content_widget)
    
    def _setup_menu(self):
        """Configure la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("&Fichier")
        
        new_action = QAction("&Nouveau workspace", self)
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
        
        # Import/Export de pages
        import_page_action = QAction("&Importer une page...", self)
        import_page_action.setShortcut("Ctrl+Shift+I")
        import_page_action.triggered.connect(self.file_handler.import_page)
        file_menu.addAction(import_page_action)
        
        export_page_action = QAction("&Exporter la page courante...", self)
        export_page_action.setShortcut("Ctrl+Shift+E")
        export_page_action.triggered.connect(self._export_current_page)
        file_menu.addAction(export_page_action)
        
        file_menu.addSeparator()
        
        # Ouvrir fichier legacy
        open_legacy_action = QAction("Ouvrir un fichier JSON (ancien format)...", self)
        open_legacy_action.triggered.connect(self.file_handler.open_legacy_file)
        file_menu.addAction(open_legacy_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quitter", self)
        quit_action.setShortcut(QKeySequence.Quit)  # type: ignore
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Pages
        pages_menu = menubar.addMenu("&Pages")
        
        add_page_action = QAction("&Nouvelle page", self)
        add_page_action.setShortcut("Ctrl+T")
        add_page_action.triggered.connect(self._add_new_page_from_menu)
        pages_menu.addAction(add_page_action)
        
        # Menu Stratégies
        strategy_menu = menubar.addMenu("&Stratégies")
        
        add_strategy_action = QAction("&Ajouter une stratégie", self)
        add_strategy_action.setShortcut("Ctrl+Shift+N")
        add_strategy_action.triggered.connect(self._add_strategy_to_current_page)
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
        
        # Version de l'application
        version_label = QLabel("V2")
        version_label.setStyleSheet("color: #666; padding: 0 10px; font-weight: bold;")
        self.statusbar.addPermanentWidget(version_label)
        
        # Indicateur de connexion Bloomberg (à droite de la statusbar)
        self.connection_label = QLabel("⚫ Déconnecté")
        self.connection_label.setStyleSheet("color: #888; padding: 0 10px;")
        self.statusbar.addPermanentWidget(self.connection_label)
        
        self.statusbar.showMessage("Prêt")
    
    def _apply_dark_theme(self):
        """Applique le thème sombre"""
        self.setStyleSheet(DARK_THEME_STYLESHEET)
    
    def _create_default_page(self):
        """Crée une page par défaut au démarrage"""
        page = Page(name="Général")
        self._add_page(page, select=True)
    
    def _add_page(self, page: Page, select: bool = True):
        """Ajoute une nouvelle page"""
        page_widget = PageWidget(page)
        page_widget.ticker_added.connect(self._on_ticker_added)
        page_widget.ticker_removed.connect(self._on_ticker_removed)
        page_widget.target_reached.connect(self.alert_handler.on_target_reached)
        page_widget.target_left.connect(self.alert_handler.on_target_left)
        page_widget.strategy_added.connect(self._on_page_modified)
        page_widget.strategy_deleted.connect(self._on_page_modified)
        page_widget.strategy_updated.connect(self._on_page_modified)
        
        self.pages[page.id] = page_widget
        self.page_stack.addWidget(page_widget)
        self.sidebar.add_page(page, select=select)
        
        if select:
            self.current_page_id = page.id
    
    def _remove_page(self, page_id: str):
        """Supprime une page"""
        if page_id in self.pages:
            page_widget = self.pages.pop(page_id)
            self.page_stack.removeWidget(page_widget)
            page_widget.deleteLater()
    
    def get_current_page(self) -> Optional[PageWidget]:
        """Retourne la page courante"""
        if self.current_page_id and self.current_page_id in self.pages:
            return self.pages[self.current_page_id]
        return None
    
    def get_all_pages(self) -> list[PageWidget]:
        """Retourne toutes les pages"""
        return list(self.pages.values())
    
    # === Event Handlers ===
    
    def _on_page_selected(self, page_id: str):
        """Appelé quand on sélectionne une page"""
        if page_id in self.pages:
            self.current_page_id = page_id
            self.page_stack.setCurrentWidget(self.pages[page_id])
            self.statusbar.showMessage(f"Page: {self.pages[page_id].page.name}", 2000)
    
    def _on_page_added(self, page: Page):
        """Appelé quand on ajoute une page depuis la sidebar"""
        self._add_page(page, select=True)
        self.statusbar.showMessage(f"Page '{page.name}' créée", 3000)
        self._trigger_auto_save()
    
    def _on_page_modified(self, *args):
        """Appelé quand une page est modifiée (stratégie ajoutée/supprimée/modifiée)"""
        if not self._loading_workspace:
            self._trigger_auto_save()
    
    def _trigger_auto_save(self):
        """Déclenche une sauvegarde automatique avec debounce"""
        if hasattr(self, '_auto_save_timer') and self._auto_save_timer.isActive():
            self._auto_save_timer.stop()
        
        if not hasattr(self, '_auto_save_timer'):
            self._auto_save_timer = QTimer()
            self._auto_save_timer.setSingleShot(True)
            self._auto_save_timer.timeout.connect(self._do_auto_save)
        
        # Sauvegarder après 2 secondes d'inactivité
        self._auto_save_timer.start(2000)
    
    def _do_auto_save(self):
        """Effectue la sauvegarde automatique"""
        if self.current_file and Path(self.current_file).is_dir():
            self.file_handler.save_current_page()
            self.file_handler._update_workspace_meta()
    
    def _on_page_renamed(self, page_id: str, new_name: str):
        """Appelé quand on renomme une page"""
        if page_id in self.pages:
            self.pages[page_id].page.name = new_name
            self.pages[page_id].update_title()
            self.statusbar.showMessage(f"Page renommée: {new_name}", 2000)
    
    def _on_page_deleted(self, page_id: str):
        """Appelé quand on supprime une page"""
        if page_id in self.pages:
            page_name = self.pages[page_id].page.name
            self._remove_page(page_id)
            self.statusbar.showMessage(f"Page '{page_name}' supprimée", 3000)
    
    def _subscribe_all_tickers(self):
        """S'abonne à tous les tickers de toutes les stratégies"""
        if self.bloomberg_service and self.bloomberg_service.is_connected:
            for page in self.pages.values():
                for ticker in page.get_all_tickers():
                    if ticker:
                        self.bloomberg_service.subscribe(ticker)
            self.statusbar.showMessage("Tous les tickers abonnés", 2000)
    
    def _on_ticker_added(self, ticker: str):
        """Appelé quand un ticker est ajouté"""
        if self.bloomberg_service and self.bloomberg_service.is_connected:
            self.bloomberg_service.subscribe(ticker)
            self.statusbar.showMessage(f"Abonné à {ticker}", 2000)
    
    def _on_ticker_removed(self, ticker: str):
        """Appelé quand un ticker est supprimé"""
        # Vérifier si le ticker est encore utilisé ailleurs
        ticker_still_used = any(
            ticker in page.get_all_tickers()
            for page in self.pages.values()
        )
        if not ticker_still_used and self.bloomberg_service:
            self.bloomberg_service.unsubscribe(ticker)
    
    def _add_new_page_from_menu(self):
        """Ajoute une page depuis le menu"""
        self.sidebar._on_add_page()
    
    def _add_strategy_to_current_page(self):
        """Ajoute une stratégie à la page courante"""
        current_page = self.get_current_page()
        if current_page:
            current_page._on_add_strategy()
    
    def _export_current_page(self):
        """Exporte la page courante"""
        if self.current_page_id:
            self.file_handler.export_page(self.current_page_id)
    
    def _show_about(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(
            self,
            "À propos",
            "<h2>Strategy Price Monitor</h2>"
            "<p>Monitor de prix en temps réel pour stratégies d'options.</p>"
            "<p>Supporte: Butterfly, Condor, et stratégies personnalisées.</p>"
            "<p><b>Fonctionnalités:</b></p>"
            "<ul>"
            "<li>Multiples pages pour organiser vos stratégies</li>"
            "<li>Alertes sonores et visuelles</li>"
            "<li>Connexion Bloomberg en temps réel</li>"
            "</ul>"
            "<p>Version 2.0</p>"
        )
    
    def closeEvent(self, event):
        """Appelé à la fermeture de la fenêtre"""
        # Arrêter le serveur d'alarmes
        if self.alarm_server:
            self.alarm_server.stop()
        
        # Arrêter Bloomberg
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
                if self.bloomberg_service and not self.bloomberg_service.is_connected:
                    self.bloomberg_handler.start_connection()
        else:
            event.accept()
    
    # === Méthodes pour la sauvegarde/chargement ===
    
    def to_dict(self) -> dict:
        """Convertit tout le workspace en dictionnaire"""
        return {
            'version': '2.0',
            'pages': [page.to_dict() for page in self.pages.values()]
        }
    
    def load_from_dict(self, data: dict):
        """Charge un workspace depuis un dictionnaire"""
        # Supprimer toutes les pages existantes
        for page_id in list(self.pages.keys()):
            self._remove_page(page_id)
            self.sidebar.remove_page(page_id)
        
        # Charger les nouvelles pages
        pages_data = data.get('pages', [])
        if not pages_data:
            # Ancienne version: données à plat
            self._create_default_page()
            current_page = self.get_current_page()
            if current_page:
                for strategy_data in data.get('strategies', []):
                    strategy = Strategy.from_dict(strategy_data)
                    current_page.add_strategy(strategy)
        else:
            # Nouvelle version: pages multiples
            for page_data in pages_data:
                page_id = page_data.get('id')
                page_name = page_data.get('name', 'Sans nom')
                
                # Créer la page
                page_widget = self.create_page(page_name, page_id)
                
                # Charger les stratégies
                for strategy_data in page_data.get('strategies', []):
                    strategy = Strategy.from_dict(strategy_data)
                    page_widget.add_strategy(strategy)
    
    # === Synchronisation serveur ===
    
    def _attempt_server_connection(self):
        """Tente de se connecter au serveur"""
        # Vérifier si un token existe déjà
        if self.auth_service.load_saved_token():
            self._start_server_sync()
        else:
            # Afficher le dialog de login
            self._show_login_dialog()
    
    def _show_login_dialog(self):
        """Affiche le dialog de connexion"""
        dialog = LoginDialog(self)
        dialog.login_successful.connect(self._on_login_attempt)
        
        if dialog.exec():
            # Utilisateur a cliqué "Continuer hors ligne"
            self._online_mode = False
            self.statusbar.showMessage("Mode hors ligne")
        else:
            self._online_mode = False
    
    def _on_login_attempt(self, username: str, password: str):
        """Appelé quand l'utilisateur tente de se connecter"""
        dialog = self.sender()
        dialog.hide_error()
        
        # Déterminer si c'est un login ou register
        is_register = dialog.is_register_mode()
        
        # Créer une coroutine pour l'appel async
        async def do_auth():
            if is_register:
                success = await self.auth_service.register(username, password)
            else:
                success = await self.auth_service.login(username, password)
            
            return success
        
        # Exécuter l'authentification
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(do_auth())
            loop.close()
            
            if success:
                dialog.accept()
                self._start_server_sync()
                self.statusbar.showMessage(f"Connecté en tant que {self.auth_service.user_info.get('username', username)}")
            else:
                dialog._show_error("Échec de l'authentification. Vérifiez vos identifiants.")
        except Exception as e:
            dialog._show_error(f"Erreur de connexion: {str(e)}")
    
    def _start_server_sync(self):
        """Démarre la synchronisation avec le serveur"""
        try:
            ws_url = self.auth_service.get_ws_url()
            
            # Créer le service WebSocket
            self.alarm_server = AlarmServerService(self)
            
            # Connecter les signaux
            self.alarm_server.connected.connect(self._on_server_connected)
            self.alarm_server.disconnected.connect(self._on_server_disconnected)
            self.alarm_server.error_occurred.connect(self._on_server_error)
            self.alarm_server.initial_state_received.connect(self._on_initial_state)
            self.alarm_server.alarm_created.connect(self._on_server_alarm_created)
            self.alarm_server.alarm_updated.connect(self._on_server_alarm_updated)
            self.alarm_server.alarm_deleted.connect(self._on_server_alarm_deleted)
            self.alarm_server.page_created.connect(self._on_server_page_created)
            
            # Démarrer la connexion
            self.alarm_server.start(ws_url)
            self._online_mode = True
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur de connexion",
                f"Impossible de se connecter au serveur:\n{str(e)}\n\nContinuer en mode hors ligne."
            )
            self._online_mode = False
    
    def _on_server_connected(self):
        """Appelé quand la connexion au serveur est établie"""
        self.statusbar.showMessage("✓ Connecté au serveur")
        print("[Server] Connected")
    
    def _on_server_disconnected(self):
        """Appelé quand la connexion au serveur est perdue"""
        self.statusbar.showMessage("⚠ Déconnecté du serveur - Tentative de reconnexion...")
        print("[Server] Disconnected")
    
    def _on_server_error(self, error_msg: str):
        """Appelé en cas d'erreur serveur"""
        print(f"[Server] Error: {error_msg}")
        QMessageBox.warning(self, "Erreur serveur", error_msg)
    
    def _on_initial_state(self, state: dict):
        """Appelé quand l'état initial est reçu du serveur"""
        print(f"[Server] Initial state received: {len(state.get('pages', []))} pages, {len(state.get('alarms', []))} alarms")
        
        # TODO: Synchroniser l'état local avec le serveur
        # Pour l'instant, on garde l'état local
        
        self.statusbar.showMessage("Synchronisé avec le serveur")
    
    def _on_server_alarm_created(self, alarm_data: dict):
        """Appelé quand une alarme est créée sur le serveur"""
        print(f"[Server] Alarm created: {alarm_data.get('id')}")
        # TODO: Créer l'alarme localement
    
    def _on_server_alarm_updated(self, alarm_data: dict):
        """Appelé quand une alarme est mise à jour sur le serveur"""
        print(f"[Server] Alarm updated: {alarm_data.get('id')}")
        # TODO: Mettre à jour l'alarme localement
    
    def _on_server_alarm_deleted(self, alarm_id: str):
        """Appelé quand une alarme est supprimée sur le serveur"""
        print(f"[Server] Alarm deleted: {alarm_id}")
        # TODO: Supprimer l'alarme localement
    
    def _on_server_page_created(self, page_data: dict):
        """Appelé quand une page est créée sur le serveur"""
        print(f"[Server] Page created: {page_data.get('name')}")
        # TODO: Créer la page localement
        self._subscribe_all_tickers()
