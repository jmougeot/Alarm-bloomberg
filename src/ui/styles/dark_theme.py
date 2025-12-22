"""
Thème sombre pour l'application
"""

DARK_THEME_STYLESHEET = """
    QMainWindow {
        background-color: #121212;
    }
    QMenuBar {
        background-color: #1e1e1e;
        color: #fff;
    }
    QMenuBar::item:selected {
        background-color: #333;
    }
    QMenu {
        background-color: #1e1e1e;
        color: #fff;
        border: 1px solid #333;
    }
    QMenu::item:selected {
        background-color: #333;
    }
    QStatusBar {
        background-color: #1e1e1e;
        color: #888;
    }
    QLabel {
        color: #fff;
    }
    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background-color: #444;
        border-radius: 6px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #555;
    }
    
    /* Dialogues */
    QDialog, QInputDialog, QMessageBox {
        background-color: #1e1e1e;
        color: #fff;
    }
    QLineEdit {
        background-color: #2a2a2a;
        color: #fff;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 8px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border-color: #1e88e5;
    }
    QPushButton {
        background-color: #333;
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #444;
    }
    QPushButton:pressed {
        background-color: #555;
    }
    QComboBox {
        background-color: #2a2a2a;
        color: #fff;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 6px 10px;
    }
    QComboBox:hover {
        border-color: #1e88e5;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    QComboBox QAbstractItemView {
        background-color: #2a2a2a;
        color: #fff;
        selection-background-color: #1e88e5;
    }
"""

# === Sidebar Styles ===
SIDEBAR_STYLE = """
    QWidget {
        background-color: #1e1e1e;
        border-right: 1px solid #333;
    }
"""

SIDEBAR_ITEM_STYLE = """
    QWidget {
        background-color: transparent;
        border-radius: 6px;
    }
    QWidget:hover {
        background-color: #2a2a2a;
    }
    QLabel {
        color: #aaa;
        font-size: 14px;
    }
"""

SIDEBAR_ITEM_SELECTED_STYLE = """
    QWidget {
        background-color: #333;
        border-radius: 6px;
        border-left: 3px solid #1e88e5;
    }
    QLabel {
        color: #ffffff;
        font-size: 14px;
        font-weight: bold;
    }
"""

SIDEBAR_ADD_BUTTON_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #666;
        border: 1px dashed #444;
        border-radius: 6px;
        padding: 10px;
        margin: 8px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #2a2a2a;
        color: #fff;
        border-color: #1e88e5;
    }
"""

# === Page Styles ===
PAGE_HEADER_STYLE = """
    QWidget {
        background-color: #1e1e1e;
        border-bottom: 1px solid #333;
    }
    QLabel {
        color: #fff;
    }
"""

PAGE_CONTENT_STYLE = """
    QWidget {
        background-color: #121212;
    }
"""

BUTTON_PRIMARY_STYLE = """
    QPushButton {
        background-color: #1e88e5;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2196f3;
    }
"""

CONNECTION_LABEL_DISCONNECTED = """
    QLabel {
        color: #888;
        font-size: 12px;
        padding: 8px;
    }
"""

SCROLL_AREA_STYLE = """
    QScrollArea {
        border: none;
        background-color: #121212;
    }
"""


def apply_dark_theme(widget):
    """Applique le thème sombre à un widget"""
    widget.setStyleSheet(DARK_THEME_STYLESHEET)
