"""
Gestion de la connexion Bloomberg et des subscriptions
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class BloombergHandler:
    """Gère la connexion Bloomberg et les mises à jour de prix"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
    
    def setup_bloomberg(self):
        """Configure le service Bloomberg"""
        from ..services.bloomberg_service import BloombergService
        
        self.window.bloomberg_service = BloombergService()
        self.window.bloomberg_service.price_updated.connect(self.on_price_updated)
        self.window.bloomberg_service.connection_status.connect(self.on_connection_status)
        self.window.bloomberg_service.subscription_started.connect(self.on_subscription_started)
        self.window.bloomberg_service.subscription_failed.connect(self.on_subscription_failed)
    
    def start_connection(self):
        """Démarre la connexion Bloomberg automatiquement"""
        if not self.window.bloomberg_service.is_connected:  # type: ignore
            self.window.bloomberg_service.start()  # type: ignore
            
            # S'abonner à tous les tickers existants
            for strategy in self.window.strategies.values():
                for ticker in strategy.get_all_tickers():
                    self.window.bloomberg_service.subscribe(ticker)  # type: ignore
    
    def on_price_updated(self, ticker: str, last: float, bid: float, ask: float):
        """Appelé quand un prix est mis à jour"""
        for widget in self.window.strategy_widgets.values():
            widget.update_price(ticker, last, bid, ask)
    
    def on_connection_status(self, connected: bool, message: str):
        """Appelé quand le status de connexion change"""
        if connected:
            self.window.connection_label.setText(f"🟢 {message}")
            self.window.connection_label.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
        else:
            self.window.connection_label.setText(f"🔴 {message}")
            self.window.connection_label.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
        
        self.window.statusbar.showMessage(message, 5000)
    
    def on_subscription_started(self, ticker: str):
        """Appelé quand une subscription démarre"""
        self.window.statusbar.showMessage(f"✓ Subscription active: {ticker}", 2000)
    
    def on_subscription_failed(self, ticker: str, error: str):
        """Appelé quand une subscription échoue"""
        self.window.statusbar.showMessage(f"✗ Échec subscription {ticker}: {error}", 5000)
