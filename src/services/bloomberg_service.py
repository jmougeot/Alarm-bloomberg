"""
Service Bloomberg pour la gestion des subscriptions en temps réel.
Utilise les signaux Qt pour communiquer avec l'interface graphique.
"""
import sys
import os

# Ajouter le chemin du module bloomberg
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'bloomberg'))

from PySide6.QtCore import QObject, Signal, QThread, QMutex, QMutexLocker
from typing import Optional
from datetime import datetime

try:
    from blpapi_import_helper import blpapi
    BLPAPI_AVAILABLE = True
except ImportError:
    BLPAPI_AVAILABLE = False
    print("[WARNING] blpapi non disponible - Mode simulation activé")


DEFAULT_FIELDS = ["LAST_PRICE", "BID", "ASK"]
DEFAULT_SERVICE = "//blp/mktdata"


class PriceUpdate:
    """Structure pour les mises à jour de prix"""
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.last_price: Optional[float] = None
        self.bid: Optional[float] = None
        self.ask: Optional[float] = None
        self.timestamp: datetime = datetime.now()


class BloombergWorker(QThread):
    """Worker thread pour gérer la session Bloomberg"""
    
    price_updated = Signal(str, float, float, float)  # ticker, last, bid, ask
    subscription_started = Signal(str)  # ticker
    subscription_failed = Signal(str, str)  # ticker, error
    connection_status = Signal(bool, str)  # connected, message
    
    def __init__(self, host: str = "localhost", port: int = 8194):
        super().__init__()
        self.host = host
        self.port = port
        self.session: Optional['blpapi.Session'] = None
        self.subscriptions: dict[str, 'blpapi.CorrelationId'] = {}
        self.is_running = False
        self.mutex = QMutex()
        self._pending_subscriptions: list[str] = []
        self._pending_unsubscriptions: list[str] = []
    
    def run(self):
        """Boucle principale du thread Bloomberg"""
        if not BLPAPI_AVAILABLE:
            self.connection_status.emit(False, "blpapi non installé")
            self._run_simulation_mode()
            return
        
        try:
            # Configuration de la session
            session_options = blpapi.SessionOptions()
            session_options.setServerHost(self.host)
            session_options.setServerPort(self.port)
            session_options.setDefaultSubscriptionService(DEFAULT_SERVICE)
            
            self.session = blpapi.Session(session_options)
            
            if not self.session.start():
                self.connection_status.emit(False, "Impossible de démarrer la session")
                return
            
            if not self.session.openService(DEFAULT_SERVICE):
                self.connection_status.emit(False, f"Impossible d'ouvrir {DEFAULT_SERVICE}")
                return
            
            self.is_running = True
            self.connection_status.emit(True, "Connecté à Bloomberg")
            
            # Boucle d'événements
            while self.is_running:
                # Traiter les subscriptions/unsubscriptions en attente
                self._process_pending_operations()
                
                # Traiter les événements Bloomberg
                event = self.session.nextEvent(500)  # timeout 500ms
                self._process_event(event)
            
        except Exception as e:
            self.connection_status.emit(False, f"Erreur: {str(e)}")
        finally:
            if self.session:
                self.session.stop()
    
    def _run_simulation_mode(self):
        """Mode simulation sans Bloomberg"""
        import random
        import time
        
        self.is_running = True
        self.connection_status.emit(True, "Mode simulation (sans Bloomberg)")
        
        simulated_prices = {}
        
        while self.is_running:
            # Traiter les opérations en attente
            with QMutexLocker(self.mutex):
                for ticker in self._pending_subscriptions:
                    simulated_prices[ticker] = random.uniform(90, 110)
                    self.subscription_started.emit(ticker)
                self._pending_subscriptions.clear()
                
                for ticker in self._pending_unsubscriptions:
                    simulated_prices.pop(ticker, None)
                self._pending_unsubscriptions.clear()
            
            # Émettre des prix simulés
            for ticker, base_price in simulated_prices.items():
                variation = random.uniform(-0.5, 0.5)
                last = base_price + variation
                bid = last - random.uniform(0.01, 0.05)
                ask = last + random.uniform(0.01, 0.05)
                self.price_updated.emit(ticker, last, bid, ask)
                simulated_prices[ticker] = last
            
            time.sleep(1)  # Mise à jour chaque seconde
    
    def _process_pending_operations(self):
        """Traite les subscriptions/unsubscriptions en attente"""
        with QMutexLocker(self.mutex):
            # Nouvelles subscriptions
            if self._pending_subscriptions:
                sub_list = blpapi.SubscriptionList()
                for ticker in self._pending_subscriptions:
                    corr_id = blpapi.CorrelationId(ticker)
                    sub_list.add(ticker, DEFAULT_FIELDS, [], corr_id)
                    self.subscriptions[ticker] = corr_id
                
                self.session.subscribe(sub_list)
                self._pending_subscriptions.clear()
            
            # Unsubscriptions
            if self._pending_unsubscriptions:
                unsub_list = blpapi.SubscriptionList()
                for ticker in self._pending_unsubscriptions:
                    if ticker in self.subscriptions:
                        unsub_list.add(ticker, DEFAULT_FIELDS, [], self.subscriptions[ticker])
                        del self.subscriptions[ticker]
                
                self.session.unsubscribe(unsub_list)
                self._pending_unsubscriptions.clear()
    
    def _process_event(self, event):
        """Traite un événement Bloomberg"""
        if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
            for msg in event:
                ticker = msg.correlationId().value()
                
                last_price = None
                bid = None
                ask = None
                
                if msg.hasElement("LAST_PRICE"):
                    try:
                        last_price = msg.getElementAsFloat("LAST_PRICE")
                    except:
                        pass
                
                if msg.hasElement("BID"):
                    try:
                        bid = msg.getElementAsFloat("BID")
                    except:
                        pass
                
                if msg.hasElement("ASK"):
                    try:
                        ask = msg.getElementAsFloat("ASK")
                    except:
                        pass
                
                self.price_updated.emit(
                    ticker,
                    last_price if last_price else 0.0,
                    bid if bid else 0.0,
                    ask if ask else 0.0
                )
        
        elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
            for msg in event:
                ticker = msg.correlationId().value()
                if msg.messageType() == blpapi.Names.SUBSCRIPTION_STARTED:
                    self.subscription_started.emit(ticker)
                elif msg.messageType() == blpapi.Names.SUBSCRIPTION_FAILURE:
                    self.subscription_failed.emit(ticker, str(msg))
    
    def subscribe(self, ticker: str):
        """Ajoute une subscription (thread-safe)"""
        with QMutexLocker(self.mutex):
            if ticker not in self.subscriptions and ticker not in self._pending_subscriptions:
                self._pending_subscriptions.append(ticker)
    
    def unsubscribe(self, ticker: str):
        """Supprime une subscription (thread-safe)"""
        with QMutexLocker(self.mutex):
            if ticker in self.subscriptions or ticker in self._pending_subscriptions:
                self._pending_unsubscriptions.append(ticker)
                if ticker in self._pending_subscriptions:
                    self._pending_subscriptions.remove(ticker)
    
    def stop(self):
        """Arrête le worker"""
        self.is_running = False
        self.wait()


