"""
Gestion de l'authentification utilisateur
"""
import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

from ..ui.login_dialog import LoginDialog

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class AuthHandler:
    """Gère l'authentification utilisateur"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.window = main_window
    
    def attempt_connection(self):
        """Tente de se connecter au serveur"""
        if self.window.auth_service.load_saved_token():
            self.window.server_handler.start_sync()
        else:
            self.show_login_dialog()
    
    def show_login_dialog(self):
        """Affiche le dialog de connexion"""
        dialog = LoginDialog(self.window)
        dialog.login_successful.connect(self._on_login_attempt)
        
        if dialog.exec():
            # Utilisateur a cliqué "Continuer hors ligne"
            self.window._online_mode = False
            self.window.statusbar.showMessage("Mode hors ligne")
            self.window._create_default_page()
        else:
            self.window._online_mode = False
            self.window._create_default_page()
    
    def _on_login_attempt(self, username: str, password: str):
        """Appelé quand l'utilisateur tente de se connecter"""
        dialog = self.window.sender()
        if hasattr(dialog, 'hide_error'):
            dialog.hide_error()
        
        # Déterminer si c'est un login ou register
        is_register = dialog.is_register_mode() if hasattr(dialog, 'is_register_mode') else False
        
        # Exécuter l'authentification
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def do_auth():
                if is_register:
                    return await self.window.auth_service.register(username, password)
                else:
                    return await self.window.auth_service.login(username, password)
            
            success = loop.run_until_complete(do_auth())
            loop.close()
            
            if success:
                if hasattr(dialog, 'accept'):
                    dialog.accept()
                self.window.server_handler.start_sync()
                username_display = self.window.auth_service.user_info.get('username', username) if self.window.auth_service.user_info else username
                self.window.statusbar.showMessage(f"Connecté en tant que {username_display}")
            else:
                if hasattr(dialog, '_show_error'):
                    dialog._show_error("Échec de l'authentification. Vérifiez vos identifiants.")
        except Exception as e:
            if hasattr(dialog, '_show_error'):
                dialog._show_error(f"Erreur de connexion: {str(e)}")
    
    def logout(self):
        """Déconnexion de l'utilisateur"""
        reply = QMessageBox.question(
            self.window,
            "Déconnexion",
            "Voulez-vous vous déconnecter?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Déconnecter du serveur
            self.window.server_handler.stop_sync()
            
            # Supprimer le token
            self.window.auth_service.logout()
            
            # Réinitialiser l'état de l'application
            self._reset_app_state()
            
            # Afficher le dialog de connexion
            self.show_login_dialog()
    
    def _reset_app_state(self):
        """Réinitialise l'état de l'application"""
        # Supprimer toutes les pages de la sidebar
        self.window.sidebar.clear_pages()
        
        # Supprimer tous les widgets de page
        for page_id in list(self.window.pages.keys()):
            page_widget = self.window.pages.pop(page_id)
            self.window.page_stack.removeWidget(page_widget)
            page_widget.deleteLater()
        
        # Réinitialiser les variables d'état
        self.window.current_page_id = None
        self.window._online_mode = False
        self.window._synced_strategies.clear()
        
        # Mettre à jour la statusbar
        self.window.statusbar.showMessage("Déconnecté")
