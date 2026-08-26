from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class QuestItem:
    """Object representing quest data for one quest."""

    title: str
    quest_id: Optional[str] = None 

    game: Optional[str] = None
    generation: Optional[int] = None

    rank: Optional[str] = None
    level: Optional[int] = None

    hub: Optional[str] = None
    location: Optional[str] = None

    is_assignment: Optional[bool] = False
    is_key: Optional[bool] = False
    is_event: Optional[bool] = False

    targets: List[str] = field(default_factory=list)
    target_hp: List[Dict[str,int]] = field(default_factory=list)

    reward_zenny: Optional[int] = 0
    reward_points: Optional[int] = 0

    requirement: Optional[int] = 0

@dataclass
class TransformedQuestItem:
    """Object representing quest data as a monster attribute."""

    title: str
    quest_id: Optional[str] = None 

    game: Optional[str] = None
    generation: Optional[int] = None

    rank: Optional[str] = None
    level: Optional[int] = None

    hub: Optional[str] = None
    location: Optional[str] = None

    is_assignment: Optional[bool] = False
    is_key: Optional[bool] = False
    is_event: Optional[bool] = False

    hp: Optional[int] = None

    reward_zenny: Optional[int] = 0
    reward_points: Optional[int] = 0

    requirement: Optional[int] = 0



