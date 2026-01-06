"""
Gestion de la synchronisation avec le serveur d'alarmes
"""
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QMessageBox

from ..services.alarm_server_service import AlarmServerService
from ..models.page import Page
from ..models.strategy import Strategy, TargetCondition, Position

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class ServerHandler:
    """Gère la synchronisation avec le serveur d'alarmes"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
    
    def start_sync(self):
        """Démarre la synchronisation avec le serveur"""
        try:
            ws_url = self.window.auth_service.get_ws_url()
            
            # Créer le service WebSocket
            self.window.alarm_server = AlarmServerService(self.window)
            
            # Connecter les signaux
            self.window.alarm_server.connected.connect(self._on_connected)
            self.window.alarm_server.disconnected.connect(self._on_disconnected)
            self.window.alarm_server.error_occurred.connect(self._on_error)
            self.window.alarm_server.auth_required.connect(self._on_auth_required)
            self.window.alarm_server.initial_state_received.connect(self._on_initial_state)
            self.window.alarm_server.alarm_created.connect(self._on_alarm_created)
            self.window.alarm_server.alarm_updated.connect(self._on_alarm_updated)
            self.window.alarm_server.alarm_deleted.connect(self._on_alarm_deleted)
            self.window.alarm_server.page_created.connect(self._on_page_created)
            
            # Démarrer la connexion
            self.window.alarm_server.start(ws_url)
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
        if self.window.alarm_server:
            self.window.alarm_server.stop()
            self.window.alarm_server = None
        self.window._online_mode = False
    
    def sync_strategy(self, action: str, strategy: Strategy, page_id: str):
        """Synchronise une stratégie avec le serveur"""
        if not self.window._online_mode or not self.window.alarm_server:
            return
        
        print(f"[Server] Syncing strategy '{strategy.name}' - action={action}, legs={len(strategy.legs)}", flush=True)
        
        if action == 'create':
            self._create_strategy_alarms(strategy, page_id)
            self.window._synced_strategies.add(strategy.id)
        
        elif action == 'update':
            # Supprimer puis recréer
            if strategy.id in self.window._synced_strategies:
                print(f"[Server] Updating strategy: deleting old alarms and recreating", flush=True)
                self.window.alarm_server.delete_alarm(strategy_id=strategy.id)
            else:
                print(f"[Server] Strategy not yet synced, creating instead of updating", flush=True)
            
            self._create_strategy_alarms(strategy, page_id)
            self.window._synced_strategies.add(strategy.id)
        
        elif action == 'delete':
            self.window.alarm_server.delete_alarm(strategy.id)
    
    def _create_strategy_alarms(self, strategy: Strategy, page_id: str):
        """Crée les alarmes pour une stratégie"""
        if len(strategy.legs) == 0:
            alarm_data = self._build_alarm_data(strategy, 0, '', '')
            print(f"[Server] Creating alarm (no legs): {strategy.name}", flush=True)
            self.window.alarm_server.create_alarm(page_id, alarm_data)
        else:
            for leg_idx, leg in enumerate(strategy.legs):
                alarm_data = self._build_alarm_data(strategy, leg_idx, leg.ticker, leg.ticker)
                print(f"[Server] Creating alarm: {strategy.name} - {leg.ticker}", flush=True)
                self.window.alarm_server.create_alarm(page_id, alarm_data)
    
    def _build_alarm_data(self, strategy: Strategy, leg_idx: int, ticker: str, option: str) -> dict:
        """Construit les données d'alarme pour le serveur"""
        return {
            'strategy_id': strategy.id,
            'strategy_name': strategy.name,
            'leg_index': leg_idx,
            'ticker': ticker,
            'option': option,
            'target_value': strategy.target_price or 0.0,
            'target_price': strategy.target_price or 0.0,
            'condition': 'above' if strategy.target_condition == TargetCondition.SUPERIEUR else 'below',
            'active': True
        }
    
    # === Callbacks serveur ===
    
    def _on_connected(self):
        """Appelé quand la connexion au serveur est établie"""
        self.window.statusbar.showMessage("✓ Connecté au serveur")
        print("[Server] Connected")
    
    def _on_disconnected(self):
        """Appelé quand la connexion au serveur est perdue"""
        self.window.statusbar.showMessage("⚠ Déconnecté du serveur - Tentative de reconnexion...")
        print("[Server] Disconnected")
    
    def _on_error(self, error_msg: str):
        """Appelé en cas d'erreur serveur"""
        print(f"[Server] Error: {error_msg}")
        
        # Ignorer les erreurs non critiques
        non_critical_errors = [
            "Alarm not found",
            "Page not found",
            "Strategy not found",
            "HTTP 403"
        ]
        
        if any(err.lower() in error_msg.lower() for err in non_critical_errors):
            return
        
        QMessageBox.warning(self.window, "Erreur serveur", error_msg)
    
    def _on_auth_required(self):
        """Appelé quand une ré-authentification est nécessaire"""
        print("[Server] Authentication required - showing login dialog")
        self.window.statusbar.showMessage("⚠ Session expirée - Reconnexion requise")
        
        # Effacer le token et stopper la connexion
        self.window.auth_service.logout()
        self.stop_sync()
        
        # Afficher le dialog de login
        self.window.auth_handler.show_login_dialog()
    
    def _on_initial_state(self, state: dict):
        """Appelé quand l'état initial est reçu du serveur"""
        pages_data = state.get('pages', [])
        alarms_data = state.get('alarms', [])
        
        print(f"[Server] Initial state received: {len(pages_data)} pages, {len(alarms_data)} alarms")
        
        # Charger les pages
        for idx, page_data in enumerate(pages_data):
            page = Page(
                id=page_data.get('id'),
                name=page_data.get('name', 'Page sans nom')
            )
            self.window._add_page(page, select=(idx == 0), sync_to_server=False)
        
        # Regrouper les alarmes par page et stratégie
        strategies_by_page = self._group_alarms_by_strategy(alarms_data)
        
        # Ajouter les stratégies aux pages
        for page_id, strategies_dict in strategies_by_page.items():
            if page_id in self.window.pages:
                page_widget = self.window.pages[page_id]
                for strategy in strategies_dict.values():
                    print(f"[Server] Adding strategy '{strategy.name}' to page {page_id}", flush=True)
                    page_widget.add_strategy(strategy, sync_to_server=False)
                    self.window._synced_strategies.add(strategy.id)
            else:
                print(f"[Server] Warning: Page {page_id} not found for strategies", flush=True)
        
        self.window.statusbar.showMessage(f"Synchronisé: {len(pages_data)} pages, {len(alarms_data)} alarmes", 5000)
    
    def _group_alarms_by_strategy(self, alarms_data: list) -> dict:
        """Regroupe les alarmes par page et stratégie"""
        strategies_by_page = {}
        
        for alarm_data in alarms_data:
            page_id = alarm_data.get('page_id')
            strategy_id = alarm_data.get('strategy_id')
            
            if not page_id or not strategy_id:
                continue
            
            if page_id not in strategies_by_page:
                strategies_by_page[page_id] = {}
            
            if strategy_id not in strategies_by_page[page_id]:
                strategy = Strategy(
                    id=strategy_id,
                    name=alarm_data.get('strategy_name', 'Stratégie')
                )
                strategy.target_price = alarm_data.get('target_value', 0.0)
                condition = alarm_data.get('condition', 'below')
                strategy.target_condition = TargetCondition.SUPERIEUR if condition == 'above' else TargetCondition.INFERIEUR
                strategies_by_page[page_id][strategy_id] = strategy
            
            # Ajouter un leg si ticker non vide
            strategy = strategies_by_page[page_id][strategy_id]
            ticker = alarm_data.get('ticker', '') or alarm_data.get('option', '')
            if ticker:
                strategy.add_leg(ticker=ticker, position=Position.LONG, quantity=1)
        
        return strategies_by_page
    
    def _on_alarm_created(self, alarm_data: dict):
        """Appelé quand une alarme est créée sur le serveur"""
        print(f"[Server] Alarm created: {alarm_data.get('id')}")
    
    def _on_alarm_updated(self, alarm_data: dict):
        """Appelé quand une alarme est mise à jour sur le serveur"""
        print(f"[Server] Alarm updated: {alarm_data.get('id')}")
    
    def _on_alarm_deleted(self, alarm_id: str):
        """Appelé quand une alarme est supprimée sur le serveur"""
        print(f"[Server] Alarm deleted: {alarm_id}")
    
    def _on_page_created(self, page_data: dict):
        """Appelé quand une page est créée sur le serveur"""
        print(f"[Server] Page created: {page_data.get('name')}")
        self.window._subscribe_all_tickers()
