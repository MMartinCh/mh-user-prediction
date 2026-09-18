from dataclasses import dataclass

@dataclass(frozen=True)
class RankingObject:
    """DTO retrieved by RankingScraper."""
    monster: str
    rank: int