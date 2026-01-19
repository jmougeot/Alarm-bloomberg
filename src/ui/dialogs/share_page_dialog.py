"""
Dialog pour partager une page avec des utilisateurs ou des groupes
"""
from typing import List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt

from ..utils.async_worker import AsyncWorker
from ...services.api_service import PageService, GroupService


class SharePageDialog(QDialog):
    """Dialog pour partager une page"""
    
    def __init__(self, page_service: PageService, group_service: GroupService, 
                 page_id: str, page_name: str, parent=None):
        super().__init__(parent)
        self.page_service = page_service
        self.group_service = group_service
        self.page_id = page_id
        self.setWindowTitle(f"Partager: {page_name}")
        self.setMinimumSize(500, 400)
        self._workers: List[AsyncWorker] = []
        
        self._setup_ui()
        self._load_permissions()
    
    def closeEvent(self, event):
        """Nettoyer les workers"""
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
        event.accept()
    
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        title = QLabel("Permissions de la page")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Section ajout
        add_section = QVBoxLayout()
        add_label = QLabel("Ajouter une permission:")
        add_section.addWidget(add_label)
        
        add_layout = QHBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Utilisateur", "Groupe"])
        add_layout.addWidget(self.type_combo)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom d'utilisateur ou de groupe")
        add_layout.addWidget(self.name_input)
        
        self.can_view_check = QCheckBox("Voir")
        self.can_view_check.setChecked(True)
        add_layout.addWidget(self.can_view_check)
        
        self.can_edit_check = QCheckBox("Éditer")
        add_layout.addWidget(self.can_edit_check)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(self._add_permission)
        add_layout.addWidget(add_btn)
        
        add_section.addLayout(add_layout)
        layout.addLayout(add_section)
        
        # Liste des permissions
        permissions_label = QLabel("Permissions actuelles:")
        layout.addWidget(permissions_label)
        
        self.permissions_list = QListWidget()
        layout.addWidget(self.permissions_list)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Retirer")
        remove_btn.clicked.connect(self._remove_permission)
        buttons_layout.addWidget(remove_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
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
    
    def _load_permissions(self):
        """Charge les permissions"""
        async def load():
            return await self.page_service.get_permissions(self.page_id)
        
        def on_success(permissions):
            self.permissions_list.clear()
            
            for perm in permissions:
                subject_type = perm.get('subject_type', 'user')
                subject_name = perm.get('subject_name', 'Inconnu')
                can_view = "✓ Voir" if perm.get('can_view') else ""
                can_edit = "✓ Éditer" if perm.get('can_edit') else ""
                
                icon = "👤" if subject_type == "user" else "👥"
                text = f"{icon} {subject_name}: {can_view} {can_edit}"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, perm)
                self.permissions_list.addItem(item)
        
        self._run_async(load, on_success)
    
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
            # Rechercher le sujet
            if subject_type == "user":
                subject = await self.group_service.search_user(name)
            else:
                subject = await self.group_service.search_group(name)
            
            if not subject:
                return False, f"{subject_type.capitalize()} '{name}' introuvable"
            
            # Ajouter la permission
            success = await self.page_service.add_permission(
                self.page_id, subject_type, subject['id'], can_view, can_edit
            )
            
            if success:
                return True, None
            return False, "Impossible d'ajouter la permission"
        
        def on_success(result):
            success, error = result
            if error:
                QMessageBox.warning(self, "Erreur", error)
            elif success:
                self._load_permissions()
                self.name_input.clear()
                QMessageBox.information(self, "Succès", "Permission ajoutée")
        
        self._run_async(add, on_success)
    
    def _remove_permission(self):
        """Retire une permission"""
        item = self.permissions_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Attention", "Sélectionnez une permission")
            return
        
        perm = item.data(Qt.ItemDataRole.UserRole)
        if not perm:
            return
        
        async def remove():
            return await self.page_service.remove_permission(self.page_id, perm['id'])
        
        def on_success(success):
            if success:
                self._load_permissions()
                QMessageBox.information(self, "Succès", "Permission retirée")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de retirer")
        
        self._run_async(remove, on_success)
