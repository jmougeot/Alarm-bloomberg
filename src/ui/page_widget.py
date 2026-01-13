"""
Widget d'une page contenant les stratégies
"""
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QScrollArea, QLabel
)
from PySide6.QtCore import Signal, Qt

from ..models.page import Page
from ..models.strategy import Strategy
from .strategy_block_widget import StrategyBlockWidget
from .styles.dark_theme import (
    BUTTON_PRIMARY_STYLE,
    SCROLL_AREA_STYLE,
    PAGE_HEADER_STYLE
)

if TYPE_CHECKING:
    from .main_window import MainWindow


class PageWidget(QWidget):
    """Widget représentant une page avec ses stratégies"""
    
    # Signaux
    strategy_added = Signal(str, Strategy)  # page_id, strategy
    strategy_deleted = Signal(str, str)  # page_id, strategy_id
    strategy_updated = Signal(str, str)  # page_id, strategy_id
    ticker_added = Signal(str)  # ticker
    ticker_removed = Signal(str)  # ticker
    target_reached = Signal(str)  # strategy_id
    target_left = Signal(str)  # strategy_id
    
    def __init__(self, page: Page, parent=None):
        super().__init__(parent)
        self.page = page
        self.strategies: dict[str, Strategy] = {}
        self.strategy_widgets: dict[str, StrategyBlockWidget] = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header de la page
        header = QWidget()
        header.setStyleSheet(PAGE_HEADER_STYLE)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        # Titre de la page
        self.title_label = QLabel(self.page.name)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Bouton ajouter stratégie
        self.add_strategy_btn = QPushButton("+ Nouvelle Stratégie")
        self.add_strategy_btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.add_strategy_btn.clicked.connect(self._on_add_strategy)
        header_layout.addWidget(self.add_strategy_btn)
        
        layout.addWidget(header)
        
        # Zone de scroll pour les stratégies
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore
        scroll_area.setStyleSheet(SCROLL_AREA_STYLE)
        
        self.strategies_container = QWidget()
        self.strategies_layout = QVBoxLayout(self.strategies_container)
        self.strategies_layout.setContentsMargins(20, 20, 20, 20)
        self.strategies_layout.setSpacing(16)
        self.strategies_layout.addStretch()
        
        scroll_area.setWidget(self.strategies_container)
        layout.addWidget(scroll_area)
    
    def update_title(self):
        """Met à jour le titre de la page"""
        self.title_label.setText(self.page.name)
    
    def add_strategy(self, strategy: Strategy, sync_to_server: bool = True):
        """Ajoute une stratégie à la page"""
        self.strategies[strategy.id] = strategy
        
        widget = StrategyBlockWidget(strategy)
        widget.strategy_deleted.connect(lambda sid: self._on_strategy_deleted(sid))
        widget.strategy_updated.connect(lambda sid: self.strategy_updated.emit(self.page.id, sid))
        widget.ticker_added.connect(self.ticker_added.emit)
        widget.ticker_removed.connect(self.ticker_removed.emit)
        widget.target_reached.connect(self.target_reached.emit)
        widget.target_left.connect(self.target_left.emit)
        
        self.strategy_widgets[strategy.id] = widget
        
        # Insérer avant le stretch
        self.strategies_layout.insertWidget(
            self.strategies_layout.count() - 1,
            widget
        )
        
        # Émettre le signal seulement si on doit synchroniser
        if sync_to_server:
            self.strategy_added.emit(self.page.id, strategy)
    
    def remove_strategy(self, strategy_id: str):
        """Supprime une stratégie de la page"""
        if strategy_id in self.strategy_widgets:
            widget = self.strategy_widgets.pop(strategy_id)
            self.strategies_layout.removeWidget(widget)
            widget.deleteLater()
        
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
    
    def update_price(self, ticker: str, last: float, bid: float, ask: float, delta: float = -999.0):
        """Met à jour les prix pour un ticker"""
        for widget in self.strategy_widgets.values():
            widget.update_price(ticker, last, bid, ask, delta)
    
    def get_all_tickers(self) -> set[str]:
        """Retourne tous les tickers de la page"""
        tickers = set()
        for strategy in self.strategies.values():
            tickers.update(strategy.get_all_tickers())
        return tickers
    
    def get_strategies(self) -> list[Strategy]:
        """Retourne toutes les stratégies"""
        return list(self.strategies.values())
    
    def _on_add_strategy(self):
        """Ajoute une nouvelle stratégie"""
        strategy = Strategy(name=f"Stratégie {len(self.strategies) + 1}")
        self.add_strategy(strategy)
    
    def _on_strategy_deleted(self, strategy_id: str):
        """Appelé quand une stratégie est supprimée"""
        self.remove_strategy(strategy_id)
        self.strategy_deleted.emit(self.page.id, strategy_id)
    
    def to_dict(self) -> dict:
        """Convertit la page et ses stratégies en dict"""
        return {
            'page': self.page.to_dict(),
            'strategies': [s.to_dict() for s in self.strategies.values()]
        }
    
    @classmethod
    def from_dict(cls, data: dict, parent=None) -> 'PageWidget':
        """Crée un PageWidget depuis un dictionnaire"""
        page = Page.from_dict(data['page'])
        widget = cls(page, parent)
        
        for strategy_data in data.get('strategies', []):
            strategy = Strategy.from_dict(strategy_data)
            widget.add_strategy(strategy)
        
        return widget