class BloombergService(QObject):
    """
    Service principal pour interagir avec Bloomberg.
    Gère les subscriptions et émet des signaux pour les mises à jour de prix.
    """
    
    # Signaux
    price_updated = Signal(str, float, float, float)  # ticker, last, bid, ask
    subscription_started = Signal(str)
    subscription_failed = Signal(str, str)
    connection_status = Signal(bool, str)
    
    def __init__(self, host: str = "localhost", port: int = 8194):
        super().__init__()
        self.worker: Optional[BloombergWorker] = None
        self.host = host
        self.port = port
        self._active_subscriptions: set[str] = set()
    
    def start(self):
        """Démarre le service Bloomberg"""
        if self.worker and self.worker.isRunning():
            return
        
        self.worker = BloombergWorker(self.host, self.port)
        
        # Connecter les signaux
        self.worker.price_updated.connect(self._on_price_updated)
        self.worker.subscription_started.connect(self._on_subscription_started)
        self.worker.subscription_failed.connect(self._on_subscription_failed)
        self.worker.connection_status.connect(self._on_connection_status)
        
        self.worker.start()
    
    def stop(self):
        """Arrête le service Bloomberg"""
        if self.worker:
            self.worker.stop()
            self.worker = None
        self._active_subscriptions.clear()
    
    def subscribe(self, ticker: str):
        """Subscribe à un ticker"""
        if not ticker or ticker in self._active_subscriptions:
            return
        
        self._active_subscriptions.add(ticker)
        if self.worker:
            self.worker.subscribe(ticker)
    
    def unsubscribe(self, ticker: str):
        """Unsubscribe d'un ticker"""
        if ticker not in self._active_subscriptions:
            return
        
        self._active_subscriptions.discard(ticker)
        if self.worker:
            self.worker.unsubscribe(ticker)
    
    def subscribe_multiple(self, tickers: list[str]):
        """Subscribe à plusieurs tickers"""
        for ticker in tickers:
            self.subscribe(ticker)
    
    def unsubscribe_all(self):
        """Unsubscribe de tous les tickers"""
        for ticker in list(self._active_subscriptions):
            self.unsubscribe(ticker)
    
    def _on_price_updated(self, ticker: str, last: float, bid: float, ask: float):
        """Relaye le signal de mise à jour de prix"""
        self.price_updated.emit(ticker, last, bid, ask)
    
    def _on_subscription_started(self, ticker: str):
        """Relaye le signal de subscription réussie"""
        self.subscription_started.emit(ticker)
    
    def _on_subscription_failed(self, ticker: str, error: str):
        """Relaye le signal d'erreur de subscription"""
        self._active_subscriptions.discard(ticker)
        self.subscription_failed.emit(ticker, error)
    
    def _on_connection_status(self, connected: bool, message: str):
        """Relaye le signal de status de connexion"""
        self.connection_status.emit(connected, message)
    
    @property
    def is_connected(self) -> bool:
        """Retourne True si le service est connecté"""
        return self.worker is not None and self.worker.isRunning()
    
    @property
    def active_subscriptions(self) -> set[str]:
        """Retourne les subscriptions actives"""
        return self._active_subscriptions.copy()
