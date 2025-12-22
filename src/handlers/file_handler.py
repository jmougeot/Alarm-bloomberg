"""
Gestion des fichiers (ouvrir, sauvegarder, nouveau workspace)
"""
import json
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QMessageBox

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class FileHandler:
    """Gère les opérations sur les fichiers"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
    
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
        """Ouvre un fichier de sauvegarde"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Ouvrir un workspace",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger les données (supporte ancien et nouveau format)
            self.window.load_from_dict(data)
            
            self.window.current_file = file_path
            self.window.setWindowTitle(f"Strategy Price Monitor - {Path(file_path).name}")
            self.window.statusbar.showMessage(f"Fichier chargé: {file_path}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self.window,
                "Erreur",
                f"Impossible de charger le fichier:\n{str(e)}"
            )
    
    def save_file(self):
        """Sauvegarde le workspace"""
        if not self.window.current_file:
            self.save_file_as()
            return
        
        self._save_to_file(self.window.current_file)
    
    def save_file_as(self):
        """Sauvegarde sous un nouveau nom"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Sauvegarder le workspace",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            self._save_to_file(file_path)
            self.window.current_file = file_path
            self.window.setWindowTitle(f"Strategy Price Monitor - {Path(file_path).name}")
    
    def _save_to_file(self, file_path: str):
        """Sauvegarde dans un fichier"""
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
