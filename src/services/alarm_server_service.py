"""
Service WebSocket pour la synchronisation avec le serveur d'alarmes
"""
import asyncio
import json
from typing import Optional, Dict, Any
from queue import Queue
import websockets
from PySide6.QtCore import QObject, Signal, QThread


class AlarmServerService(QObject):
    """Service de communication WebSocket avec le serveur d'alarmes"""
    
    # Signaux Qt
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    auth_required = Signal()  # Émis quand une ré-authentification est nécessaire (HTTP 403)
    
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
        self.ws = None
        self.ws_url: Optional[str] = None
        self._running = False
        self._reconnect_delay = 5.0
        self._thread: Optional[QThread] = None
        self._message_queue = Queue()  # File de messages à envoyer
        
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
            self._thread.wait(2000)  # Attendre maximum 2 secondes
    
    async def _run_forever(self):
        """Boucle principale de connexion avec reconnexion automatique"""
        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                error_str = str(e)
                # HTTP 403 = non autorisé, demander une ré-authentification
                if "403" in error_str or "Forbidden" in error_str:
                    print(f"[Server] Error: server rejected WebSocket connection: HTTP 403")
                    self.error_occurred.emit("server rejected WebSocket connection: HTTP 403")
                    self._running = False  # Arrêter les tentatives de reconnexion
                    self.auth_required.emit()  # Demander la ré-authentification
                    return
                else:
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
                # Tâche pour écouter les messages
                listen_task = asyncio.create_task(self._listen_messages(ws))
                # Tâche pour envoyer les messages en file
                send_task = asyncio.create_task(self._send_queued_messages(ws))
                
                await asyncio.gather(listen_task, send_task)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
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
            try:
                # Vérifier s'il y a des messages à envoyer
                if not self._message_queue.empty():
                    message = self._message_queue.get_nowait()
                    await ws.send(json.dumps(message))
                    print(f"[Server] Message sent: {message.get('type')}")
                else:
                    # Attendre un peu avant de revérifier
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Send error: {e}")
    
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
    
    def send_message_sync(self, msg_type: str, payload: Dict[str, Any]):
        """Envoie un message de manière synchrone (pour Qt)"""
        message = {
            "type": msg_type,
            "payload": payload
        }
        self._message_queue.put(message)
        print(f"[Server] Message queued: {msg_type}", flush=True)
    
    # === Méthodes de synchronisation ===
    
    def create_page(self, name: str, page_id: str = None):
        """Crée une page sur le serveur"""
        print(f"[Server] Creating page: {name} (id={page_id})", flush=True)
        payload = {"name": name}
        if page_id:
            payload["id"] = page_id
        self.send_message_sync("create_page", payload)
    
    def create_alarm(self, page_id: str, alarm_data: Dict[str, Any]):
        """Crée une alarme sur le serveur"""
        print(f"[Server] Creating alarm: {alarm_data.get('strategy_name', 'Unknown')} - {alarm_data.get('ticker', 'Unknown')}", flush=True)
        payload = {
            "page_id": page_id,
            **alarm_data
        }
        self.send_message_sync("create_alarm", payload)
    
    def update_alarm(self, alarm_id: str, alarm_data: Dict[str, Any]):
        """Met à jour une alarme"""
        payload = {
            "alarm_id": alarm_id,
            **alarm_data
        }
        self.send_message_sync("update_alarm", payload)
    
    def delete_alarm(self, alarm_id: str = None, strategy_id: str = None):
        """Supprime une alarme (par alarm_id ou strategy_id)"""
        if strategy_id:
            print(f"[Server] Deleting alarms for strategy: {strategy_id}", flush=True)
            self.send_message_sync("delete_alarm", {"strategy_id": strategy_id})
        elif alarm_id:
            print(f"[Server] Deleting alarm: {alarm_id}", flush=True)
            self.send_message_sync("delete_alarm", {"alarm_id": alarm_id})
    
    def update_page(self, page_id: str, name: str):
        """Met à jour une page sur le serveur"""
        print(f"[Server] Updating page: {page_id} -> {name}", flush=True)
        self.send_message_sync("update_page", {"page_id": page_id, "name": name})
    
    def delete_page(self, page_id: str):
        """Supprime une page sur le serveur"""
        print(f"[Server] Deleting page: {page_id}", flush=True)
        self.send_message_sync("delete_page", {"page_id": page_id})
    
    def trigger_alarm(self, alarm_id: str, price: float):
        """Déclenche une alarme"""
        self.send_message_sync("trigger_alarm", {"alarm_id": alarm_id, "price": price})
