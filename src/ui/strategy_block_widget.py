"""
Widget bloc pour une stratégie complète (butterfly, condor, etc.)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..models.strategy import Strategy, OptionLeg, Position, StrategyStatus, TargetCondition
from .option_leg_widget import OptionLegWidget


class StrategyBlockWidget(QFrame):
    """
    Widget représentant un bloc de stratégie complet.
    Contient:
    - Nom de la stratégie
    - Liste des legs (options)
    - Prix en direct de la stratégie
    - Prix cible avec tolérance
    - Status (en cours, fait)
    - Boutons pour ajouter/supprimer des legs et supprimer la stratégie
    """
    
    # Signaux
    strategy_deleted = Signal(str)  # strategy_id
    strategy_updated = Signal(str)  # strategy_id
    ticker_added = Signal(str)  # ticker
    ticker_removed = Signal(str)  # ticker
    target_reached = Signal(str)  # strategy_id
    target_left = Signal(str)  # strategy_id - quand le prix sort de la zone
    
    def __init__(self, strategy: Strategy, parent=None):
        super().__init__(parent)
        self.strategy = strategy
        self.leg_widgets: dict[str, OptionLegWidget] = {}
        self._was_target_reached = False  # Pour tracker l'état précédent
        self._setup_ui()
        self._connect_signals()
        self._load_legs()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised) # type: ignore
        self.setLineWidth(2)
        self.setStyleSheet("""
            StrategyBlockWidget {
                background-color: #1e1e1e;
                border: 2px solid #444;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # === Header ===
        header_layout = QHBoxLayout()
        
        # Nom de la stratégie (éditable)
        self.name_edit = QLineEdit(self.strategy.name)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #fff;
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit:focus {
                background-color: #333;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        header_layout.addWidget(self.name_edit)
        
        header_layout.addStretch()
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("En cours", StrategyStatus.EN_COURS)
        self.status_combo.addItem("Fait", StrategyStatus.FAIT)
        self.status_combo.addItem("Annulé", StrategyStatus.ANNULE)
        self.status_combo.setCurrentIndex(
            self.status_combo.findData(self.strategy.status)
        )
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
            }
        """)
        header_layout.addWidget(self.status_combo)
        
        # Bouton supprimer la stratégie
        self.delete_strategy_btn = QPushButton("Supprimer")
        self.delete_strategy_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b0000;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #a00000;
            }
        """)
        header_layout.addWidget(self.delete_strategy_btn)
        
        main_layout.addLayout(header_layout)
        
        # === Séparateur ===
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine) # type: ignore
        separator.setStyleSheet("background-color: #444;")
        main_layout.addWidget(separator)
        
        # === Container pour les legs ===
        self.legs_container = QWidget()
        self.legs_layout = QVBoxLayout(self.legs_container)
        self.legs_layout.setContentsMargins(0, 0, 0, 0)
        self.legs_layout.setSpacing(4)
        main_layout.addWidget(self.legs_container)
        
        # === Bouton ajouter une ligne ===
        add_leg_layout = QHBoxLayout()
        self.add_leg_btn = QPushButton("Ajouter une option")
        self.add_leg_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a27;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3d7a37;
            }
        """)
        add_leg_layout.addWidget(self.add_leg_btn)
        add_leg_layout.addStretch()
        main_layout.addLayout(add_leg_layout)
        
        # === Séparateur ===
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine) # type: ignore
        separator2.setStyleSheet("background-color: #444;")
        main_layout.addWidget(separator2)
        
        # === Prix et cible ===
        price_layout = QHBoxLayout()
        
        # Prix actuel de la stratégie
        price_layout.addWidget(QLabel("Prix mid actuel:"))
        self.current_price_label = QLabel("--")
        self.current_price_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                color: #00ff88;
                border: 2px solid #00aa55;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }
        """)
        self.current_price_label.setMinimumWidth(150)
        self.current_price_label.setAlignment(Qt.AlignCenter) # type: ignore
        price_layout.addWidget(self.current_price_label)
        
        price_layout.addSpacing(30)
        
        # Condition (inférieur/supérieur)
        price_layout.addWidget(QLabel("Alarme si:"))
        self.condition_combo = QComboBox()
        self.condition_combo.addItem("Inférieur à", TargetCondition.INFERIEUR)
        self.condition_combo.addItem("Supérieur à", TargetCondition.SUPERIEUR)
        self.condition_combo.setCurrentIndex(
            self.condition_combo.findData(self.strategy.target_condition)
        )
        self.condition_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 130px;
            }
        """)
        price_layout.addWidget(self.condition_combo)
        
        # Prix cible
        self.target_price_spin = QDoubleSpinBox()
        self.target_price_spin.setRange(-1000, 1000)
        self.target_price_spin.setDecimals(4)
        self.target_price_spin.setSingleStep(0.01)
        self.target_price_spin.setValue(self.strategy.target_price if self.strategy.target_price is not None else 0)
        self.target_price_spin.setSpecialValueText("--")
        self.target_price_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #333;
                color: #ffcc00;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
                font-weight: bold;
            }
        """)
        price_layout.addWidget(self.target_price_spin)
        
        # Indicateur cible atteinte
        self.target_indicator = QLabel("⬤")
        self.target_indicator.setStyleSheet("color: #666; font-size: 20px;")
        self.target_indicator.setToolTip("Cible non définie")
        price_layout.addWidget(self.target_indicator)
        
        price_layout.addStretch()
        main_layout.addLayout(price_layout)
    
    def _connect_signals(self):
        """Connecte les signaux"""
        self.name_edit.editingFinished.connect(self._on_name_changed)
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)
        self.delete_strategy_btn.clicked.connect(self._on_delete_strategy)
        self.add_leg_btn.clicked.connect(self._on_add_leg)
        self.condition_combo.currentIndexChanged.connect(self._on_condition_changed)
        self.target_price_spin.valueChanged.connect(self._on_target_price_changed)
    
    def _load_legs(self):
        """Charge les legs existants"""
        for leg in self.strategy.legs:
            self._add_leg_widget(leg)
    
    def _add_leg_widget(self, leg: OptionLeg):
        """Ajoute un widget de leg"""
        widget = OptionLegWidget(leg)
        widget.ticker_changed.connect(self._on_leg_ticker_changed)
        widget.position_changed.connect(self._on_leg_position_changed)
        widget.quantity_changed.connect(self._on_leg_quantity_changed)
        widget.delete_requested.connect(self._on_leg_delete)
        
        self.leg_widgets[leg.id] = widget
        self.legs_layout.addWidget(widget)
        
        # Émettre le signal pour s'abonner au ticker
        if leg.ticker:
            self.ticker_added.emit(leg.ticker)
    
    def _on_name_changed(self):
        """Appelé quand le nom change"""
        self.strategy.name = self.name_edit.text()
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_status_changed(self, index: int):
        """Appelé quand le status change"""
        self.strategy.status = self.status_combo.currentData()
        self.strategy_updated.emit(self.strategy.id)
        self._update_style_for_status()
    
    def _update_style_for_status(self):
        """Met à jour le style selon le status"""
        if self.strategy.status == StrategyStatus.FAIT:
            self.setStyleSheet("""
                StrategyBlockWidget {
                    background-color: #1a2e1a;
                    border: 2px solid #2d5a27;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)
        elif self.strategy.status == StrategyStatus.ANNULE:
            self.setStyleSheet("""
                StrategyBlockWidget {
                    background-color: #2e1a1a;
                    border: 2px solid #5a2727;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                StrategyBlockWidget {
                    background-color: #1e1e1e;
                    border: 2px solid #444;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)
    
    def _on_delete_strategy(self):
        """Appelé quand on supprime la stratégie"""
        # Émettre les signaux pour se désabonner des tickers
        for leg in self.strategy.legs:
            if leg.ticker:
                self.ticker_removed.emit(leg.ticker)
        
        self.strategy_deleted.emit(self.strategy.id)
    
    def _on_add_leg(self):
        """Ajoute une nouvelle ligne d'option"""
        leg = self.strategy.add_leg()
        self._add_leg_widget(leg)
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_leg_ticker_changed(self, leg_id: str, new_ticker: str):
        """Appelé quand un ticker de leg change"""
        leg = self.strategy.get_leg(leg_id)
        if leg:
            old_ticker = leg.ticker
            if old_ticker and old_ticker != new_ticker:
                self.ticker_removed.emit(old_ticker)
            if new_ticker:
                self.ticker_added.emit(new_ticker)
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_leg_position_changed(self, leg_id: str, position: Position):
        """Appelé quand la position d'un leg change"""
        self._update_strategy_price()
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_leg_quantity_changed(self, leg_id: str, quantity: int):
        """Appelé quand la quantité d'un leg change"""
        self._update_strategy_price()
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_leg_delete(self, leg_id: str):
        """Supprime un leg"""
        leg = self.strategy.get_leg(leg_id)
        if leg and leg.ticker:
            self.ticker_removed.emit(leg.ticker)
        
        if leg_id in self.leg_widgets:
            widget = self.leg_widgets.pop(leg_id)
            self.legs_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.strategy.remove_leg(leg_id)
        self._update_strategy_price()
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_condition_changed(self, index: int):
        """Appelé quand la condition change"""
        self.strategy.target_condition = self.condition_combo.currentData()
        self._update_target_indicator()
        self.strategy_updated.emit(self.strategy.id)
    
    def _on_target_price_changed(self, value: float):
        """Appelé quand le prix cible change"""
        self.strategy.target_price = value if value != 0 else None
        self._update_target_indicator()
        self.strategy_updated.emit(self.strategy.id)
    
    def update_price(self, ticker: str, last_price: float, bid: float, ask: float):
        """Met à jour le prix d'un ticker"""
        # Normaliser le ticker pour la comparaison (strip + upper)
        ticker_normalized = ticker.strip().upper()
        
        for leg_id, widget in self.leg_widgets.items():
            widget_ticker = widget.ticker.strip().upper() if widget.ticker else ""
            if widget_ticker == ticker_normalized:
                widget.update_price(last_price, bid, ask)
        
        self._update_strategy_price()
    
    def _update_strategy_price(self):
        """Met à jour le prix total de la stratégie"""
        price = self.strategy.calculate_strategy_price()
        
        if price is not None:
            self.current_price_label.setText(f"{price:.4f}")
            
            # Couleur selon positif/négatif
            if price >= 0:
                self.current_price_label.setStyleSheet("""
                    QLabel {
                        background-color: #1a1a2e;
                        color: #00ff88;
                        border: 2px solid #00aa55;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 18px;
                        font-weight: bold;
                        font-family: 'Consolas', monospace;
                    }
                """)
            else:
                self.current_price_label.setStyleSheet("""
                    QLabel {
                        background-color: #2e1a1a;
                        color: #ff4444;
                        border: 2px solid #aa0000;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 18px;
                        font-weight: bold;
                        font-family: 'Consolas', monospace;
                    }
                """)
        else:
            self.current_price_label.setText("--")
            self.current_price_label.setStyleSheet("""
                QLabel {
                    background-color: #1a1a2e;
                    color: #888;
                    border: 2px solid #444;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 18px;
                    font-family: 'Consolas', monospace;
                }
            """)
        
        self._update_target_indicator()
    
    def _update_target_indicator(self):
        """Met à jour l'indicateur de cible (seulement si status EN_COURS)"""
        # Ne vérifier l'alarme que si le status est EN_COURS
        if self.strategy.status != StrategyStatus.EN_COURS:
            self.target_indicator.setStyleSheet("color: #666; font-size: 20px;")
            self.target_indicator.setToolTip("Alarme désactivée (stratégie non en cours)")
            self._was_target_reached = False
            return
        
        target_reached = self.strategy.is_target_reached()
        
        if target_reached is None:
            self.target_indicator.setStyleSheet("color: #666; font-size: 20px;")
            self.target_indicator.setToolTip("Cible non définie ou prix non disponible")
            # Si on avait atteint la cible avant, on est sorti
            if self._was_target_reached:
                self._was_target_reached = False
                self.target_left.emit(self.strategy.id)
        elif target_reached:
            self.target_indicator.setStyleSheet("color: #00ff00; font-size: 20px;")
            condition_text = "inférieur" if self.strategy.target_condition == TargetCondition.INFERIEUR else "supérieur"
            self.target_indicator.setToolTip(f"✅ ALARME! Prix {condition_text} à {self.strategy.target_price:.4f}")
            # Émettre le signal seulement si on vient d'atteindre la cible
            if not self._was_target_reached:
                self._was_target_reached = True
                self.target_reached.emit(self.strategy.id)
        else:
            self.target_indicator.setStyleSheet("color: #ff4444; font-size: 20px;")
            
            # Si on avait atteint la cible avant, on est sorti de la zone
            if self._was_target_reached:
                self._was_target_reached = False
                self.target_left.emit(self.strategy.id)
            
            # Calculer la distance à la cible
            current = self.strategy.calculate_strategy_price()
            if current is not None and self.strategy.target_price is not None:
                diff = self.strategy.target_price - current
                condition_text = "⬇️" if self.strategy.target_condition == TargetCondition.INFERIEUR else "⬆️"
                self.target_indicator.setToolTip(f"{condition_text} Distance: {diff:+.4f}")
            else:
                self.target_indicator.setToolTip("En attente...")
    
    @property
    def strategy_id(self) -> str:
        """Retourne l'ID de la stratégie"""
        return self.strategy.id
    
    def get_all_tickers(self) -> list[str]:
        """Retourne tous les tickers de la stratégie"""
        return self.strategy.get_all_tickers()
