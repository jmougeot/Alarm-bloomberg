"""
Widget de la sidebar pour naviguer entre les pages
"""
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QScrollArea, QLineEdit, QMenu, QInputDialog,
    QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from ..models.page import Page
from .styles.dark_theme import (
    SIDEBAR_STYLE, 
    SIDEBAR_ITEM_STYLE, 
    SIDEBAR_ITEM_SELECTED_STYLE,
    SIDEBAR_ADD_BUTTON_STYLE
)

if TYPE_CHECKING:
    from .main_window import MainWindow


class SidebarItemWidget(QWidget):
    """Widget pour un élément de la sidebar"""
    
    clicked = Signal(str)  # page_id
    rename_requested = Signal(str, str)  # page_id, new_name
    delete_requested = Signal(str)  # page_id
    
    def __init__(self, page: Page, parent=None):
        super().__init__(parent)
        self.page = page
        self._selected = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Nom (sans icône)
        self.name_label = QLabel(self.page.name)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        self.setStyleSheet(SIDEBAR_ITEM_STYLE)
        self.setCursor(Qt.PointingHandCursor)  # type: ignore
    
    def set_selected(self, selected: bool):
        """Définit si l'élément est sélectionné"""
        self._selected = selected
        if selected:
            self.setStyleSheet(SIDEBAR_ITEM_SELECTED_STYLE)
        else:
            self.setStyleSheet(SIDEBAR_ITEM_STYLE)
    
    def update_page(self, page: Page):
        """Met à jour les infos de la page"""
        self.page = page
        self.name_label.setText(page.name)
    
    def mousePressEvent(self, event):
        """Gère le clic sur l'élément"""
        if event.button() == Qt.LeftButton:  # type: ignore
            self.clicked.emit(self.page.id)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """Menu contextuel (clic droit)"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1e88e5;
            }
        """)
        
        rename_action = QAction("Renommer", self)
        rename_action.triggered.connect(self._on_rename)
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ Supprimer", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)
        
        menu.exec_(event.globalPos())
    
    def _on_rename(self):
        """Renomme la page"""
        new_name, ok = QInputDialog.getText(
            self, 
            "Renommer la page",
            "Nouveau nom:",
            QLineEdit.Normal,  # type: ignore
            self.page.name
        )
        if ok and new_name:
            self.rename_requested.emit(self.page.id, new_name)
    
    def _on_delete(self):
        """Demande la suppression de la page"""
        self.delete_requested.emit(self.page.id)


class SidebarWidget(QWidget):
    """Widget de la sidebar avec la liste des pages"""
    
    page_selected = Signal(str)  # page_id
    page_added = Signal(Page)
    page_renamed = Signal(str, str)  # page_id, new_name
    page_deleted = Signal(str)  # page_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pages: dict[str, Page] = {}
        self.page_items: dict[str, SidebarItemWidget] = {}
        self.current_page_id: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedWidth(220)
        self.setStyleSheet(SIDEBAR_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #1e1e1e;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 12)
        
        title = QLabel("Pages")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Liste des pages (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.pages_container = QWidget()
        self.pages_layout = QVBoxLayout(self.pages_container)
        self.pages_layout.setContentsMargins(8, 8, 8, 8)
        self.pages_layout.setSpacing(4)
        self.pages_layout.addStretch()
        
        scroll_area.setWidget(self.pages_container)
        layout.addWidget(scroll_area)
        
        # Bouton ajouter une page
        self.add_page_btn = QPushButton("+ Nouvelle page")
        self.add_page_btn.setStyleSheet(SIDEBAR_ADD_BUTTON_STYLE)
        self.add_page_btn.clicked.connect(self._on_add_page)
        layout.addWidget(self.add_page_btn)
    
    def add_page(self, page: Page, select: bool = True):
        """Ajoute une page à la sidebar"""
        self.pages[page.id] = page
        
        item = SidebarItemWidget(page)
        item.clicked.connect(self._on_page_clicked)
        item.rename_requested.connect(self._on_page_rename)
        item.delete_requested.connect(self._on_page_delete)
        
        self.page_items[page.id] = item
        
        # Insérer avant le stretch
        self.pages_layout.insertWidget(
            self.pages_layout.count() - 1,
            item
        )
        
        if select:
            self.select_page(page.id)
    
    def remove_page(self, page_id: str):
        """Supprime une page de la sidebar"""
        if page_id in self.page_items:
            item = self.page_items.pop(page_id)
            self.pages_layout.removeWidget(item)
            item.deleteLater()
        
        if page_id in self.pages:
            del self.pages[page_id]
        
        # Sélectionner une autre page si c'était la page courante
        if self.current_page_id == page_id and self.pages:
            first_page_id = next(iter(self.pages.keys()))
            self.select_page(first_page_id)
    
    def select_page(self, page_id: str):
        """Sélectionne une page"""
        if page_id not in self.pages:
            return
        
        # Désélectionner l'ancienne
        if self.current_page_id and self.current_page_id in self.page_items:
            self.page_items[self.current_page_id].set_selected(False)
        
        # Sélectionner la nouvelle
        self.current_page_id = page_id
        if page_id in self.page_items:
            self.page_items[page_id].set_selected(True)
        
        self.page_selected.emit(page_id)
    
    def rename_page(self, page_id: str, new_name: str):
        """Renomme une page"""
        if page_id in self.pages:
            self.pages[page_id].name = new_name
            if page_id in self.page_items:
                self.page_items[page_id].update_page(self.pages[page_id])
    
    def get_all_pages(self) -> list[Page]:
        """Retourne toutes les pages"""
        return list(self.pages.values())
    
    def _on_add_page(self):
        """Ajoute une nouvelle page"""
        name, ok = QInputDialog.getText(
            self,
            "Nouvelle page",
            "Nom de la page:",
            QLineEdit.Normal,  # type: ignore
            f"Page {len(self.pages) + 1}"
        )
        if ok and name:
            page = Page(name=name)
            # Ne pas appeler add_page ici, c'est main_window qui le fera via page_added
            self.page_added.emit(page)
    
    def _on_page_clicked(self, page_id: str):
        """Appelé quand on clique sur une page"""
        self.select_page(page_id)
    
    def _on_page_rename(self, page_id: str, new_name: str):
        """Appelé quand on renomme une page"""
        self.rename_page(page_id, new_name)
        self.page_renamed.emit(page_id, new_name)
    
    def _on_page_delete(self, page_id: str):
        """Appelé quand on veut supprimer une page"""
        if len(self.pages) <= 1:
            QMessageBox.warning(
                self,
                "Impossible",
                "Vous devez garder au moins une page."
            )
            return
        
        page = self.pages.get(page_id)
        if page:
            reply = QMessageBox.question(
                self,
                "Supprimer la page",
                f"Voulez-vous vraiment supprimer la page '{page.name}' et toutes ses stratégies?",
                QMessageBox.Yes | QMessageBox.No  # type: ignore
            )
            if reply == QMessageBox.Yes:  # type: ignore
                self.page_deleted.emit(page_id)
                self.remove_page(page_id)
