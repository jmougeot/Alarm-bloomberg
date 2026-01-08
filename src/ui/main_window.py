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
from .group_dialog import GroupDialog
from .share_page_dialog import SharePageDialog
from ..handlers import FileHandler, AlertHandler, BloombergHandler, StrategyHandler, ServerHandler, AuthHandler
from .styles.dark_theme import DARK_THEME_STYLESHEET

if TYPE_CHECKING:
    from ..handlers.file_handler import FileHandler
    from ..handlers.alert_handler import AlertHandler
    from ..handlers.bloomberg_handler import BloombergHandler
    from ..handlers.strategy_handler import StrategyHandler
    from ..handlers.server_handler import ServerHandler
    from ..handlers.auth_handler import AuthHandler


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
    server_handler: 'ServerHandler'
    auth_handler: 'AuthHandler'
    
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
        self._synced_strategies: set[str] = set()  # IDs des stratégies synchronisées avec le serveur
        
        # Propriétés de compatibilité pour les handlers
        self._strategies_cache: dict[str, Strategy] = {}
        self._strategy_widgets_cache: dict[str, StrategyBlockWidget] = {}
        
        # Handlers
        self.file_handler = FileHandler(self)
        self.alert_handler = AlertHandler(self)
        self.bloomberg_handler = BloombergHandler(self)
        self.strategy_handler = StrategyHandler(self)
        self.server_handler = ServerHandler(self)
        self.auth_handler = AuthHandler(self)
        
        # Setup
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self.bloomberg_handler.setup_bloomberg()
        self._apply_dark_theme()
        
        # Tenter la connexion au serveur
        QTimer.singleShot(500, self.auth_handler.attempt_connection)
        
        # Plus de chargement automatique de workspace local
        # Les données viennent maintenant du serveur
        # Si pas connecté, une page par défaut sera créée
    
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
        self.sidebar.refresh_requested.connect(self._on_refresh_requested)
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
        
        # Import/Export de pages (pour backup local)
        import_page_action = QAction("&Importer une page (JSON)...", self)
        import_page_action.setShortcut("Ctrl+Shift+I")
        import_page_action.triggered.connect(self.file_handler.import_page)
        file_menu.addAction(import_page_action)
        
        export_page_action = QAction("&Exporter la page courante (JSON)...", self)
        export_page_action.setShortcut("Ctrl+Shift+E")
        export_page_action.triggered.connect(self._export_current_page)
        file_menu.addAction(export_page_action)
        
        file_menu.addSeparator()
        
        # Déconnexion
        logout_action = QAction("&Déconnexion", self)
        logout_action.triggered.connect(self.auth_handler.logout)
        file_menu.addAction(logout_action)
        
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
        
        pages_menu.addSeparator()
        
        share_page_action = QAction("&Partager la page courante...", self)
        share_page_action.setShortcut("Ctrl+Shift+S")
        share_page_action.triggered.connect(self._share_current_page)
        pages_menu.addAction(share_page_action)
        
        # Menu Stratégies
        strategy_menu = menubar.addMenu("&Stratégies")
        
        add_strategy_action = QAction("&Ajouter une stratégie", self)
        add_strategy_action.setShortcut("Ctrl+Shift+N")
        add_strategy_action.triggered.connect(self._add_strategy_to_current_page)
        strategy_menu.addAction(add_strategy_action)
        
        # Menu Groupes
        groups_menu = menubar.addMenu("&Groupes")
        
        manage_groups_action = QAction("&Gérer les groupes...", self)
        manage_groups_action.setShortcut("Ctrl+G")
        manage_groups_action.triggered.connect(self._manage_groups)
        groups_menu.addAction(manage_groups_action)
        
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
    
    def _add_page(self, page: Page, select: bool = True, sync_to_server: bool = True):
        """Ajoute une nouvelle page"""
        page_widget = PageWidget(page)
        page_widget.ticker_added.connect(self._on_ticker_added)
        page_widget.ticker_removed.connect(self._on_ticker_removed)
        page_widget.target_reached.connect(self.alert_handler.on_target_reached)
        page_widget.target_left.connect(self.alert_handler.on_target_left)
        page_widget.strategy_added.connect(self._on_page_modified)
        page_widget.strategy_deleted.connect(self._on_strategy_deleted)
        page_widget.strategy_updated.connect(self._on_page_modified)
        
        self.pages[page.id] = page_widget
        self.page_stack.addWidget(page_widget)
        self.sidebar.add_page(page, select=select)
        
        # Envoyer au serveur si connecté (sauf si c'est une page déjà présente sur le serveur)
        if sync_to_server and self._online_mode and self.alarm_server:
            self.alarm_server.create_page(page.name, page.id)
        
        if select:
            self.current_page_id = page.id
    
    def _remove_page(self, page_id: str, sync_to_server: bool = True):
        """Supprime une page"""
        if page_id in self.pages:
            page_widget = self.pages.pop(page_id)
            self.page_stack.removeWidget(page_widget)
            page_widget.deleteLater()
            
            # Synchroniser avec le serveur
            if sync_to_server and self._online_mode and self.alarm_server:
                self.alarm_server.delete_page(page_id)
    
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
    
    def _on_page_modified(self, page_id: str = None, strategy_or_id = None, *args):
        """Appelé quand une page est modifiée (stratégie ajoutée ou modifiée)"""
        from ..models.strategy import Strategy
        
        # Le signal peut envoyer soit un ID (str) soit un objet Strategy
        if isinstance(strategy_or_id, Strategy):
            strategy = strategy_or_id
            strategy_id = strategy.id
            effective_page_id = page_id or self.current_page_id
            print(f"[Page] Strategy added - page_id={effective_page_id}, strategy={strategy.name}", flush=True)
            
            # Synchroniser immédiatement pour les nouvelles stratégies
            if self._online_mode and self.alarm_server:
                self.server_handler.sync_strategy('create', strategy, effective_page_id)
        else:
            strategy_id = strategy_or_id
            # Pour les mises à jour, utiliser un debounce par stratégie
            self._schedule_strategy_sync(page_id, strategy_id)
        
        if not self._loading_workspace:
            self._trigger_auto_save()
    
    def _schedule_strategy_sync(self, page_id: str, strategy_id: str):
        """Planifie une synchronisation de stratégie avec debounce"""
        # Créer le dictionnaire de timers si nécessaire
        if not hasattr(self, '_strategy_sync_timers'):
            self._strategy_sync_timers: dict[str, QTimer] = {}
        
        # Annuler le timer existant pour cette stratégie
        if strategy_id in self._strategy_sync_timers:
            self._strategy_sync_timers[strategy_id].stop()
        else:
            timer = QTimer()
            timer.setSingleShot(True)
            self._strategy_sync_timers[strategy_id] = timer
        
        # Configurer le timer pour synchroniser après 500ms d'inactivité
        timer = self._strategy_sync_timers[strategy_id]
        try:
            timer.timeout.disconnect()
        except RuntimeError:
            pass  # Pas de connexion à déconnecter
        timer.timeout.connect(lambda: self._do_strategy_sync(page_id, strategy_id))
        timer.start(500)
    
    def _do_strategy_sync(self, page_id: str, strategy_id: str):
        """Effectue la synchronisation d'une stratégie avec le serveur"""
        if not self._online_mode or not self.alarm_server:
            return
        
        if not page_id or page_id not in self.pages:
            return
        
        page_widget = self.pages[page_id]
        if strategy_id not in page_widget.strategies:
            return
        
        strategy = page_widget.strategies[strategy_id]
        print(f"[Page] Syncing strategy update '{strategy.name}' to server", flush=True)
        self.server_handler.sync_strategy('update', strategy, page_id)
    
    def _on_strategy_deleted(self, page_id: str, strategy_id: str):
        """Appelé quand une stratégie est supprimée"""
        print(f"[Page] Strategy deleted - page_id={page_id}, strategy_id={strategy_id}", flush=True)
        
        # Annuler tout timer de sync en attente pour cette stratégie
        if hasattr(self, '_strategy_sync_timers') and strategy_id in self._strategy_sync_timers:
            self._strategy_sync_timers[strategy_id].stop()
            del self._strategy_sync_timers[strategy_id]
        
        # Synchroniser avec le serveur
        if self._online_mode and self.alarm_server:
            self.alarm_server.delete_alarm(strategy_id=strategy_id)
        
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
            
            # Synchroniser avec le serveur
            if self._online_mode and self.alarm_server:
                self.alarm_server.update_page(page_id, new_name)
            
            self.statusbar.showMessage(f"Page renommée: {new_name}", 2000)
    
    def _on_page_deleted(self, page_id: str):
        """Appelé quand on supprime une page"""
        if page_id in self.pages:
            page_name = self.pages[page_id].page.name
            self._remove_page(page_id)
            self.statusbar.showMessage(f"Page '{page_name}' supprimée", 3000)
    
    def _on_refresh_requested(self):
        """Rafraîchit toutes les données depuis le serveur"""
        if not self._online_mode or not self.alarm_server:
            self.statusbar.showMessage("⚠️ Non connecté au serveur", 3000)
            return
        
        self.statusbar.showMessage("🔄 Rafraîchissement en cours...", 2000)
        
        # Vider toutes les pages locales
        self.sidebar.clear_pages()
        for page_id in list(self.pages.keys()):
            page_widget = self.pages.pop(page_id)
            self.page_stack.removeWidget(page_widget)
            page_widget.deleteLater()
        
        self._synced_strategies.clear()
        self.current_page_id = None
        
        # Relancer la connexion WebSocket pour récupérer l'état initial
        self.server_handler.stop_sync()
        QTimer.singleShot(500, self.server_handler.start_sync)
    
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
                from ..models.page import Page
                page = Page(name=page_name, id=page_id)
                self._add_page(page, select=False)
                page_widget = self.pages[page_id]
                
                # Charger les stratégies
                for strategy_data in page_data.get('strategies', []):
                    strategy = Strategy.from_dict(strategy_data)
                    page_widget.add_strategy(strategy)
    
    def closeEvent(self, event):
        """Appelé quand l'application se ferme"""
        # Si connecté au serveur, les données sont déjà synchronisées
        if self._online_mode and self.alarm_server:
            # Fermer proprement la connexion WebSocket
            if hasattr(self.alarm_server, 'stop'):
                self.alarm_server.stop()
        
        # Arrêter Bloomberg si démarré
        if self._bloomberg_started and self.bloomberg_service:
            try:
                self.bloomberg_service.stop()
            except:
                pass
        
        event.accept()
    
    def _manage_groups(self):
        """Ouvre le dialog de gestion des groupes"""
        if not self.auth_service.is_authenticated():
            QMessageBox.warning(
                self,
                "Non connecté",
                "Vous devez être connecté au serveur pour gérer les groupes."
            )
            return
        
        dialog = GroupDialog(self.auth_service, self)
        dialog.exec()
    
    def _share_current_page(self):
        """Ouvre le dialog de partage de la page courante"""
        if not self.auth_service.is_authenticated():
            QMessageBox.warning(
                self,
                "Non connecté",
                "Vous devez être connecté au serveur pour partager une page."
            )
            return
        
        if not self.current_page_id:
            QMessageBox.warning(
                self,
                "Pas de page",
                "Aucune page sélectionnée."
            )
            return
        
        page_widget = self.pages.get(self.current_page_id)
        if not page_widget:
            return
        
        # Vérifier si l'utilisateur est owner
        page = page_widget.page
        if not getattr(page, 'is_owner', True):
            QMessageBox.warning(
                self,
                "Permission refusée",
                "Seul le propriétaire peut partager cette page."
            )
            return
        
        dialog = SharePageDialog(
            self.auth_service,
            self.current_page_id,
            page.name,
            self
        )
        dialog.exec()
