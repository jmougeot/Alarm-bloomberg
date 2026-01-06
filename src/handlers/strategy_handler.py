"""
Gestion des stratégies (ajout, suppression, mise à jour)
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow
    from ..models.strategy import Strategy


class StrategyHandler:
    """Gère les opérations sur les stratégies"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
    
    def add_new_strategy(self):
        """Ajoute un nouveau bloc de stratégie"""
        from ..models.strategy import Strategy
        
        strategy = Strategy(name=f"Stratégie {len(self.window.strategies) + 1}")
        self.add_strategy_widget(strategy)
        self.window.statusbar.showMessage(f"Stratégie '{strategy.name}' créée", 3000)
    
    def add_strategy_widget(self, strategy: 'Strategy', sync_to_server: bool = True):
        """Ajoute un widget de stratégie"""
        print(f"[Strategy] add_strategy_widget called - sync_to_server={sync_to_server}", flush=True)
        from ..ui.strategy_block_widget import StrategyBlockWidget
        
        self.window.strategies[strategy.id] = strategy
        
        widget = StrategyBlockWidget(strategy)
        widget.strategy_deleted.connect(self.on_strategy_deleted)
        widget.strategy_updated.connect(self.on_strategy_updated)
        widget.ticker_added.connect(self.on_ticker_added)
        widget.ticker_removed.connect(self.on_ticker_removed)
        widget.target_reached.connect(self.window.alert_handler.on_target_reached)
        widget.target_left.connect(self.window.alert_handler.on_target_left)
        
        self.window.strategy_widgets[strategy.id] = widget
        
        # Insérer avant le stretch
        self.window.strategies_layout.insertWidget(
            self.window.strategies_layout.count() - 1, 
            widget
        )
        
        # Envoyer au serveur si connecté (sauf si c'est une stratégie déjà présente sur le serveur)
        if sync_to_server:
            self._sync_to_server('create', strategy)
        
        # S'abonner aux tickers existants
        if self.window.bloomberg_service and self.window.bloomberg_service.is_connected:
            for ticker in strategy.get_all_tickers():
                self.window.bloomberg_service.subscribe(ticker)
    
    def on_strategy_deleted(self, strategy_id: str):
        """Appelé quand une stratégie est supprimée"""
        strategy = self.window.strategies.get(strategy_id)
        
        if strategy_id in self.window.strategy_widgets:
            widget = self.window.strategy_widgets.pop(strategy_id)
            self.window.strategies_layout.removeWidget(widget)
            widget.deleteLater()
        
        if strategy_id in self.window.strategies:
            self.window.strategies.pop(strategy_id)
            
            # Envoyer la suppression au serveur
            self._sync_to_server('delete', strategy)
            
            self.window.statusbar.showMessage(f"Stratégie '{strategy.name}' supprimée", 3000)
    
    def on_strategy_updated(self, strategy_id: str):
        """Appelé quand une stratégie est mise à jour"""
        strategy = self.window.strategies.get(strategy_id)
        if strategy:
            # Envoyer la mise à jour au serveur
            self._sync_to_server('update', strategy)
    
    def on_ticker_added(self, ticker: str):
        """Appelé quand un ticker est ajouté"""
        if self.window.bloomberg_service and self.window.bloomberg_service.is_connected:
            self.window.bloomberg_service.subscribe(ticker)
            self.window.statusbar.showMessage(f"Abonné à {ticker}", 2000)
    
    def on_ticker_removed(self, ticker: str):
        """Appelé quand un ticker est supprimé"""
        # Vérifier si le ticker est encore utilisé ailleurs
        ticker_still_used = any(
            ticker in strategy.get_all_tickers()
            for strategy in self.window.strategies.values()
        )
        
        if not ticker_still_used and self.window.bloomberg_service:
            self.window.bloomberg_service.unsubscribe(ticker)
    
    def _sync_to_server(self, action: str, strategy: 'Strategy'):
        """Synchronise une modification de stratégie avec le serveur"""
        print(f"[Strategy] _sync_to_server called - action={action}, strategy={strategy.name}", flush=True)
        if not self.window._online_mode or not self.window.alarm_server:
            print(f"[Strategy] Sync skipped - online_mode={self.window._online_mode}, alarm_server={self.window.alarm_server is not None}", flush=True)
            return
        
        print(f"[Strategy] Syncing '{strategy.name}' - action: {action}, legs: {len(strategy.legs)}", flush=True)
        
        # Les stratégies sont converties en alarmes pour le serveur
        # Une stratégie peut contenir plusieurs legs, donc plusieurs alarmes
        if not self.window.current_page_id:
            print(f"[Strategy] No current page - cannot sync alarm")
            return
        
        page_id = self.window.current_page_id
        print(f"[Strategy] Current page ID: {page_id}")
        
        if action == 'create':
            # Créer une alarme pour chaque leg de la stratégie
            from ..models.strategy import TargetCondition
            for leg_idx, leg in enumerate(strategy.legs):
                alarm_data = {
                    'strategy_id': strategy.id,
                    'strategy_name': strategy.name,
                    'leg_index': leg_idx,
                    'ticker': leg.ticker,
                    'target_value': strategy.target_price or 0.0,
                    'condition': 'above' if strategy.target_condition == TargetCondition.SUPERIEUR else 'below',
                    'active': True
                }
                self.window.alarm_server.create_alarm(page_id, alarm_data)
        
        elif action == 'update':
            # Mettre à jour les alarmes de cette stratégie
            from ..models.strategy import TargetCondition
            for leg_idx, leg in enumerate(strategy.legs):
                alarm_data = {
                    'strategy_id': strategy.id,
                    'strategy_name': strategy.name,
                    'leg_index': leg_idx,
                    'ticker': leg.ticker,
                    'target_value': strategy.target_price or 0.0,
                    'condition': 'above' if strategy.target_condition == TargetCondition.SUPERIEUR else 'below',
                    'active': True
                }
                self.window.alarm_server.update_alarm(strategy.id, alarm_data)
        
        elif action == 'delete':
            # Supprimer toutes les alarmes associées à cette stratégie
            self.window.alarm_server.delete_alarm(strategy.id)
