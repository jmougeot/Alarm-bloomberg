"""
Dialog pour créer et gérer des groupes
"""
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QGroupBox, QWidget
)
from PySide6.QtCore import Qt

from ..utils.async_worker import AsyncWorker
from ...services.api_service import GroupService


class GroupDialog(QDialog):
    """Dialog pour gérer les groupes"""
    
    def __init__(self, group_service: GroupService, parent=None):
        super().__init__(parent)
        self.group_service = group_service
        self.setWindowTitle("Gestion des groupes")
        self.setMinimumSize(700, 500)
        self._workers: List[AsyncWorker] = []
        self._current_group: Optional[Dict[str, Any]] = None
        
        self._setup_ui()
        self._load_groups()
    
    def closeEvent(self, event):
        """Nettoyer les workers"""
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
        self._workers.clear()
        event.accept()
    
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QHBoxLayout(self)
        
        # === Panneau gauche : Liste des groupes ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        groups_title = QLabel("Mes Groupes")
        groups_title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        left_layout.addWidget(groups_title)
        
        self.groups_list = QListWidget()
        self.groups_list.setMinimumWidth(200)
        self.groups_list.currentItemChanged.connect(self._on_group_selected)
        left_layout.addWidget(self.groups_list)
        
        groups_buttons = QHBoxLayout()
        
        create_btn = QPushButton("+ Créer")
        create_btn.clicked.connect(self._create_group)
        groups_buttons.addWidget(create_btn)
        
        delete_btn = QPushButton("Supprimer")
        delete_btn.clicked.connect(self._delete_group)
        groups_buttons.addWidget(delete_btn)
        
        left_layout.addLayout(groups_buttons)
        
        # === Panneau droit : Membres ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        self.group_info_label = QLabel("Sélectionnez un groupe")
        self.group_info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        right_layout.addWidget(self.group_info_label)
        
        members_group = QGroupBox("Membres")
        members_layout = QVBoxLayout(members_group)
        
        self.members_list = QListWidget()
        members_layout.addWidget(self.members_list)
        
        members_buttons = QHBoxLayout()
        
        self.add_member_btn = QPushButton("+ Ajouter")
        self.add_member_btn.clicked.connect(self._add_member)
        self.add_member_btn.setEnabled(False)
        members_buttons.addWidget(self.add_member_btn)
        
        self.remove_member_btn = QPushButton("Retirer")
        self.remove_member_btn.clicked.connect(self._remove_member)
        self.remove_member_btn.setEnabled(False)
        members_buttons.addWidget(self.remove_member_btn)
        
        members_buttons.addStretch()
        members_layout.addLayout(members_buttons)
        
        right_layout.addWidget(members_group)
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        right_layout.addLayout(close_layout)
        
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
    
    def _run_async(self, coro_func, on_success, on_error=None):
        """Exécute une coroutine"""
        worker = AsyncWorker(coro_func)
        worker.finished.connect(on_success)
        if on_error:
            worker.error.connect(on_error)
        else:
            worker.error.connect(lambda e: QMessageBox.warning(self, "Erreur", str(e)))
        worker.start()
        self._workers.append(worker)
    
    def _load_groups(self):
        """Charge la liste des groupes"""
        def on_success(groups):
            self.groups_list.clear()
            self._current_group = None
            self._update_members_panel()
            
            for group in groups:
                name = group.get('name', 'Sans nom')
                members = group.get('members', [])
                count = len(members) if isinstance(members, list) else 0
                
                item = QListWidgetItem(f"{name} ({count} membres)")
                item.setData(Qt.ItemDataRole.UserRole, group)
                self.groups_list.addItem(item)
        
        self._run_async(self.group_service.get_groups, on_success)
    
    def _on_group_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Groupe sélectionné"""
        if not current:
            self._current_group = None
            self._update_members_panel()
            return
        
        self._current_group = current.data(Qt.ItemDataRole.UserRole)
        self._update_members_panel()
        
        group_id = self._current_group.get('id')
        if group_id:
            self._load_group_details(group_id)
    
    def _load_group_details(self, group_id: str):
        """Charge les détails d'un groupe"""
        async def fetch():
            return await self.group_service.get_group(group_id)
        
        def on_success(group_data):
            if group_data and self._current_group and group_data.get('id') == self._current_group.get('id'):
                self._current_group = group_data
                current_item = self.groups_list.currentItem()
                if current_item:
                    members = group_data.get('members', [])
                    count = len(members) if isinstance(members, list) else 0
                    current_item.setText(f"{group_data.get('name', 'Sans nom')} ({count} membres)")
                    current_item.setData(Qt.ItemDataRole.UserRole, group_data)
                self._update_members_panel()
        
        self._run_async(fetch, on_success)
    
    def _update_members_panel(self):
        """Met à jour le panneau des membres"""
        self.members_list.clear()
        
        if not self._current_group:
            self.group_info_label.setText("Sélectionnez un groupe")
            self.add_member_btn.setEnabled(False)
            self.remove_member_btn.setEnabled(False)
            return
        
        name = self._current_group.get('name', 'Sans nom')
        self.group_info_label.setText(f"Groupe : {name}")
        self.add_member_btn.setEnabled(True)
        self.remove_member_btn.setEnabled(True)
        
        members = self._current_group.get('members', [])
        if not members:
            item = QListWidgetItem("(Aucun membre)")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(Qt.GlobalColor.gray)
            self.members_list.addItem(item)
            return
        
        for member in members:
            if isinstance(member, dict):
                username = member.get('username', 'Inconnu')
                user_id = member.get('id', '')
            else:
                username = str(member)
                user_id = str(member)
            
            item = QListWidgetItem(f"👤 {username}")
            item.setData(Qt.ItemDataRole.UserRole, {'id': user_id, 'username': username})
            self.members_list.addItem(item)
    
    def _create_group(self):
        """Crée un nouveau groupe"""
        name, ok = QInputDialog.getText(self, "Créer un groupe", "Nom du groupe:")
        
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        async def create():
            return await self.group_service.create_group(name)
        
        def on_success(result):
            if result:
                QMessageBox.information(self, "Succès", f"Groupe '{name}' créé")
                self._load_groups()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de créer le groupe")
        
        self._run_async(create, on_success)
    
    def _delete_group(self):
        """Supprime un groupe"""
        if not self._current_group:
            QMessageBox.warning(self, "Attention", "Sélectionnez un groupe")
            return
        
        name = self._current_group.get('name', 'ce groupe')
        reply = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer le groupe '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        group_id = self._current_group.get('id')
        
        async def delete():
            return await self.group_service.delete_group(group_id)
        
        def on_success(success):
            if success:
                QMessageBox.information(self, "Succès", "Groupe supprimé")
                self._load_groups()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer")
        
        self._run_async(delete, on_success)
    
    def _add_member(self):
        """Ajoute un membre"""
        if not self._current_group:
            return
        
        username, ok = QInputDialog.getText(self, "Ajouter un membre", "Nom d'utilisateur:")
        
        if not ok or not username.strip():
            return
        
        username = username.strip()
        group_id = self._current_group.get('id')
        
        async def add():
            # Rechercher l'utilisateur
            user = await self.group_service.search_user(username)
            if not user:
                return False, f"Utilisateur '{username}' introuvable"
            
            # Ajouter au groupe
            success = await self.group_service.add_member(group_id, user['id'])
            if success:
                return True, None
            return False, "Impossible d'ajouter le membre"
        
        def on_success(result):
            success, error = result
            if success:
                QMessageBox.information(self, "Succès", f"'{username}' ajouté")
                self._load_group_details(group_id)
            else:
                QMessageBox.warning(self, "Erreur", error or "Erreur inconnue")
        
        self._run_async(add, on_success)
    
    def _remove_member(self):
        """Retire un membre"""
        if not self._current_group:
            return
        
        current_item = self.members_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attention", "Sélectionnez un membre")
            return
        
        member_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not member_data:
            return
        
        member_id = member_data.get('id')
        member_name = member_data.get('username', 'ce membre')
        group_id = self._current_group.get('id')
        
        reply = QMessageBox.question(
            self, "Confirmer",
            f"Retirer '{member_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        async def remove():
            return await self.group_service.remove_member(group_id, member_id)
        
        def on_success(success):
            if success:
                QMessageBox.information(self, "Succès", f"'{member_name}' retiré")
                self._load_group_details(group_id)
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de retirer")
        
        self._run_async(remove, on_success)
