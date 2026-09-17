from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ModelConfig:
    type: str
    n_estimators: int
    max_depth: int | None = None

@dataclass(frozen=True)
class WebSettings:
    overwrite: bool = False
    polite_delay: float = 0.0

@dataclass(frozen=True)
class RankingScraperConfig:
    url: str
    cache: Path

@dataclass(frozen=True)
class WikiScraperConfig:
    url: str
    cache: Path

@dataclass(frozen=True)
class PartialQuestScraperConfig:
    game: str
    generation: int
    cache: Path | None
    utils: dict[str, Path]

@dataclass(frozen=True)
class QuestScrapersConfig:
    cache: Path
    partial: dict[str, PartialQuestScraperConfig]

@dataclass(frozen=True)
class ScraperConfig:
    web_settings: WebSettings
    ranking: RankingScraperConfig
    wiki: WikiScraperConfig
    quest: QuestScrapersConfig

@dataclass(frozen=True)
class PathsConfig:
    data_path: Path
    metadata_path: Path

@dataclass(frozen=True)
class Config:
    model: ModelConfig
    scraper: ScraperConfig
    paths: PathsConfig