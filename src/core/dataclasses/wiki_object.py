from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(frozen=True)
class WikiObject:
    """DTO retrieved from the Monster Hunter Wiki - Monster Overview site and recursive Monster links."""
    monster: str

    first_appearance: Optional[str] = None
    latest_appearance: Optional[str] = None

    classification: Optional[str] = None
    elements: List[str] = field(default_factory=list)
    ailments: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    size: Optional[float] = None
    habitats: List[str] = field(default_factory=list)

    is_flagship: Optional[bool] = False
    is_subspecies: Optional[bool] = False
    is_variant: Optional[bool] = False
    is_deviant: Optional[bool] = False
    is_rare_species: Optional[bool] = False
    is_collaboration: Optional[bool] = False
    is_final_boss: Optional[bool] = False
    has_theme: Optional[bool] = False