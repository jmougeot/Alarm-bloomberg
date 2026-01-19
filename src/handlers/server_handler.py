"""
Gestion de la synchronisation avec le serveur
"""
from typing import TYPE_CHECKING, Dict, List

from PySide6.QtWidgets import QMessageBox

from ..services.server_service import ServerService
from ..models.page import Page
from ..models.strategy import Strategy, StrategyStatus, OptionLeg, TargetCondition, Position

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class ServerHandler:
    """Gère la synchronisation avec le serveur"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
        self._synced_strategies: set = set()
    
    def start_sync(self):
        """Démarre la synchronisation avec le serveur"""
        try:
            ws_url = self.window.auth_service.get_ws_url()
            
            # Créer le service WebSocket
            self.window.server_service = ServerService(self.window)
            
            # Connecter les signaux
            self.window.server_service.connected.connect(self._on_connected)
            self.window.server_service.disconnected.connect(self._on_disconnected)
            self.window.server_service.error_occurred.connect(self._on_error)
            self.window.server_service.auth_required.connect(self._on_auth_required)
            self.window.server_service.initial_state_received.connect(self._on_initial_state)
            
            # Pages
            self.window.server_service.page_created.connect(self._on_page_created)
            self.window.server_service.page_updated.connect(self._on_page_updated)
            self.window.server_service.page_deleted.connect(self._on_page_deleted)
            
            # Strategies
            self.window.server_service.strategy_created.connect(self._on_strategy_created)
            self.window.server_service.strategy_updated.connect(self._on_strategy_updated)
            self.window.server_service.strategy_deleted.connect(self._on_strategy_deleted)
            
            # Démarrer
            self.window.server_service.start(ws_url)
            self.window._online_mode = True
            
        except Exception as e:
            QMessageBox.warning(
                self.window,
                "Erreur de connexion",
                f"Impossible de se connecter au serveur:\n{str(e)}\n\nContinuer en mode hors ligne."
            )
            self.window._online_mode = False
    
    def stop_sync(self):
        """Arrête la synchronisation"""
        if self.window.server_service:
            self.window.server_service.stop()
            self.window.server_service = None
        self.window._online_mode = False
    
    # === Synchronisation des stratégies ===
    
    def sync_strategy(self, action: str, strategy: Strategy, page_id: str):
        """Synchronise une stratégie avec le serveur"""
        if not self.window._online_mode or not self.window.server_service:
            return
        
        print(f"[Server] Sync strategy '{strategy.name}' - {action}")
        
        if action == 'create':
            self.window.server_service.create_strategy(page_id, strategy.to_server_dict())
            self._synced_strategies.add(strategy.id)
            
        elif action == 'update':
            self.window.server_service.update_strategy(strategy.id, strategy.to_server_dict())
            self._synced_strategies.add(strategy.id)
            
        elif action == 'delete':
            self.window.server_service.delete_strategy(strategy.id)
            self._synced_strategies.discard(strategy.id)
    
    def sync_page(self, action: str, page: Page):
        """Synchronise une page avec le serveur"""
        if not self.window._online_mode or not self.window.server_service:
            return
        
        print(f"[Server] Sync page '{page.name}' - {action}")
        
        if action == 'create':
            self.window.server_service.create_page(page.name, page.id)
        elif action == 'update':
            self.window.server_service.update_page(page.id, page.name)
        elif action == 'delete':
            self.window.server_service.delete_page(page.id)
    
    # === Callbacks serveur ===
    
    def _on_connected(self):
        """Connexion établie"""
        self.window.statusbar.showMessage("✓ Connecté au serveur")
        print("[Server] Connected")
    
    def _on_disconnected(self):
        """Connexion perdue"""
        self.window.statusbar.showMessage("⚠ Déconnecté du serveur")
        print("[Server] Disconnected")
    
    def _on_error(self, error_msg: str):
        """Erreur serveur"""
        print(f"[Server] Error: {error_msg}")
        
        # Ignorer les erreurs non critiques
        if any(x in error_msg.lower() for x in ["not found", "http 403"]):
            return
        
        self.window.statusbar.showMessage(f"⚠ Erreur: {error_msg}", 5000)
    
    def _on_auth_required(self):
        """Ré-authentification nécessaire"""
        print("[Server] Auth required")
        self.window.statusbar.showMessage("⚠ Session expirée")
        self.window.auth_service.logout()
        self.stop_sync()
        self.window.auth_handler.show_login_dialog()
    
    def _on_initial_state(self, state: dict):
        """État initial reçu du serveur"""
        pages_data = state.get('pages', [])
        strategies_data = state.get('strategies', [])
        
        print(f"[Server] Initial state: {len(pages_data)} pages, {len(strategies_data)} strategies")
        
        # Si aucune page, créer une page par défaut "Général"
        if not pages_data:
            print("[Server] No pages found, creating default page 'Général'")
            default_page = Page(name="Général")
            # Ajouter localement ET synchroniser avec le serveur
            self.window._add_page(default_page, select=True, sync_to_server=True)
            return
        
        # Charger les pages
        for idx, page_data in enumerate(pages_data):
            page = Page.from_dict(page_data)
            self.window._add_page(page, select=(idx == 0), sync_to_server=False)
        
        # Grouper les stratégies par page
        strategies_by_page = self._group_strategies_by_page(strategies_data)
        
        # Ajouter les stratégies
        for page_id, strategies in strategies_by_page.items():
            if page_id in self.window.pages:
                page_widget = self.window.pages[page_id]
                for strategy in strategies:
                    page_widget.add_strategy(strategy, sync_to_server=False)
                    self._synced_strategies.add(strategy.id)
        
        self.window.statusbar.showMessage(
            f"Synchronisé: {len(pages_data)} pages, {len(strategies_data)} stratégies", 
            5000
        )
    
    def _group_strategies_by_page(self, strategies_data: List[dict]) -> Dict[str, List[Strategy]]:
        """Regroupe les stratégies par page"""
        result = {}
        
        for data in strategies_data:
            page_id = data.get('page_id')
            if not page_id:
                continue
            
            strategy = Strategy.from_server_dict(data)
            
            if page_id not in result:
                result[page_id] = []
            result[page_id].append(strategy)
        
        return result
    
    def _on_page_created(self, data: dict):
        """Page créée par un autre client"""
        print(f"[Server] Page created: {data.get('name')}")
    
    def _on_page_updated(self, data: dict):
        """Page mise à jour par un autre client"""
        print(f"[Server] Page updated: {data.get('name')}")
    
    def _on_page_deleted(self, page_id: str):
        """Page supprimée par un autre client"""
        print(f"[Server] Page deleted: {page_id}")
    
    def _on_strategy_created(self, data: dict):
        """Stratégie créée par un autre client"""
        print(f"[Server] Strategy created: {data.get('name')}")
    
    def _on_strategy_updated(self, data: dict):
        """Stratégie mise à jour par un autre client"""
        print(f"[Server] Strategy updated: {data.get('name')}")
    
    def _on_strategy_deleted(self, strategy_id: str):
        """Stratégie supprimée par un autre client"""
        print(f"[Server] Strategy deleted: {strategy_id}")
