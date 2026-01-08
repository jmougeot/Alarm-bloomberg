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
        # Note: La synchronisation avec le serveur est maintenant gérée par main_window._on_page_modified
        # qui utilise server_handler.sync_strategy() pour éviter les doublons
        
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
            
            # Note: La suppression sur le serveur est gérée par main_window._on_strategy_deleted
            # qui utilise alarm_server.delete_alarm()
            
            self.window.statusbar.showMessage(f"Stratégie '{strategy.name}' supprimée", 3000)
    
    def on_strategy_updated(self, strategy_id: str):
        """Appelé quand une stratégie est mise à jour"""
        # La synchronisation avec le serveur est gérée par main_window._on_page_modified
        # qui utilise server_handler.sync_strategy() - ne rien faire ici pour éviter la double sync
        pass
    
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

