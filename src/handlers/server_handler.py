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
        """Crée les alarmes pour une stratégie (une alarme par leg)"""
        # Filtrer les legs avec ticker vide
        legs_with_ticker = [leg for leg in strategy.legs if leg.ticker and leg.ticker.strip()]
        
        if len(legs_with_ticker) == 0:
            # Stratégie sans legs valides - créer une alarme placeholder
            alarm_data = self._build_alarm_data(strategy, 0, None)
            self.window.alarm_server.create_alarm(page_id, alarm_data)
        else:
            for leg_idx, leg in enumerate(legs_with_ticker):
                alarm_data = self._build_alarm_data(strategy, leg_idx, leg)
                self.window.alarm_server.create_alarm(page_id, alarm_data)
        
        print(f"[Server] Synced strategy '{strategy.name}' with {len(legs_with_ticker)} legs")
    
    def _build_alarm_data(self, strategy: Strategy, leg_idx: int, leg) -> dict:
        """Construit les données d'alarme pour le serveur
        
        Args:
            strategy: La stratégie parente
            leg_idx: Index du leg dans la stratégie
            leg: L'objet OptionLeg (peut être None si stratégie sans legs)
        """
        from ..models.strategy import Position
        
        data = {
            'strategy_id': strategy.id,
            'strategy_name': strategy.name,
            'leg_index': leg_idx,
            'target_value': strategy.target_price or 0.0,
            'target_price': strategy.target_price or 0.0,
            'condition': 'above' if strategy.target_condition == TargetCondition.SUPERIEUR else 'below',
            'active': True,
            # Client/Action de la stratégie
            'client': strategy.client or '',
            'action': strategy.action or '',
            'status': strategy.status.value if strategy.status else 'En cours'
        }
        
        # Ajouter les données du leg s'il existe
        if leg:
            data.update({
                'leg_id': leg.id,
                'ticker': leg.ticker,
                'option': leg.ticker,  # Pour compatibilité
                'position': leg.position.value,  # 'long' ou 'short'
                'quantity': leg.quantity
            })
        else:
            data.update({
                'leg_id': '',
                'ticker': '',
                'option': '',
                'position': 'long',
                'quantity': 1
            })
        
        return data
    
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
        
        # Charger les pages avec toutes leurs propriétés
        for idx, page_data in enumerate(pages_data):
            page = Page(
                id=page_data.get('id'),
                name=page_data.get('name', 'Page sans nom'),
                owner_id=page_data.get('owner_id'),
                owner_name=page_data.get('owner_name'),
                is_owner=page_data.get('is_owner', True),
                group_id=page_data.get('group_id'),
                group_name=page_data.get('group_name'),
                shared_by=page_data.get('shared_by'),
                can_edit=page_data.get('can_edit', True),
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
        from ..models.strategy import StrategyStatus, OptionLeg
        
        strategies_by_page = {}
        
        # Trier par leg_index pour garantir l'ordre des legs
        sorted_alarms = sorted(alarms_data, key=lambda x: (x.get('strategy_id', ''), x.get('leg_index', 0)))
        
        for alarm_data in sorted_alarms:
            page_id = alarm_data.get('page_id')
            strategy_id = alarm_data.get('strategy_id')
            
            if not page_id or not strategy_id:
                continue
            
            if page_id not in strategies_by_page:
                strategies_by_page[page_id] = {}
            
            if strategy_id not in strategies_by_page[page_id]:
                # Créer la stratégie avec toutes ses propriétés
                strategy = Strategy(
                    id=strategy_id,
                    name=alarm_data.get('strategy_name', 'Stratégie'),
                    client=alarm_data.get('client') or None,
                    action=alarm_data.get('action') or None
                )
                strategy.target_price = alarm_data.get('target_value', 0.0) or alarm_data.get('target_price', 0.0)
                condition = alarm_data.get('condition', 'below')
                strategy.target_condition = TargetCondition.SUPERIEUR if condition == 'above' else TargetCondition.INFERIEUR
                
                # Charger le status
                status_str = alarm_data.get('status', 'En cours')
                try:
                    strategy.status = StrategyStatus(status_str)
                except ValueError:
                    strategy.status = StrategyStatus.EN_COURS
                
                strategies_by_page[page_id][strategy_id] = strategy
            
            # Ajouter un leg si ticker non vide
            strategy = strategies_by_page[page_id][strategy_id]
            ticker = alarm_data.get('ticker', '') or alarm_data.get('option', '')
            if ticker:
                # Récupérer position et quantity depuis les données (avec valeurs par défaut robustes)
                position_str = alarm_data.get('position') or 'long'  # None -> 'long'
                position = Position.LONG if position_str == 'long' else Position.SHORT
                quantity = alarm_data.get('quantity') or 1  # None -> 1
                if not isinstance(quantity, int):
                    quantity = int(quantity) if quantity else 1
                leg_id = alarm_data.get('leg_id') or ''
                
                # Créer le leg avec toutes ses propriétés
                if leg_id:
                    leg = OptionLeg(
                        id=leg_id,
                        ticker=ticker,
                        position=position,
                        quantity=quantity
                    )
                else:
                    leg = OptionLeg(
                        ticker=ticker,
                        position=position,
                        quantity=quantity
                    )
                strategy.legs.append(leg)
        
        # Log résumé des stratégies chargées
        total_strategies = sum(len(strategies) for strategies in strategies_by_page.values())
        total_legs = sum(len(s.legs) for strategies in strategies_by_page.values() for s in strategies.values())
        print(f"[Server] Loaded {total_strategies} strategies with {total_legs} legs total")
        
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
