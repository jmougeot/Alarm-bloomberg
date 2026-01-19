"""
Service d'authentification avec le serveur d'alarmes
"""
import httpx
from typing import Optional, Dict, Any
from pathlib import Path
import json


class AuthService:
    """Gère l'authentification avec le serveur"""
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url.rstrip('/')
        self.token: Optional[str] = None
        self.user_info: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None  # Dernier message d'erreur
        self._token_file = Path.home() / ".bloomberg_alarm" / "auth_token.json"
        
    async def login(self, username: str, password: str) -> bool:
        """
        Connexion au serveur
        Returns: True si succès, False sinon
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/login",
                    data={"username": username, "password": password},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    
                    # Récupérer les infos utilisateur
                    await self._fetch_user_info()
                    
                    # Sauvegarder le token
                    self._save_token()
                    
                    return True
                else:
                    print(f"Login failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    async def register(self, username: str, password: str) -> bool:
        """
        Créer un nouveau compte
        Returns: True si succès, False sinon
        """
        self.last_error = None
        try:
            payload = {"username": username, "password": password}
            print(f"[DEBUG] Sending register request to {self.server_url}/register with payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/register",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                print(f"[DEBUG] Register response: status={response.status_code}, body={response.text}")
                
                if response.status_code == 200:
                    # Auto-login après inscription
                    return await self.login(username, password)
                else:
                    # Parser le message d'erreur du serveur
                    try:
                        error_data = response.json()
                        detail = error_data.get("detail", "")
                        if "already registered" in detail.lower():
                            self.last_error = "Ce nom d'utilisateur existe déjà. Utilisez l'onglet Connexion."
                        else:
                            self.last_error = detail or f"Erreur d'inscription ({response.status_code})"
                    except:
                        self.last_error = f"Erreur d'inscription ({response.status_code})"
                    print(f"Register failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.last_error = f"Erreur de connexion au serveur: {e}"
            print(f"Register error: {e}")
            return False
    
    async def _fetch_user_info(self):
        """Récupère les infos de l'utilisateur connecté"""
        if not self.token:
            return
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.server_url}/me",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.user_info = response.json()
                    
        except Exception as e:
            print(f"Fetch user info error: {e}")
    
    def _save_token(self):
        """Sauvegarde le token localement"""
        if not self.token:
            return
            
        try:
            self._token_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "token": self.token,
                "user_info": self.user_info
            }
            
            with open(self._token_file, 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            print(f"Save token error: {e}")
    
    def load_saved_token(self) -> bool:
        """
        Charge le token sauvegardé
        Returns: True si un token valide a été chargé
        """
        try:
            if not self._token_file.exists():
                return False
                
            with open(self._token_file, 'r') as f:
                data = json.load(f)
                
            self.token = data.get("token")
            self.user_info = data.get("user_info")
            
            return self.token is not None
            
        except Exception as e:
            print(f"Load token error: {e}")
            return False
    
    def logout(self):
        """Déconnexion"""
        self.token = None
        self.user_info = None
        
        # Supprimer le token sauvegardé
        try:
            if self._token_file.exists():
                self._token_file.unlink()
        except Exception as e:
            print(f"Logout error: {e}")
    
    def is_authenticated(self) -> bool:
        """Vérifie si l'utilisateur est authentifié"""
        return self.token is not None
    
    def get_ws_url(self) -> str:
        """Retourne l'URL WebSocket avec le token"""
        if not self.token:
            raise ValueError("Not authenticated")
            
        # Convertir http:// en ws:// et https:// en wss://
        ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{ws_url}/ws?token={self.token}"
