"""
Widget pour une jambe d'option (ligne dans une stratégie)
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, 
    QPushButton, QLabel, QSpinBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..models.strategy import OptionLeg, Position


class OptionLegWidget(QWidget):
    """
    Widget représentant une ligne d'option dans une stratégie.
    Contient: ticker, position (long/short), quantité, prix en direct, bouton supprimer
    """
    
    # Signaux
    ticker_changed = Signal(str, str)  # leg_id, new_ticker
    position_changed = Signal(str, Position)  # leg_id, new_position
    quantity_changed = Signal(str, int)  # leg_id, new_quantity
    delete_requested = Signal(str)  # leg_id
    
    def __init__(self, leg: OptionLeg, parent=None):
        super().__init__(parent)
        self.leg = leg
        self._setup_ui()
        self._connect_signals()
        self._load_data()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Ticker input
        self.ticker_edit = QLineEdit()
        self.ticker_edit.setPlaceholderText("SFRH6C 98.00")
        self.ticker_edit.setMinimumWidth(250)
        layout.addWidget(self.ticker_edit)
        
        # Position (Long/Short)
        self.position_combo = QComboBox()
        self.position_combo.addItem("Long", Position.LONG)
        self.position_combo.addItem("Short", Position.SHORT)
        self.position_combo.setMinimumWidth(80)
        layout.addWidget(self.position_combo)
        
        # Quantité
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setMinimumWidth(60)
        layout.addWidget(self.quantity_spin)
        
        # Prix en direct (lecture seule)
        self.price_label = QLabel("--")
        self.price_label.setMinimumWidth(100)
        self.price_label.setAlignment(Qt.AlignCenter) # type: ignore
        self.price_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #00ff00;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.price_label)
        
        # Contribution au prix
        self.contribution_label = QLabel("(+0.00)")
        self.contribution_label.setMinimumWidth(80)
        self.contribution_label.setAlignment(Qt.AlignCenter) # type: ignore
        self.contribution_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.contribution_label)
        
        # Bouton supprimer
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        layout.addWidget(self.delete_btn)
    
    def _connect_signals(self):
        """Connecte les signaux internes"""
        self.ticker_edit.editingFinished.connect(self._on_ticker_changed)
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        self.quantity_spin.valueChanged.connect(self._on_quantity_changed)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
    
    def _load_data(self):
        """Charge les données du leg dans les widgets"""
        self.ticker_edit.setText(self.leg.ticker)
        
        index = self.position_combo.findData(self.leg.position)
        if index >= 0:
            self.position_combo.setCurrentIndex(index)
        
        self.quantity_spin.setValue(self.leg.quantity)
        self.update_price_display()
    
    def _on_ticker_changed(self):
        """Appelé quand le ticker change"""
        new_ticker = self.ticker_edit.text().strip().upper()
        
        # Ajouter automatiquement " Comdty" si pas déjà présent
        if new_ticker and not new_ticker.upper().endswith(" COMDTY"):
            new_ticker = new_ticker + " Comdty"
        
        # Normaliser le ticker (majuscules pour cohérence avec Bloomberg)
        new_ticker = new_ticker.upper()
        self.ticker_edit.setText(new_ticker)
        
        if new_ticker != self.leg.ticker:
            old_ticker = self.leg.ticker
            self.leg.ticker = new_ticker
            self.ticker_changed.emit(self.leg.id, new_ticker)
    
    def _on_position_changed(self, index: int):
        """Appelé quand la position change"""
        new_position = self.position_combo.currentData()
        if new_position != self.leg.position:
            self.leg.position = new_position
            self.position_changed.emit(self.leg.id, new_position)
            self.update_contribution_display()
    
    def _on_quantity_changed(self, value: int):
        """Appelé quand la quantité change"""
        if value != self.leg.quantity:
            self.leg.quantity = value
            self.quantity_changed.emit(self.leg.id, value)
            self.update_contribution_display()
    
    def _on_delete_clicked(self):
        """Appelé quand le bouton supprimer est cliqué"""
        self.delete_requested.emit(self.leg.id)
    
    def update_price(self, last_price: float, bid: float, ask: float):
        """Met à jour le prix affiché"""
        self.leg.update_price(last_price, bid, ask)
        self.update_price_display()
        self.update_contribution_display()
    
    def update_price_display(self):
        """Met à jour l'affichage du prix"""
        price = self.leg.mid if self.leg.mid else self.leg.last_price
        if price is not None:
            self.price_label.setText(f"{price:.4f}")
            self.price_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    color: #00ff00;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Consolas', monospace;
                    font-weight: bold;
                }
            """)
        else:
            self.price_label.setText("--")
            self.price_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    color: #888;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Consolas', monospace;
                }
            """)
    
    def update_contribution_display(self):
        """Met à jour l'affichage de la contribution"""
        contribution = self.leg.get_price_contribution()
        if contribution is not None:
            sign = "+" if contribution >= 0 else ""
            self.contribution_label.setText(f"({sign}{contribution:.4f})")
            color = "#00aa00" if contribution >= 0 else "#ff4444"
            self.contribution_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 11px;
                }}
            """)
        else:
            self.contribution_label.setText("(--)")
            self.contribution_label.setStyleSheet("""
                QLabel {
                    color: #888;
                    font-size: 11px;
                }
            """)
    
    @property
    def ticker(self) -> str:
        """Retourne le ticker actuel"""
        return self.leg.ticker
    
    @property
    def leg_id(self) -> str:
        """Retourne l'ID du leg"""
        return self.leg.id
