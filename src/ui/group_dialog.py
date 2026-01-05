"""
Dialog pour créer et gérer des groupes
"""
from typing import Optional
import asyncio

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, QObject
import httpx

from .async_worker import AsyncWorker


class GroupDialog(QDialog):
    """Dialog pour gérer les groupes"""
    
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setWindowTitle("Gestion des groupes")
        self.setMinimumSize(500, 400)
        self._workers = []  # Liste des workers pour le nettoyage
        
        self._setup_ui()
        self._load_groups()
    
    def closeEvent(self, event):
        """Nettoyer les workers avant de fermer"""
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
        event.accept()
    
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Mes Groupes")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Liste des groupes
        self.groups_list = QListWidget()
        self.groups_list.itemDoubleClicked.connect(self._manage_group_members)
        layout.addWidget(self.groups_list)
        
        # Boutons d'actions
        buttons_layout = QHBoxLayout()
        
        create_btn = QPushButton("Créer un groupe")
        create_btn.clicked.connect(self._create_group)
        buttons_layout.addWidget(create_btn)
        
        manage_btn = QPushButton("Gérer les membres")
        manage_btn.clicked.connect(lambda: self._manage_group_members(self.groups_list.currentItem()))
        buttons_layout.addWidget(manage_btn)
        
        delete_btn = QPushButton("Supprimer")
        delete_btn.clicked.connect(self._delete_group)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_groups(self):
        """Charge la liste des groupes"""
        async def load():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service.server_url}/groups",
                    headers={"Authorization": f"Bearer {self.auth_service.token}"},
                    timeout=10.0
                )
                return response
        
        def on_finished(response):
            try:
                if response.status_code == 200:
                    groups = response.json()
                    self.groups_list.clear()
                    
                    for group in groups:
                        item = QListWidgetItem(f"{group['name']} ({len(group.get('members', []))} membres)")
                        item.setData(Qt.ItemDataRole.UserRole, group)
                        self.groups_list.addItem(item)
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de charger les groupes")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur: {str(e)}")
        
        def on_error(error_msg):
            QMessageBox.warning(self, "Erreur", f"Erreur de connexion: {error_msg}")
        
        worker = AsyncWorker(load)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
        
        # Garder une référence pour éviter le garbage collection
        self._workers.append(worker)
    
    def _create_group(self):
        """Crée un nouveau groupe"""
        name, ok = QInputDialog.getText(
            self,
            "Créer un groupe",
            "Nom du groupe:"
        )
        
        if ok and name:
            async def create():
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.auth_service.server_url}/groups",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        json={"name": name},
                        timeout=10.0
                    )
                    return response
            
            def on_finished(response):
                if response.status_code == 200:
                    self._load_groups()
                    QMessageBox.information(self, "Succès", f"Groupe '{name}' créé")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de créer le groupe")
            
            def on_error(error_msg):
                QMessageBox.warning(self, "Erreur", f"Erreur: {error_msg}")
            
            worker = AsyncWorker(create)
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            worker.start()
            self._workers.append(worker)
    
    def _manage_group_members(self, item: Optional[QListWidgetItem]):
        """Gère les membres d'un groupe"""
        if not item:
            return
        
        group = item.data(Qt.ItemDataRole.UserRole)
        dialog = GroupMembersDialog(self.auth_service, group, self)
        if dialog.exec():
            self._load_groups()
    
    def _delete_group(self):
        """Supprime un groupe"""
        item = self.groups_list.currentItem()
        if not item:
            return
        
        group = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmer",
            f"Supprimer le groupe '{group['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            async def delete():
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        f"{self.auth_service.server_url}/groups/{group['id']}",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        timeout=10.0
                    )
                    return response
            
            def on_finished(response):
                if response.status_code == 200:
                    self._load_groups()
                    QMessageBox.information(self, "Succès", "Groupe supprimé")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de supprimer le groupe")
            
            def on_error(error_msg):
                QMessageBox.warning(self, "Erreur", f"Erreur: {error_msg}")
            
            worker = AsyncWorker(delete)
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            worker.start()
            self._workers.append(worker)


