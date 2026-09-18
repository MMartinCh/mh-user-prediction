from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class ModelConfig:
    type: str
    n_estimators: int
    max_depth: int | None = None

@dataclass(frozen=True)
class WebSettings:
    polite_delay: Optional[float] = None
    timeout: float = 10.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

@dataclass(frozen=True)
class RankingScraperConfig:
    url: str
    cache: Path
    overwrite: bool = False

@dataclass(frozen=True)
class WikiScraperConfig:
    url: str
    cache: Path
    utils: dict[str, Path]
    overwrite: bool = False

@dataclass(frozen=True)
class PartialQuestScraperConfig:
    game: str
    generation: int
    cache: Path | None
    utils: dict[str, Path]
    overwrite: bool = False

@dataclass(frozen=True)
class QuestScrapersConfig:
    cache: Path
    partial: dict[str, PartialQuestScraperConfig]
    overwrite: bool = False

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