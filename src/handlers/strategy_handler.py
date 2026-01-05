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
    
    def add_strategy_widget(self, strategy: 'Strategy'):
        """Ajoute un widget de stratégie"""
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
        
        # S'abonner aux tickers existants
        if self.window.bloomberg_service and self.window.bloomberg_service.is_connected:
            for ticker in strategy.get_all_tickers():
                self.window.bloomberg_service.subscribe(ticker)
    
    def on_strategy_deleted(self, strategy_id: str):
        """Appelé quand une stratégie est supprimée"""
        if strategy_id in self.window.strategy_widgets:
            widget = self.window.strategy_widgets.pop(strategy_id)
            self.window.strategies_layout.removeWidget(widget)
            widget.deleteLater()
        
        if strategy_id in self.window.strategies:
            strategy = self.window.strategies.pop(strategy_id)
            self.window.statusbar.showMessage(f"Stratégie '{strategy.name}' supprimée", 3000)
    
    def on_strategy_updated(self, strategy_id: str):
        """Appelé quand une stratégie est mise à jour"""
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
