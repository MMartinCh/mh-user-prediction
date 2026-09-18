import yaml
from pathlib import Path

from .config_dataclass import (
    Config,
    ModelConfig,
    PathsConfig,
    PartialQuestScraperConfig,
    QuestScrapersConfig,
    RankingScraperConfig,
    ScraperConfig,
    WebSettings,
    WikiScraperConfig,
)

class ConfigLoader:

    def __init__(self, path: Path) -> None:
        self.config_path = path
        self.base_path = Path(__file__).resolve().parent

    def load(self) -> Config:
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return Config(
            model=self._load_model_config(config["model"]),
            scraper=self._load_scrapers_config(config["scraper"]),
            paths=self._load_paths_config(config["paths"])
        )

    def _load_model_config(self, data: dict) -> ModelConfig:
        return ModelConfig(
            type=data["type"],
            n_estimators=data["n_estimators"],
            max_depth=data["max_depth"],
        )

    def _load_paths_config(self, data: dict) -> PathsConfig:
        return PathsConfig(
            data_path= self.base_path / data["data_path"],
            metadata_path= self.base_path / data["metadata_path"]
        )

    def _load_scrapers_config(self, data: dict) -> ScraperConfig:
        return ScraperConfig(
            web_settings=WebSettings(
                polite_delay=data["web_settings"]["polite_delay"],
                timeout=data["web_settings"]["timeout"],
                user_agent=data["web_settings"]["user_agent"],
            ),
            ranking=RankingScraperConfig(
                url=data["ranking"]["url"],
                cache=self.base_path / data["ranking"]["cache"],
                overwrite=data["ranking"]["overwrite"]
            ),
            wiki=WikiScraperConfig(
                url=data["wiki"]["url"],
                cache=self.base_path / data["wiki"]["cache"],
                overwrite=data["wiki"]["overwrite"],
                utils=data["wiki"]["utils"]
            ),
            quest=self._load_quest_scraper_config(data["quest"])
        )

    def _load_quest_scraper_config(self, data: dict) -> QuestScrapersConfig:
        partial: dict[str, PartialQuestScraperConfig] = {
            name: partial_scraper
            for name, scraper_data in data["partial"].items()
            if (partial_scraper := PartialQuestScraperConfig(
                game=scraper_data["game"],
                generation=scraper_data["generation"],
                cache=self.base_path / scraper_data["cache"],
                utils={
                    key: self.base_path / path 
                    for key, path in scraper_data["utils"].items()
                },
                overwrite=scraper_data["overwrite"]

            ))
        }

        return QuestScrapersConfig(
            cache=self.base_path / data["cache"],
            partial=partial,
            overwrite=data["overwrite"]
        )