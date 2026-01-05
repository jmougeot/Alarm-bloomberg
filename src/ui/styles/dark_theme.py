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