class GroupMembersDialog(QDialog):
    """Dialog pour gérer les membres d'un groupe"""
    
    def __init__(self, auth_service, group, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.group = group
        self.setWindowTitle(f"Membres de {group['name']}")
        self.setMinimumSize(400, 300)
        self._workers = []
        
        self._setup_ui()
        self._load_members()
    
    def closeEvent(self, event):
        """Nettoyer les workers avant de fermer"""
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
        event.accept()
    
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Liste des membres
        self.members_list = QListWidget()
        layout.addWidget(self.members_list)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ajouter un membre")
        add_btn.clicked.connect(self._add_member)
        buttons_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Retirer")
        remove_btn.clicked.connect(self._remove_member)
        buttons_layout.addWidget(remove_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_members(self):
        """Charge les membres du groupe"""
        self.members_list.clear()
        for member in self.group.get('members', []):
            item = QListWidgetItem(member.get('username', 'Unknown'))
            item.setData(Qt.ItemDataRole.UserRole, member)
            self.members_list.addItem(item)
    
    def _add_member(self):
        """Ajoute un membre au groupe"""
        username, ok = QInputDialog.getText(
            self,
            "Ajouter un membre",
            "Nom d'utilisateur:"
        )
        
        if ok and username:
            async def add():
                # D'abord, récupérer l'ID de l'utilisateur
                async with httpx.AsyncClient() as client:
                    # Recherche de l'utilisateur
                    response = await client.get(
                        f"{self.auth_service.server_url}/users/search?username={username}",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        timeout=10.0
                    )
                    
                    if response.status_code != 200:
                        return None, f"Utilisateur '{username}' introuvable"
                    
                    user = response.json()
                    user_id = user['id']
                    
                    # Ajouter au groupe
                    response = await client.post(
                        f"{self.auth_service.server_url}/groups/{self.group['id']}/members/{user_id}",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        timeout=10.0
                    )
                    
                    if response.status_code != 200:
                        return None, "Impossible d'ajouter le membre"
                    
                    # Recharger les données du groupe
                    response = await client.get(
                        f"{self.auth_service.server_url}/groups/{self.group['id']}",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        return response.json(), None
                    return None, None
            
            def on_finished(result):
                group_data, error = result
                if error:
                    QMessageBox.warning(self, "Erreur", error)
                elif group_data:
                    self.group = group_data
                    self._load_members()
                    QMessageBox.information(self, "Succès", f"Membre '{username}' ajouté")
            
            def on_error(error_msg):
                QMessageBox.warning(self, "Erreur", f"Erreur: {error_msg}")
            
            worker = AsyncWorker(add)
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            worker.start()
            self._workers.append(worker)
    
    def _remove_member(self):
        """Retire un membre du groupe"""
        item = self.members_list.currentItem()
        if not item:
            return
        
        member = item.data(Qt.ItemDataRole.UserRole)
        
        async def remove():
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.auth_service.server_url}/groups/{self.group['id']}/members/{member['id']}",
                    headers={"Authorization": f"Bearer {self.auth_service.token}"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None, "Impossible de retirer le membre"
                
                # Recharger les données du groupe
                response = await client.get(
                    f"{self.auth_service.server_url}/groups/{self.group['id']}",
                    headers={"Authorization": f"Bearer {self.auth_service.token}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json(), None
                return None, None
        
        def on_finished(result):
            group_data, error = result
            if error:
                QMessageBox.warning(self, "Erreur", error)
            elif group_data:
                self.group = group_data
                self._load_members()
                QMessageBox.information(self, "Succès", "Membre retiré")
        
        def on_error(error_msg):
            QMessageBox.warning(self, "Erreur", f"Erreur: {error_msg}")
        
        worker = AsyncWorker(remove)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
        self._workers.append(worker)
