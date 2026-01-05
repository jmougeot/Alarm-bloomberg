"""
Dialog pour partager une page avec des utilisateurs ou des groupes
"""
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt, QObject
import httpx

from .async_worker import AsyncWorker


class SharePageDialog(QDialog):
    """Dialog pour partager une page"""
    
    def __init__(self, auth_service, page_id: str, page_name: str, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.page_id = page_id
        self.setWindowTitle(f"Partager: {page_name}")
        self.setMinimumSize(500, 400)
        self._workers = []
        
        self._setup_ui()
        self._load_permissions()
    
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
        title = QLabel("Permissions de la page")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Section ajout de permission
        add_section = QVBoxLayout()
        
        add_label = QLabel("Ajouter une permission:")
        add_section.addWidget(add_label)
        
        add_layout = QHBoxLayout()
        
        # Type (user ou group)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Utilisateur", "Groupe"])
        add_layout.addWidget(self.type_combo)
        
        # Nom
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom d'utilisateur ou de groupe")
        add_layout.addWidget(self.name_input)
        
        # Permissions
        self.can_view_check = QCheckBox("Voir")
        self.can_view_check.setChecked(True)
        add_layout.addWidget(self.can_view_check)
        
        self.can_edit_check = QCheckBox("Éditer")
        add_layout.addWidget(self.can_edit_check)
        
        # Bouton ajouter
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(self._add_permission)
        add_layout.addWidget(add_btn)
        
        add_section.addLayout(add_layout)
        layout.addLayout(add_section)
        
        # Liste des permissions existantes
        permissions_label = QLabel("Permissions actuelles:")
        layout.addWidget(permissions_label)
        
        self.permissions_list = QListWidget()
        layout.addWidget(self.permissions_list)
        
        # Boutons d'actions
        buttons_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Retirer")
        remove_btn.clicked.connect(self._remove_permission)
        buttons_layout.addWidget(remove_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_permissions(self):
        """Charge les permissions existantes"""
        async def load():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service.server_url}/pages/{self.page_id}/permissions",
                    headers={"Authorization": f"Bearer {self.auth_service.token}"},
                    timeout=10.0
                )
                return response
        
        def on_finished(response):
            try:
                if response.status_code == 200:
                    permissions = response.json()
                    self.permissions_list.clear()
                    
                    for perm in permissions:
                        subject_type = perm['subject_type']
                        subject_name = perm.get('subject_name', 'Unknown')
                        can_view = "✓ Voir" if perm['can_view'] else ""
                        can_edit = "✓ Éditer" if perm['can_edit'] else ""
                        
                        type_icon = "👤" if subject_type == "user" else "👥"
                        text = f"{type_icon} {subject_name}: {can_view} {can_edit}"
                        
                        item = QListWidgetItem(text)
                        item.setData(Qt.ItemDataRole.UserRole, perm)
                        self.permissions_list.addItem(item)
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de charger les permissions")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur: {str(e)}")
        
        def on_error(error_msg):
            QMessageBox.warning(self, "Erreur", f"Erreur de connexion: {error_msg}")
        
        worker = AsyncWorker(load)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
        self._workers.append(worker)
    
    def _add_permission(self):
        """Ajoute une permission"""
        subject_type = "user" if self.type_combo.currentText() == "Utilisateur" else "group"
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom")
            return
        
        can_view = self.can_view_check.isChecked()
        can_edit = self.can_edit_check.isChecked()
        
        if not can_view and not can_edit:
            QMessageBox.warning(self, "Erreur", "Sélectionnez au moins une permission")
            return
        
        async def add():
            async with httpx.AsyncClient() as client:
                # D'abord, trouver l'ID
                if subject_type == "user":
                    response = await client.get(
                        f"{self.auth_service.server_url}/users/search?username={name}",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        timeout=10.0
                    )
                else:
                    response = await client.get(
                        f"{self.auth_service.server_url}/groups/search?name={name}",
                        headers={"Authorization": f"Bearer {self.auth_service.token}"},
                        timeout=10.0
                    )
                
                if response.status_code != 200:
                    return False, f"{subject_type.capitalize()} '{name}' introuvable"
                
                subject = response.json()
                subject_id = subject['id']
                
                # Ajouter la permission
                response = await client.post(
                    f"{self.auth_service.server_url}/pages/{self.page_id}/permissions",
                    headers={"Authorization": f"Bearer {self.auth_service.token}"},
                    json={
                        "subject_type": subject_type,
                        "subject_id": subject_id,
                        "can_view": can_view,
                        "can_edit": can_edit
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True, None
                return False, "Impossible d'ajouter la permission"
        
        def on_finished(result):
            success, error = result
            if error:
                QMessageBox.warning(self, "Erreur", error)
            elif success:
                self._load_permissions()
                self.name_input.clear()
                QMessageBox.information(self, "Succès", "Permission ajoutée")
        
        def on_error(error_msg):
            QMessageBox.warning(self, "Erreur", f"Erreur: {error_msg}")
        
        worker = AsyncWorker(add)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
        self._workers.append(worker)
    
    def _remove_permission(self):
        """Retire une permission"""
        item = self.permissions_list.currentItem()
        if not item:
            return
        
        perm = item.data(Qt.ItemDataRole.UserRole) 
        
        async def remove():
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.auth_service.server_url}/pages/{self.page_id}/permissions/{perm['id']}",
                    headers={"Authorization": f"Bearer {self.auth_service.token}"},
                    timeout=10.0
                )
                return response.status_code == 200
        
        def on_finished(success):
            if success:
                self._load_permissions()
                QMessageBox.information(self, "Succès", "Permission retirée")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de retirer la permission")
        
        def on_error(error_msg):
            QMessageBox.warning(self, "Erreur", f"Erreur: {error_msg}")
        
        worker = AsyncWorker(remove)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
        self._workers.append(worker)
