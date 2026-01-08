"""
Widget de la sidebar pour naviguer entre les pages
"""
from typing import Optional, TYPE_CHECKING
from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QScrollArea, QLineEdit, QMenu, QInputDialog,
    QMessageBox, QFrame
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from ..models.page import Page, PageCategory
from .styles.dark_theme import (
    SIDEBAR_STYLE, 
    SIDEBAR_ITEM_STYLE, 
    SIDEBAR_ITEM_SELECTED_STYLE,
    SIDEBAR_ADD_BUTTON_STYLE
)

if TYPE_CHECKING:
    from .main_window import MainWindow


class SectionHeaderWidget(QWidget):
    """Widget pour un en-tête de section dans la sidebar"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 4)
        layout.setSpacing(0)
        
        self.label = QLabel(self.title)
        self.label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            }
        """)
        layout.addWidget(self.label)
        layout.addStretch()
    
    def set_title(self, title: str):
        self.title = title
        self.label.setText(title)


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
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Icône selon le type
        if not self.page.is_owner:
            icon = "👁️"  # Page en lecture seule
        elif self.page.group_id:
            icon = "📁"  # Page de groupe
        else:
            icon = ""  # Page personnelle, pas d'icône
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(icon_label)
        
        # Nom de la page
        self.name_label = QLabel(self.page.name)
        self.name_label.setStyleSheet("color: #fff;")
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Badge si pas owner (read-only)
        if not self.page.can_edit:
            readonly_badge = QLabel("R")
            readonly_badge.setStyleSheet("""
                QLabel {
                    background-color: #555;
                    color: #aaa;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
            """)
            readonly_badge.setToolTip("Lecture seule")
            layout.addWidget(readonly_badge)
        
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
            QMenu::item:disabled {
                color: #666;
            }
        """)
        
        # Renommer (seulement si owner)
        rename_action = QAction("✏️ Renommer", self)
        rename_action.triggered.connect(self._on_rename)
        rename_action.setEnabled(self.page.is_owner)
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        # Supprimer (seulement si owner)
        delete_action = QAction("🗑️ Supprimer", self)
        delete_action.triggered.connect(self._on_delete)
        delete_action.setEnabled(self.page.is_owner)
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
    """Widget de la sidebar avec la liste des pages organisées par sections"""
    
    page_selected = Signal(str)  # page_id
    page_added = Signal(Page)
    page_renamed = Signal(str, str)  # page_id, new_name
    page_deleted = Signal(str)  # page_id
    refresh_requested = Signal()  # Signal pour demander un refresh complet
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pages: dict[str, Page] = {}
        self.page_items: dict[str, SidebarItemWidget] = {}
        self.section_headers: dict[str, SectionHeaderWidget] = {}
        self.current_page_id: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedWidth(240)
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
        self.pages_layout.setContentsMargins(0, 0, 0, 0)
        self.pages_layout.setSpacing(0)
        self.pages_layout.addStretch()
        
        scroll_area.setWidget(self.pages_container)
        layout.addWidget(scroll_area)
        
        # Conteneur pour les boutons du bas
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(8, 8, 8, 8)
        buttons_layout.setSpacing(8)
        
        # Bouton refresh
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Rafraîchir depuis le serveur")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """)
        self.refresh_btn.clicked.connect(self._on_refresh)
        buttons_layout.addWidget(self.refresh_btn)
        
        # Bouton ajouter une page
        self.add_page_btn = QPushButton("+ Nouvelle page")
        self.add_page_btn.setStyleSheet(SIDEBAR_ADD_BUTTON_STYLE)
        self.add_page_btn.clicked.connect(self._on_add_page)
        buttons_layout.addWidget(self.add_page_btn)
        
        layout.addWidget(buttons_container)
    
    def _on_refresh(self):
        """Demande un refresh complet depuis le serveur"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳")
        self.refresh_requested.emit()
        
        # Réactiver après 2 secondes
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self._reset_refresh_button)
    
    def _reset_refresh_button(self):
        """Réactive le bouton refresh"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄")
    
    def _rebuild_layout(self):
        """Reconstruit le layout avec les pages organisées par sections"""
        # Sauvegarder la sélection actuelle
        current_selection = self.current_page_id
        
        # Vider le layout (garder le stretch à la fin)
        while self.pages_layout.count() > 1:
            item = self.pages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)  # type: ignore
        
        # Nettoyer les références aux headers
        self.section_headers.clear()
        
        # Grouper les pages par section
        sections = defaultdict(list)
        for page in self.pages.values():
            section_name = page.section_name
            sections[section_name].append(page)
        
        # Trier les sections: "Mes pages" en premier, puis groupes, puis partagées
        def section_sort_key(section_name: str) -> tuple:
            if section_name.startswith("📄"):  # Mes pages
                return (0, section_name)
            elif section_name.startswith("📁"):  # Groupes
                return (1, section_name)
            elif section_name.startswith("👤"):  # Partagées
                return (2, section_name)
            else:
                return (3, section_name)
        
        sorted_sections = sorted(sections.keys(), key=section_sort_key)
        
        # Insérer les sections et leurs pages
        insert_index = 0
        for section_name in sorted_sections:
            # Header de section
            header = SectionHeaderWidget(section_name)
            self.section_headers[section_name] = header
            self.pages_layout.insertWidget(insert_index, header)
            insert_index += 1
            
            # Pages de cette section (triées par nom)
            section_pages = sorted(sections[section_name], key=lambda p: p.name.lower())
            for page in section_pages:
                item = self.page_items.get(page.id)
                if item:
                    self.pages_layout.insertWidget(insert_index, item)
                    insert_index += 1
        
        # Restaurer la sélection
        if current_selection and current_selection in self.page_items:
            self.page_items[current_selection].set_selected(True)
    
    def add_page(self, page: Page, select: bool = True):
        """Ajoute une page à la sidebar"""
        self.pages[page.id] = page
        
        item = SidebarItemWidget(page)
        item.clicked.connect(self._on_page_clicked)
        item.rename_requested.connect(self._on_page_rename)
        item.delete_requested.connect(self._on_page_delete)
        
        self.page_items[page.id] = item
        
        # Reconstruire le layout pour placer la page dans la bonne section
        self._rebuild_layout()
        
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
        
        # Reconstruire pour mettre à jour les sections
        self._rebuild_layout()
        
        # Sélectionner une autre page si c'était la page courante
        if self.current_page_id == page_id and self.pages:
            first_page_id = next(iter(self.pages.keys()))
            self.select_page(first_page_id)
    
    def clear_pages(self):
        """Supprime toutes les pages de la sidebar"""
        # Vider le layout complet (sauf le stretch)
        while self.pages_layout.count() > 1:
            item = self.pages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Vider les dictionnaires
        self.pages.clear()
        self.page_items.clear()
        self.section_headers.clear()
        self.current_page_id = None
    
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
