from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ModelConfig:
    type: str
    n_estimators: int
    max_depth: int

@dataclass(frozen=True)
class PathConfig:
    data_path: str
    outpath: str

@dataclass(frozen=True)
class ScraperConfig:
    overwrite: Optional[bool] = False

@dataclass(frozen=True)
class Config:
    model: ModelConfig
    path: PathConfig
    scraper: ScraperConfig