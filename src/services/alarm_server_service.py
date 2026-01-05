"""
Service WebSocket pour la synchronisation avec le serveur d'alarmes
"""
import asyncio
import json
from typing import Optional, Callable, Dict, Any, List
import websockets
from websockets.client import WebSocketClientProtocol
from PySide6.QtCore import QObject, Signal, QThread


class AlarmServerService(QObject):
    """Service de communication WebSocket avec le serveur d'alarmes"""
    
    # Signaux Qt
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    
    # Signaux de synchronisation
    initial_state_received = Signal(dict)  # État initial du serveur
    alarm_created = Signal(dict)  # Nouvelle alarme
    alarm_updated = Signal(dict)  # Alarme modifiée
    alarm_deleted = Signal(str)  # ID de l'alarme supprimée
    alarm_triggered = Signal(dict)  # Alarme déclenchée
    page_created = Signal(dict)  # Nouvelle page
    page_updated = Signal(dict)  # Page modifiée
    page_deleted = Signal(str)  # ID de la page supprimée
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ws: Optional[WebSocketClientProtocol] = None
        self.ws_url: Optional[str] = None
        self._running = False
        self._reconnect_delay = 5.0
        self._thread: Optional[QThread] = None
        
    def start(self, ws_url: str):
        """Démarre la connexion WebSocket"""
        self.ws_url = ws_url
        self._running = True
        
        # Lancer dans un thread séparé pour ne pas bloquer l'UI
        self._thread = QThread()
        self._thread.run = lambda: asyncio.run(self._run_forever())
        self._thread.start()
    
    def stop(self):
        """Arrête la connexion WebSocket"""
        self._running = False
        if self._thread:
            self._thread.quit()
            self._thread.wait()
    
    async def _run_forever(self):
        """Boucle principale de connexion avec reconnexion automatique"""
        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                print(f"WebSocket error: {e}")
                self.error_occurred.emit(str(e))
                
            if self._running:
                print(f"Reconnecting in {self._reconnect_delay} seconds...")
                await asyncio.sleep(self._reconnect_delay)
    
    async def _connect_and_listen(self):
        """Se connecte et écoute les messages"""
        async with websockets.connect(self.ws_url) as ws:
            self.ws = ws
            self.connected.emit()
            print("Connected to alarm server")
            
            try:
                async for message in ws:
                    await self._handle_message(message)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
            finally:
                self.ws = None
                self.disconnected.emit()
    
    async def _handle_message(self, message: str):
        """Traite un message reçu du serveur"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            payload = data.get("payload", {})
            
            if msg_type == "initial_state":
                self.initial_state_received.emit(payload)
                
            elif msg_type == "alarm_update":
                action = payload.get("action")
                alarm_data = payload.get("data")
                
                if action == "created":
                    self.alarm_created.emit(alarm_data)
                elif action == "updated":
                    self.alarm_updated.emit(alarm_data)
                elif action == "deleted":
                    alarm_id = payload.get("alarm_id")
                    self.alarm_deleted.emit(alarm_id)
                elif action == "triggered":
                    self.alarm_triggered.emit(alarm_data)
                    
            elif msg_type == "page_update":
                action = payload.get("action")
                page_data = payload.get("data")
                
                if action == "created":
                    self.page_created.emit(page_data)
                elif action == "updated":
                    self.page_updated.emit(page_data)
                elif action == "deleted":
                    page_id = payload.get("page_id")
                    self.page_deleted.emit(page_id)
                    
            elif msg_type == "error":
                error_msg = payload.get("message", "Unknown error")
                self.error_occurred.emit(error_msg)
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse message: {e}")
    
    async def send_message(self, msg_type: str, payload: Dict[str, Any]):
        """Envoie un message au serveur"""
        if not self.ws:
            raise ConnectionError("Not connected to server")
            
        message = json.dumps({
            "type": msg_type,
            "payload": payload
        })
        
        await self.ws.send(message)
    
    # === Méthodes de synchronisation ===
    
    def create_alarm_sync(self, page_id: str, alarm_data: Dict[str, Any]):
        """Crée une alarme sur le serveur (version sync pour Qt)"""
        asyncio.run_coroutine_threadsafe(
            self.send_message("create_alarm", {
                "page_id": page_id,
                **alarm_data
            }),
            asyncio.get_event_loop()
        )
    
    def update_alarm_sync(self, alarm_id: str, updates: Dict[str, Any]):
        """Met à jour une alarme sur le serveur"""
        asyncio.run_coroutine_threadsafe(
            self.send_message("update_alarm", {
                "alarm_id": alarm_id,
                **updates
            }),
            asyncio.get_event_loop()
        )
    
    def delete_alarm_sync(self, alarm_id: str):
        """Supprime une alarme sur le serveur"""
        asyncio.run_coroutine_threadsafe(
            self.send_message("delete_alarm", {
                "alarm_id": alarm_id
            }),
            asyncio.get_event_loop()
        )
    
    def trigger_alarm_sync(self, alarm_id: str, price: float):
        """Déclenche une alarme"""
        asyncio.run_coroutine_threadsafe(
            self.send_message("trigger_alarm", {
                "alarm_id": alarm_id,
                "price": price
            }),
            asyncio.get_event_loop()
        )
    
    def create_page_sync(self, name: str):
        """Crée une page sur le serveur"""
        asyncio.run_coroutine_threadsafe(
            self.send_message("create_page", {
                "name": name
            }),
            asyncio.get_event_loop()
        )
    
    def share_page_sync(self, page_id: str, subject_type: str, subject_id: str,
                        can_view: bool = True, can_edit: bool = False):
        """Partage une page avec un utilisateur ou groupe"""
        asyncio.run_coroutine_threadsafe(
            self.send_message("share_page", {
                "page_id": page_id,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "can_view": can_view,
                "can_edit": can_edit
            }),
            asyncio.get_event_loop()
        )
