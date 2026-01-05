"""
Dialog de login pour l'authentification au serveur
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTabWidget, QWidget,
    QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import asyncio


class LoginDialog(QDialog):
    """Dialog de connexion/inscription au serveur"""
    
    login_successful = Signal(str, str)  # username, password
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion au serveur")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Bloomberg Alarm Server")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)  # type: ignore
        layout.addWidget(title)
        
        # Tabs login/register
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_login_tab(), "Connexion")
        self.tabs.addTab(self._create_register_tab(), "Inscription")
        layout.addWidget(self.tabs)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #ff4444; padding: 8px;")
        self.error_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Bouton mode hors ligne
        offline_btn = QPushButton("Continuer hors ligne")
        offline_btn.clicked.connect(self.reject)
        offline_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #aaa;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        layout.addWidget(offline_btn)
    
    def _create_login_tab(self) -> QWidget:
        """Crée l'onglet de connexion"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Username
        layout.addWidget(QLabel("Nom d'utilisateur:"))
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("username")
        self.login_username.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: #fff;
            }
        """)
        layout.addWidget(self.login_username)
        
        # Password
        layout.addWidget(QLabel("Mot de passe:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)  # type: ignore
        self.login_password.setPlaceholderText("••••••••")
        self.login_password.setStyleSheet(self.login_username.styleSheet())
        self.login_password.returnPressed.connect(self._on_login_clicked)
        layout.addWidget(self.login_password)
        
        # Remember me
        self.remember_checkbox = QCheckBox("Se souvenir de moi")
        self.remember_checkbox.setChecked(True)
        layout.addWidget(self.remember_checkbox)
        
        layout.addSpacing(10)
        
        # Bouton connexion
        login_btn = QPushButton("Se connecter")
        login_btn.clicked.connect(self._on_login_clicked)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a27;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3d7a37;
            }
            QPushButton:pressed {
                background-color: #1d4a17;
            }
        """)
        layout.addWidget(login_btn)
        
        layout.addStretch()
        return widget
    
    def _create_register_tab(self) -> QWidget:
        """Crée l'onglet d'inscription"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Username
        layout.addWidget(QLabel("Nom d'utilisateur:"))
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("username")
        self.register_username.setStyleSheet(self.login_username.styleSheet())
        layout.addWidget(self.register_username)
        
        # Password
        layout.addWidget(QLabel("Mot de passe:"))
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.Password)  # type: ignore
        self.register_password.setPlaceholderText("••••••••")
        self.register_password.setStyleSheet(self.login_username.styleSheet())
        layout.addWidget(self.register_password)
        
        # Confirm password
        layout.addWidget(QLabel("Confirmer le mot de passe:"))
        self.register_confirm = QLineEdit()
        self.register_confirm.setEchoMode(QLineEdit.Password)  # type: ignore
        self.register_confirm.setPlaceholderText("••••••••")
        self.register_confirm.setStyleSheet(self.login_username.styleSheet())
        self.register_confirm.returnPressed.connect(self._on_register_clicked)
        layout.addWidget(self.register_confirm)
        
        layout.addSpacing(10)
        
        # Bouton inscription
        register_btn = QPushButton("Créer un compte")
        register_btn.clicked.connect(self._on_register_clicked)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5a8b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2a6a9b;
            }
            QPushButton:pressed {
                background-color: #0a4a7b;
            }
        """)
        layout.addWidget(register_btn)
        
        layout.addStretch()
        return widget
    
    def _on_login_clicked(self):
        """Appelé quand on clique sur Se connecter"""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            self._show_error("Veuillez remplir tous les champs")
            return
        
        # Émettre le signal
        self.login_successful.emit(username, password)
    
    def _on_register_clicked(self):
        """Appelé quand on clique sur Créer un compte"""
        username = self.register_username.text().strip()
        password = self.register_password.text()
        confirm = self.register_confirm.text()
        
        if not username or not password or not confirm:
            self._show_error("Veuillez remplir tous les champs")
            return
        
        if password != confirm:
            self._show_error("Les mots de passe ne correspondent pas")
            return
        
        if len(password) < 6:
            self._show_error("Le mot de passe doit contenir au moins 6 caractères")
            return
        
        # Émettre le signal (même signal que login, le parent gérera)
        self.login_successful.emit(username, password)
    
    def _show_error(self, message: str):
        """Affiche un message d'erreur"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def hide_error(self):
        """Cache le message d'erreur"""
        self.error_label.hide()
    
    def is_register_mode(self) -> bool:
        """Retourne True si on est dans l'onglet inscription"""
        return self.tabs.currentIndex() == 1
