from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass(frozen=True) 
class MonsterObject:
    """Domain model representing a single monster's raw and engineered traits."""
    monster_name: Optional[str] = None

    # Meta data
    first_appearance: Optional[str] = None
    latest_appearance: Optional[str] = None
    generation: Optional[int] = None

    quest_levels: List[int] = field(default_factory=list)
    classification: Optional[str] = None

    is_flagship: Optional[bool] = False
    is_subspecies: Optional[bool] = False
    is_variant: Optional[bool] = False
    is_deviant: Optional[bool] = False
    is_rare_species: Optional[bool] = False
    is_collaboration: Optional[bool] = False

    # Gameplay data
    difficulty: Optional[str] = None

    base_hp: Optional[int] = None
    size: Optional[float] = None
    weaknesses: List[str] = field(default_factory=list)
    elements: List[str] = field(default_factory=list)
    ailments: List[str] = field(default_factory=list)

    habitats: List[str] = field(default_factory=list)
    
    # Target variable (y)
    rank: Optional[int] = None





