"""
Modèles de données pour les stratégies d'options
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime
import uuid
import re
import json


def normalize_ticker(ticker: str) -> str:
    """
    Normalise un ticker Bloomberg pour garantir la cohérence.
    """
    if not ticker:
        return ""
    
    ticker = ticker.strip().upper()
    ticker = re.sub(r'\bCOMDITY\b', 'COMDTY', ticker, flags=re.IGNORECASE)
    ticker = re.sub(r'\bCOMODITY\b', 'COMDTY', ticker, flags=re.IGNORECASE)
    ticker = re.sub(r'\bCOMDTY\b', 'COMDTY', ticker, flags=re.IGNORECASE)
    ticker = re.sub(r'\s+', ' ', ticker)
    
    return ticker


class Position(Enum):
    """Position sur une option"""
    LONG = "long"
    SHORT = "short"


class StrategyStatus(Enum):
    """Status d'une stratégie"""
    EN_COURS = "En cours"
    FAIT = "Fait"
    ANNULE = "Annulé"


class TargetCondition(Enum):
    """Condition de déclenchement de l'alarme"""
    INFERIEUR = "inferieur"
    SUPERIEUR = "superieur"


@dataclass
class OptionLeg:
    """Représente une jambe d'option dans une stratégie"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str = ""
    position: Position = Position.LONG
    quantity: int = 1
    
    # Prix temps réel (non persistés)
    last_price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid: Optional[float] = None
    delta: Optional[float] = None
    last_update: Optional[datetime] = None
    
    def update_price(self, last_price: float, bid: float, ask: float):
        """Met à jour les prix de l'option"""
        if last_price is not None and last_price >= 0:
            self.last_price = last_price
        if bid is not None and bid >= 0:
            self.bid = bid
        if ask is not None and ask >= 0:
            self.ask = ask
        if self.bid is not None and self.ask is not None:
            self.mid = (self.bid + self.ask) / 2
        self.last_update = datetime.now()
    
    def update_delta(self, delta: float):
        """Met à jour le delta de l'option"""
        if delta is not None and delta > -999:
            self.delta = delta
            self.last_update = datetime.now()
    
    def get_price_contribution(self) -> Optional[float]:
        """Contribution au prix de la stratégie"""
        price = self.mid if self.mid else self.last_price
        if price is None:
            return None
        
        multiplier = 1 if self.position == Position.LONG else -1
        return price * multiplier * self.quantity
    
    def get_delta_contribution(self) -> Optional[float]:
        """Contribution au delta de la stratégie"""
        if self.delta is None:
            return None
        
        multiplier = 1 if self.position == Position.LONG else -1
        return self.delta * multiplier * self.quantity
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "position": self.position.value,
            "quantity": self.quantity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "OptionLeg":
        """Crée depuis un dictionnaire"""
        ticker = normalize_ticker(data.get("ticker", ""))
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            ticker=ticker,
            position=Position(data.get("position", "long")),
            quantity=data.get("quantity", 1)
        )


@dataclass 
class Strategy:
    """Représente une stratégie d'options"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Nouvelle Stratégie"
    legs: List[OptionLeg] = field(default_factory=list)
    
    # Métadonnées
    client: Optional[str] = None
    action: Optional[str] = None
    
    # Alarme
    target_price: Optional[float] = None
    target_condition: TargetCondition = TargetCondition.INFERIEUR
    
    # Status
    status: StrategyStatus = StrategyStatus.EN_COURS
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def add_leg(self, ticker: str = "", position: Position = Position.LONG, quantity: int = 1) -> OptionLeg:
        """Ajoute une jambe à la stratégie"""
        leg = OptionLeg(ticker=ticker, position=position, quantity=quantity)
        self.legs.append(leg)
        self.updated_at = datetime.now()
        return leg
    
    def remove_leg(self, leg_id: str) -> bool:
        """Supprime une jambe par son ID"""
        for i, leg in enumerate(self.legs):
            if leg.id == leg_id:
                self.legs.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_leg(self, leg_id: str) -> Optional[OptionLeg]:
        """Retourne une jambe par son ID"""
        for leg in self.legs:
            if leg.id == leg_id:
                return leg
        return None
    
    def calculate_strategy_price(self) -> Optional[float]:
        """Calcule le prix de la stratégie"""
        if not self.legs:
            return None
        
        total = 0.0
        for leg in self.legs:
            contribution = leg.get_price_contribution()
            if contribution is None:
                return None
            total += contribution
        
        return total
    
    def calculate_strategy_delta(self) -> Optional[float]:
        """Calcule le delta de la stratégie"""
        if not self.legs:
            return None
        
        total = 0.0
        for leg in self.legs:
            contribution = leg.get_delta_contribution()
            if contribution is None:
                return None
            total += contribution
        
        return total
    
    def is_target_reached(self) -> Optional[bool]:
        """Vérifie si le prix a atteint la cible"""
        if self.target_price is None:
            return None
        
        current_price = self.calculate_strategy_price()
        if current_price is None:
            return None
        
        if self.target_condition == TargetCondition.INFERIEUR:
            return current_price <= self.target_price
        else:
            return current_price >= self.target_price
    
    def get_all_tickers(self) -> List[str]:
        """Retourne tous les tickers de la stratégie"""
        return [leg.ticker for leg in self.legs if leg.ticker]
    
    def legs_to_json(self) -> str:
        """Sérialise les legs en JSON pour la BDD"""
        return json.dumps([leg.to_dict() for leg in self.legs])
    
    @staticmethod
    def legs_from_json(legs_json: str) -> List[OptionLeg]:
        """Désérialise les legs depuis JSON"""
        if not legs_json:
            return []
        try:
            legs_data = json.loads(legs_json)
            return [OptionLeg.from_dict(leg) for leg in legs_data]
        except json.JSONDecodeError:
            return []
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour sauvegarde locale"""
        return {
            "id": self.id,
            "name": self.name,
            "client": self.client,
            "action": self.action,
            "legs": [leg.to_dict() for leg in self.legs],
            "target_price": self.target_price,
            "target_condition": self.target_condition.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def to_server_dict(self) -> dict:
        """Convertit en dictionnaire pour le serveur (legs en JSON)"""
        return {
            "id": self.id,
            "name": self.name,
            "client": self.client or "",
            "action": self.action or "",
            "status": self.status.value,
            "target_price": self.target_price,
            "target_condition": self.target_condition.value,
            "legs": self.legs_to_json()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Strategy":
        """Crée depuis un dictionnaire (sauvegarde locale)"""
        condition = data.get("target_condition", "inferieur")
        strategy = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Nouvelle Stratégie"),
            client=data.get("client"),
            action=data.get("action"),
            target_price=data.get("target_price"),
            target_condition=TargetCondition(condition) if condition else TargetCondition.INFERIEUR,
            status=StrategyStatus(data.get("status", "En cours"))
        )
        
        # Legs comme liste ou JSON string
        legs_data = data.get("legs", [])
        if isinstance(legs_data, str):
            strategy.legs = cls.legs_from_json(legs_data)
        else:
            for leg_data in legs_data:
                strategy.legs.append(OptionLeg.from_dict(leg_data))
        
        if data.get("created_at"):
            strategy.created_at = datetime.fromisoformat(data["created_at"])
        
        return strategy
    
    @classmethod
    def from_server_dict(cls, data: dict) -> "Strategy":
        """Crée depuis un dictionnaire serveur (legs en JSON string)"""
        return cls.from_dict(data)
