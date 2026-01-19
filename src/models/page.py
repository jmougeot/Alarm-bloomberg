"""
Modèle de données pour une page de stratégies
"""
import uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PageCategory(Enum):
    """Catégorie de page pour le tri dans la sidebar"""
    PERSONAL = "personal"
    GROUP = "group"
    SHARED = "shared"


@dataclass
class Page:
    """Représente une page/catégorie de stratégies"""
    
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Propriétaire
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    is_owner: bool = True
    
    # Groupe (si page de groupe)
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    
    # Partage
    shared_by: Optional[str] = None
    can_edit: bool = True
    
    @property
    def category(self) -> PageCategory:
        """Détermine la catégorie de la page"""
        if self.group_id:
            return PageCategory.GROUP
        elif not self.is_owner and self.shared_by:
            return PageCategory.SHARED
        else:
            return PageCategory.PERSONAL
    
    @property
    def section_name(self) -> str:
        """Nom de la section pour l'affichage"""
        if self.group_id and self.group_name:
            return f"📁 {self.group_name}"
        elif not self.is_owner and self.shared_by:
            return f"👤 {self.shared_by}"
        else:
            return "📄 Mes pages"
    
    def to_dict(self) -> dict:
        """Convertit la page en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'is_owner': self.is_owner,
            'group_id': self.group_id,
            'group_name': self.group_name,
            'shared_by': self.shared_by,
            'can_edit': self.can_edit,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Page':
        """Crée une page depuis un dictionnaire"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'Page sans nom'),
            owner_id=data.get('owner_id'),
            owner_name=data.get('owner_name'),
            is_owner=data.get('is_owner', True),
            group_id=data.get('group_id'),
            group_name=data.get('group_name'),
            shared_by=data.get('shared_by'),
            can_edit=data.get('can_edit', True),
        )
