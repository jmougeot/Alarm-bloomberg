"""
Service WebSocket unifié pour la synchronisation avec le serveur
"""
import asyncio
import json
from typing import Optional, Dict, Any, List
from queue import Queue
import websockets
from PySide6.QtCore import QObject, Signal, QThread


class ServerService(QObject):
    """Service de communication WebSocket avec le serveur"""
    
    # Signaux de connexion
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    auth_required = Signal()
    
    # Signaux de synchronisation
    initial_state_received = Signal(dict)
    
    # Pages
    page_created = Signal(dict)
    page_updated = Signal(dict)
    page_deleted = Signal(str)
    
    # Strategies
    strategy_created = Signal(dict)
    strategy_updated = Signal(dict)
    strategy_deleted = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ws = None
        self.ws_url: Optional[str] = None
        self._running = False
        self._reconnect_delay = 5.0
        self._thread: Optional[QThread] = None
        self._message_queue = Queue()
        
    def start(self, ws_url: str):
        """Démarre la connexion WebSocket"""
        self.ws_url = ws_url
        self._running = True
        
        self._thread = QThread()
        self._thread.run = lambda: asyncio.run(self._run_forever())
        self._thread.start()
    
    def stop(self):
        """Arrête la connexion WebSocket"""
        self._running = False
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)
    
    async def _run_forever(self):
        """Boucle principale de connexion avec reconnexion automatique"""
        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                error_str = str(e)
                if "403" in error_str or "Forbidden" in error_str:
                    print(f"[Server] HTTP 403 - Authentication required")
                    self.error_occurred.emit("HTTP 403 - Session expirée")
                    self._running = False
                    self.auth_required.emit()
                    return
                else:
                    print(f"[Server] WebSocket error: {e}")
                    self.error_occurred.emit(str(e))
                
            if self._running:
                print(f"[Server] Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
    
    async def _connect_and_listen(self):
        """Connexion et écoute des messages"""
        if not self.ws_url:
            return
            
        async with websockets.connect(self.ws_url) as ws:
            self.ws = ws
            self.connected.emit()
            print("[Server] Connected")
            
            try:
                listen_task = asyncio.create_task(self._listen_messages(ws))
                send_task = asyncio.create_task(self._send_queued_messages(ws))
                await asyncio.gather(listen_task, send_task)
            except websockets.exceptions.ConnectionClosed:
                print("[Server] Connection closed")
            finally:
                self.ws = None
                self.disconnected.emit()
    
    async def _listen_messages(self, ws):
        """Écoute les messages du serveur"""
        async for message in ws:
            await self._handle_message(str(message))
    
    async def _send_queued_messages(self, ws):
        """Envoie les messages en file d'attente"""
        while self._running:
            if not self._message_queue.empty():
                message = self._message_queue.get_nowait()
                await ws.send(json.dumps(message))
                print(f"[Server] Sent: {message.get('type')}")
            else:
                await asyncio.sleep(0.1)
    
    async def _handle_message(self, message: str):
        """Traite un message reçu du serveur"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            payload = data.get("payload", {})
            
            if msg_type == "ping":
                if self.ws:
                    await self.ws.send(json.dumps({"type": "pong"}))
                return
            
            if msg_type == "initial_state":
                self.initial_state_received.emit(payload)
                
            elif msg_type == "page":
                action = payload.get("action")
                if action == "created":
                    self.page_created.emit(payload.get("data", {}))
                elif action == "updated":
                    self.page_updated.emit(payload.get("data", {}))
                elif action == "deleted":
                    self.page_deleted.emit(payload.get("id", ""))
                    
            elif msg_type == "strategy":
                action = payload.get("action")
                if action == "created":
                    self.strategy_created.emit(payload.get("data", {}))
                elif action == "updated":
                    self.strategy_updated.emit(payload.get("data", {}))
                elif action == "deleted":
                    self.strategy_deleted.emit(payload.get("id", ""))
                    
            elif msg_type == "error":
                self.error_occurred.emit(payload.get("message", "Unknown error"))
                
        except json.JSONDecodeError as e:
            print(f"[Server] JSON parse error: {e}")
    
    def _send(self, msg_type: str, payload: Dict[str, Any]):
        """Envoie un message via la file d'attente"""
        self._message_queue.put({"type": msg_type, "payload": payload})
    
    # === API Pages ===
    
    def create_page(self, name: str, page_id: Optional[str] = None):
        """Crée une page"""
        payload = {"name": name}
        if page_id:
            payload["id"] = page_id
        self._send("page.create", payload)
    
    def update_page(self, page_id: str, name: str):
        """Met à jour une page"""
        self._send("page.update", {"id": page_id, "name": name})
    
    def delete_page(self, page_id: str):
        """Supprime une page"""
        self._send("page.delete", {"id": page_id})
    
    # === API Strategies ===
    
    def create_strategy(self, page_id: str, strategy_data: Dict[str, Any]):
        """Crée une stratégie"""
        self._send("strategy.create", {"page_id": page_id, **strategy_data})
    
    def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]):
        """Met à jour une stratégie"""
        self._send("strategy.update", {"id": strategy_id, **strategy_data})
    
    def delete_strategy(self, strategy_id: str):
        """Supprime une stratégie"""
        self._send("strategy.delete", {"id": strategy_id})
