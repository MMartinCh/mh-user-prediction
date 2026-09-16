from typing import Any
from ...src.data_collection.repositories import LocalCsvRepository
from ...src.data_collection.scrapers import QuestScraper, WikiScraper, RankingScraper
from ...src.features import Aggregator, CrossGameNormalizer
from ..core.dataclasses.config_dataclass import Config
from .pipeline import Pipeline

def build_pipeline(config: Config) -> Pipeline:
    """Accept Config and return Pipeline object of specified settings."""

    return Pipeline(
        quest_scraper=_build_quest_scraper(config),
        wiki_scraper=_build_wiki_scraper(config),
        ranking_scraper=_build_ranking_scraper(config),
        aggregator=_build_aggregator(config),
        normalizer=_build_normalizer(config),
        model=_build_model(config),
        repository=_build_repository(config),
    )

def _build_quest_scraper(config: Config) -> QuestScraper:
    return QuestScraper()

def _build_wiki_scraper(config: Config) -> WikiScraper:
    return WikiScraper()

def _build_ranking_scraper(config: Config) -> RankingScraper:
    return RankingScraper()

def _build_aggregator(config: Config) -> Aggregator:
    return Aggregator()

def _build_normalizer(config: Config) -> CrossGameNormalizer:
    return CrossGameNormalizer()

def _build_model(config: Config) -> Any: #HACK: placeholder
    return Any 

def _build_repository(config: Config) -> LocalCsvRepository:
    return LocalCsvRepository()