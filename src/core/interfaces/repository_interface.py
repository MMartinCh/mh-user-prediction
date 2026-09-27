from abc import ABC, abstractmethod
from pathlib import Path
from src.core.dataclasses import MonsterObject

class AbstractMonsterRepository(ABC):
    """Interface for saving and retrieving monster datasets."""
    ROOT_PATH = Path(__file__).resolve().parents[3]
    DATA_PATH = ROOT_PATH / "data"
    
    @abstractmethod
    def save(self, monsters: list[MonsterObject]) -> None:
        """Persist a list of MonsterData objects."""
        pass

    @abstractmethod
    def load(self) -> list[MonsterObject]:
        """Retrieve all persisted MonsterData objects."""
        pass