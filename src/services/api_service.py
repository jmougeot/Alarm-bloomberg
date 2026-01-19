"""
Service HTTP pour les opérations sur les pages et permissions
"""
import httpx
from typing import Optional, Dict, Any, List, Callable


class PageService:
    """Service pour les opérations REST sur les pages"""
    
    def __init__(self, server_url: str, get_token: Callable[[], Optional[str]]):
        self.server_url = server_url.rstrip('/')
        self._get_token = get_token
    
    def _headers(self) -> Dict[str, str]:
        """Headers avec token d'authentification"""
        return {"Authorization": f"Bearer {self._get_token()}"}
    
    # === Pages ===
    
    async def get_pages(self) -> List[Dict[str, Any]]:
        """Récupère toutes les pages accessibles"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/pages",
                headers=self._headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return []
    
    async def create_page(self, name: str, page_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Crée une nouvelle page"""
        payload = {"name": name}
        if page_id:
            payload["id"] = page_id
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/pages",
                headers=self._headers(),
                json=payload,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def update_page(self, page_id: str, name: str) -> bool:
        """Met à jour une page"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.server_url}/pages/{page_id}",
                headers=self._headers(),
                json={"name": name},
                timeout=10.0
            )
            return response.status_code == 200
    
    async def delete_page(self, page_id: str) -> bool:
        """Supprime une page"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.server_url}/pages/{page_id}",
                headers=self._headers(),
                timeout=10.0
            )
            return response.status_code == 200
    
    # === Permissions ===
    
    async def get_permissions(self, page_id: str) -> List[Dict[str, Any]]:
        """Récupère les permissions d'une page"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/pages/{page_id}/permissions",
                headers=self._headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return []
    
    async def add_permission(
        self, 
        page_id: str, 
        subject_type: str, 
        subject_id: str,
        can_view: bool = True,
        can_edit: bool = False
    ) -> bool:
        """Ajoute une permission"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/pages/{page_id}/permissions",
                headers=self._headers(),
                json={
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "can_view": can_view,
                    "can_edit": can_edit
                },
                timeout=10.0
            )
            return response.status_code == 200
    
    async def remove_permission(self, page_id: str, permission_id: str) -> bool:
        """Supprime une permission"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.server_url}/pages/{page_id}/permissions/{permission_id}",
                headers=self._headers(),
                timeout=10.0
            )
            return response.status_code == 200


class GroupService:
    """Service pour les opérations REST sur les groupes"""
    
    def __init__(self, server_url: str, get_token: Callable[[], Optional[str]]):
        self.server_url = server_url.rstrip('/')
        self._get_token = get_token
    
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}
    
    async def get_groups(self) -> List[Dict[str, Any]]:
        """Récupère tous les groupes de l'utilisateur"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/groups",
                headers=self._headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return []
    
    async def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un groupe par ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/groups/{group_id}",
                headers=self._headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def create_group(self, name: str) -> Optional[Dict[str, Any]]:
        """Crée un groupe"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/groups",
                headers=self._headers(),
                json={"name": name},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def delete_group(self, group_id: str) -> bool:
        """Supprime un groupe"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.server_url}/groups/{group_id}",
                headers=self._headers(),
                timeout=10.0
            )
            return response.status_code == 200
    
    async def add_member(self, group_id: str, user_id: str) -> bool:
        """Ajoute un membre au groupe"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/groups/{group_id}/members/{user_id}",
                headers=self._headers(),
                timeout=10.0
            )
            return response.status_code == 200
    
    async def remove_member(self, group_id: str, user_id: str) -> bool:
        """Retire un membre du groupe"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.server_url}/groups/{group_id}/members/{user_id}",
                headers=self._headers(),
                timeout=10.0
            )
            return response.status_code == 200
    
    async def search_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Recherche un utilisateur par nom"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/users/search",
                params={"username": username},
                headers=self._headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def search_group(self, name: str) -> Optional[Dict[str, Any]]:
        """Recherche un groupe par nom"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/groups/search",
                params={"name": name},
                headers=self._headers(),
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
