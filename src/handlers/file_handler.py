"""
Gestion des fichiers (ouvrir, sauvegarder, nouveau workspace)
Supporte le nouveau format dossier (un JSON par page) et l'ancien format fichier unique
"""
import json
import re
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..services.settings_service import SettingsService

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


def sanitize_filename(name: str) -> str:
    """Nettoie un nom pour en faire un nom de fichier valide"""
    # Remplacer les caractères non autorisés
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Supprimer les espaces multiples
    name = re.sub(r'\s+', ' ', name).strip()
    return name if name else 'page'


class FileHandler:
    """Gère les opérations sur les fichiers"""
    
    WORKSPACE_META_FILE = "_workspace.json"
    PAGE_PREFIX = "page_"
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
        self.settings = SettingsService()
    
    def auto_load_last_workspace(self) -> bool:
        """Charge automatiquement le dernier workspace au démarrage
        Retourne True si un workspace a été chargé"""
        last_workspace = self.settings.get_last_workspace()
        
        if last_workspace and Path(last_workspace).exists():
            try:
                if Path(last_workspace).is_dir():
                    self._load_workspace_folder(last_workspace)
                else:
                    self._load_legacy_file(last_workspace)
                return True
            except Exception as e:
                print(f"Erreur chargement auto workspace: {e}")
                self.settings.clear_last_workspace()
        
        return False
    
    def new_workspace(self):
        """Crée un nouveau workspace"""
        if self.window.strategies:
            reply = QMessageBox.question(
                self.window,
                "Nouveau workspace",
                "Voulez-vous sauvegarder avant de créer un nouveau workspace?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel  # type: ignore
            )
            
            if reply == QMessageBox.Save:  # type: ignore
                self.save_file()
            elif reply == QMessageBox.Cancel:  # type: ignore
                return
        
        # Supprimer toutes les pages
        from ..models.page import Page
        for page_id in list(self.window.pages.keys()):
            self.window._remove_page(page_id)
            self.window.sidebar.remove_page(page_id)
        
        # Créer une page par défaut
        self.window._create_default_page()
        
        self.window.current_file = None
        self.window.setWindowTitle("Strategy Price Monitor")
        self.window.statusbar.showMessage("Nouveau workspace créé", 3000)
    
    def open_file(self):
        """Ouvre un dossier workspace ou un fichier legacy"""
        # D'abord essayer d'ouvrir un dossier workspace
        folder_path = QFileDialog.getExistingDirectory(
            self.window,
            "Ouvrir un dossier Workspace",
            "",
            QFileDialog.ShowDirsOnly  # type: ignore
        )
        
        if folder_path:
            self._open_workspace_folder(folder_path)
            return
        
        # Si annulé, proposer d'ouvrir un fichier legacy
        reply = QMessageBox.question(
            self.window,
            "Ouvrir un fichier",
            "Voulez-vous ouvrir un ancien fichier JSON à la place?",
            QMessageBox.Yes | QMessageBox.No  # type: ignore
        )
        
        if reply == QMessageBox.Yes:  # type: ignore
            self._open_legacy_file()
    
    def open_legacy_file(self):
        """Ouvre un ancien fichier JSON (pour menu)"""
        self._open_legacy_file()
    
    def _open_legacy_file(self):
        """Ouvre un fichier JSON legacy"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Ouvrir un fichier JSON",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self._load_legacy_file(file_path)
            except Exception as e:
                QMessageBox.critical(
                    self.window,
                    "Erreur",
                    f"Impossible de charger le fichier:\n{str(e)}"
                )
    
    def _load_legacy_file(self, file_path: str):
        """Charge un fichier JSON legacy"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.window.load_from_dict(data)
        
        self.window.current_file = file_path
        self.window.setWindowTitle(f"Strategy Price Monitor - {Path(file_path).name}")
        self.window.statusbar.showMessage(f"Fichier chargé: {file_path}", 3000)
        
        self.settings.set_last_workspace(file_path)
        self.settings.add_recent_workspace(file_path)
    
    def _open_workspace_folder(self, folder_path: str):
        """Ouvre un dossier workspace"""
        try:
            self._load_workspace_folder(folder_path)
        except Exception as e:
            QMessageBox.critical(
                self.window,
                "Erreur",
                f"Impossible de charger le workspace:\n{str(e)}"
            )
    
    def _load_workspace_folder(self, folder_path: str):
        """Charge un workspace depuis un dossier"""
        folder = Path(folder_path)
        
        # Supprimer toutes les pages existantes
        for page_id in list(self.window.pages.keys()):
            self.window._remove_page(page_id)
            self.window.sidebar.remove_page(page_id)
        
        # Charger les métadonnées du workspace
        meta_file = folder / self.WORKSPACE_META_FILE
        pages_order = {}
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                pages_order = {p['id']: p.get('order', i) for i, p in enumerate(meta.get('pages_order', []))}
        
        # Charger toutes les pages
        pages_loaded = []
        for json_file in folder.glob(f"{self.PAGE_PREFIX}*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                page_data = json.load(f)
            
            page_id = page_data['page']['id']
            order = pages_order.get(page_id, 999)
            pages_loaded.append((order, page_data))
        
        # Trier par ordre
        pages_loaded.sort(key=lambda x: x[0])
        
        # Ajouter les pages
        from ..models.page import Page
        from ..models.strategy import Strategy
        
        for i, (_, page_data) in enumerate(pages_loaded):
            page = Page.from_dict(page_data['page'])
            self.window._add_page(page, select=(i == 0))
            
            page_widget = self.window.pages[page.id]
            for strategy_data in page_data.get('strategies', []):
                strategy = Strategy.from_dict(strategy_data)
                page_widget.add_strategy(strategy)
        
        # Si aucune page, créer une page par défaut
        if not pages_loaded:
            self.window._create_default_page()
        
        self.window.current_file = folder_path
        self.window.setWindowTitle(f"Strategy Price Monitor - {folder.name}")
        self.window.statusbar.showMessage(f"Workspace chargé: {folder_path}", 3000)
        
        # Sauvegarder dans les settings
        self.settings.set_last_workspace(folder_path)
        self.settings.add_recent_workspace(folder_path)
        
        # Forcer l'abonnement de tous les tickers
        self.window._subscribe_all_tickers()
    
    def save_file(self):
        """Sauvegarde le workspace"""
        if not self.window.current_file:
            self.save_file_as()
            return
        
        current_path = Path(self.window.current_file)
        
        if current_path.is_dir():
            self._save_workspace_folder(str(current_path))
        else:
            # Fichier legacy - convertir en dossier?
            reply = QMessageBox.question(
                self.window,
                "Format de sauvegarde",
                "Voulez-vous convertir vers le nouveau format dossier?\n"
                "(Permet de partager des pages individuellement)",
                QMessageBox.Yes | QMessageBox.No  # type: ignore
            )
            
            if reply == QMessageBox.Yes:  # type: ignore
                self.save_file_as()
            else:
                self._save_to_legacy_file(str(current_path))
    
    def save_file_as(self):
        """Sauvegarde sous un nouveau dossier workspace"""
        folder_path = QFileDialog.getExistingDirectory(
            self.window,
            "Choisir un dossier pour le Workspace",
            "",
            QFileDialog.ShowDirsOnly  # type: ignore
        )
        
        if folder_path:
            self._save_workspace_folder(folder_path)
            self.window.current_file = folder_path
            self.window.setWindowTitle(f"Strategy Price Monitor - {Path(folder_path).name}")
            
            self.settings.set_last_workspace(folder_path)
            self.settings.add_recent_workspace(folder_path)
    
    def _save_workspace_folder(self, folder_path: str):
        """Sauvegarde le workspace dans un dossier"""
        try:
            folder = Path(folder_path)
            folder.mkdir(parents=True, exist_ok=True)
            
            # Supprimer les anciens fichiers de pages
            for old_file in folder.glob(f"{self.PAGE_PREFIX}*.json"):
                old_file.unlink()
            
            # Sauvegarder chaque page
            pages_order = []
            for page_widget in self.window.pages.values():
                page = page_widget.page
                page_data = page_widget.to_dict()
                
                # Nom de fichier basé sur le nom de la page
                safe_name = sanitize_filename(page.name)
                filename = f"{self.PAGE_PREFIX}{safe_name}_{page.id[:8]}.json"
                
                with open(folder / filename, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=2, ensure_ascii=False)
                
                pages_order.append({
                    'id': page.id,
                    'name': page.name,
                    'filename': filename,
                    'order': page.order
                })
            
            # Sauvegarder les métadonnées
            meta = {
                'version': '3.0',
                'pages_order': pages_order
            }
            with open(folder / self.WORKSPACE_META_FILE, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            
            self.window.statusbar.showMessage(f"Workspace sauvegardé: {folder_path}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self.window,
                "Erreur",
                f"Impossible de sauvegarder:\n{str(e)}"
            )
    
    def _save_to_legacy_file(self, file_path: str):
        """Sauvegarde dans un fichier legacy"""
        try:
            data = self.window.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.window.statusbar.showMessage(f"Sauvegardé: {file_path}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self.window,
                "Erreur",
                f"Impossible de sauvegarder:\n{str(e)}"
            )
    
    def save_current_page(self):
        """Sauvegarde uniquement la page courante (pour auto-save)"""
        if not self.window.current_file:
            return
        
        current_path = Path(self.window.current_file)
        if not current_path.is_dir():
            return
        
        current_page = self.window.get_current_page()
        if not current_page:
            return
        
        try:
            page = current_page.page
            page_data = current_page.to_dict()
            
            safe_name = sanitize_filename(page.name)
            filename = f"{self.PAGE_PREFIX}{safe_name}_{page.id[:8]}.json"
            
            with open(current_path / filename, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
            
            self.window.statusbar.showMessage(f"Page '{page.name}' sauvegardée", 2000)
            
        except Exception as e:
            print(f"Erreur sauvegarde page: {e}")
    
    def export_page(self, page_id: str):
        """Exporte une page dans un fichier JSON"""
        if page_id not in self.window.pages:
            return
        
        page_widget = self.window.pages[page_id]
        page = page_widget.page
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.window,
            f"Exporter la page '{page.name}'",
            f"page_{sanitize_filename(page.name)}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if not file_path.endswith('.json'):
                    file_path += '.json'
                
                page_data = page_widget.to_dict()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=2, ensure_ascii=False)
                
                self.window.statusbar.showMessage(f"Page exportée: {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(
                    self.window,
                    "Erreur",
                    f"Impossible d'exporter:\n{str(e)}"
                )
    
    def import_page(self):
        """Importe une page depuis un fichier JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Importer une page",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                page_data = json.load(f)
            
            # Vérifier le format
            if 'page' not in page_data:
                raise ValueError("Format de fichier invalide")
            
            from ..models.page import Page
            from ..models.strategy import Strategy
            import uuid
            
            # Créer une nouvelle page avec un nouvel ID (éviter les conflits)
            page_info = page_data['page']
            page = Page(
                id=str(uuid.uuid4()),  # Nouvel ID
                name=page_info['name'],
                icon=page_info.get('icon', '📊'),
                order=len(self.window.pages)
            )
            
            self.window._add_page(page, select=True)
            
            page_widget = self.window.pages[page.id]
            for strategy_data in page_data.get('strategies', []):
                # Nouvel ID pour éviter les conflits
                strategy_data['id'] = str(uuid.uuid4())
                for leg in strategy_data.get('legs', []):
                    leg['id'] = str(uuid.uuid4())
                
                strategy = Strategy.from_dict(strategy_data)
                page_widget.add_strategy(strategy)
            
            self.window.statusbar.showMessage(f"Page '{page.name}' importée", 3000)
            
            # Sauvegarder automatiquement si workspace dossier
            if self.window.current_file and Path(self.window.current_file).is_dir():
                self.save_current_page()
                self._update_workspace_meta()
            
        except Exception as e:
            QMessageBox.critical(
                self.window,
                "Erreur",
                f"Impossible d'importer la page:\n{str(e)}"
            )
    
    def _update_workspace_meta(self):
        """Met à jour le fichier de métadonnées du workspace"""
        if not self.window.current_file:
            return
        
        folder = Path(self.window.current_file)
        if not folder.is_dir():
            return
        
        try:
            pages_order = []
            for page_widget in self.window.pages.values():
                page = page_widget.page
                safe_name = sanitize_filename(page.name)
                filename = f"{self.PAGE_PREFIX}{safe_name}_{page.id[:8]}.json"
                
                pages_order.append({
                    'id': page.id,
                    'name': page.name,
                    'filename': filename,
                    'order': page.order
                })
            
            meta = {
                'version': '3.0',
                'pages_order': pages_order
            }
            with open(folder / self.WORKSPACE_META_FILE, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erreur mise à jour meta: {e}")
