from dataclasses import dataclass

@dataclass(frozen=True)
class RankingObject:
    """DTO retrieved by RankingScraper."""
    monster_name: str
    rank: int