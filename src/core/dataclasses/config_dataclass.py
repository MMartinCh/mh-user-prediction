from dataclasses import dataclass
from typing import Any, Optional

@dataclass(frozen=True)
class ModelConfig:
    type: str
    n_estimators: int
    max_depth: int

@dataclass(frozen=True)
class PathConfig:
    out: str
    meta: str

@dataclass(frozen=True)
class ScraperConfig:
    overwrite: Optional[bool]
    polite: Optional[bool] 
    main: dict[str, Any]

@dataclass(frozen=True)
class Config:
    model: ModelConfig
    path: PathConfig
    scraper: ScraperConfig