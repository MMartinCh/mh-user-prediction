from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from ...src.data_collection.repositories import LocalCsvRepository
from ...src.data_collection.scrapers import QuestScraper, WikiScraper, RankingScraper
from ...src.features import FeatureAssembler, CrossGameNormalizer, QuestFeatureBuilder
from ...config.config_dataclass import Config
from ..core.interfaces import Model
from .pipeline import Pipeline

def build_pipeline(config: Config) -> Pipeline:
    """Accept Config and return Pipeline object of specified settings."""

    return Pipeline(
        quest_scraper=_build_quest_scraper(config),
        wiki_scraper=_build_wiki_scraper(config),
        ranking_scraper=_build_ranking_scraper(config),
        quest_feature_builder=_build_quest_feature_builder(config),
        assembler=_build_assembler(config),
        normalizer=_build_normalizer(config),
        model=_build_model(config),
        repository=_build_repository(config),
    )

def _build_quest_scraper(config: Config) -> QuestScraper:
    return QuestScraper(
        config=config.scraper.quest,
        web_settings=config.scraper.web_settings,
    )

def _build_wiki_scraper(config: Config) -> WikiScraper:
    return WikiScraper(
        config=config.scraper.wiki,
        web_settings=config.scraper.web_settings
    )

def _build_ranking_scraper(config: Config) -> RankingScraper:
    return RankingScraper(
        config=config.scraper.ranking,
        web_settings=config.scraper.web_settings,
        metadata_path=config.paths.metadata_path,
    )

def _build_quest_feature_builder(config: Config) -> QuestFeatureBuilder:
    return QuestFeatureBuilder()

def _build_assembler(config: Config) -> FeatureAssembler:
    return FeatureAssembler()

def _build_normalizer(config: Config) -> CrossGameNormalizer:
    return CrossGameNormalizer()

def _build_model(config: Config) -> Model: 
    settings = config.model

    match settings.type:

        case "RandomForestRegressr":
            return RandomForestRegressor(
                n_estimators=settings.n_estimators,
                max_depth=settings.max_depth
            )

        case "LinearRegression":
            return LinearRegression()
        
        case _:
            raise KeyError("%s not a valid model type!", settings.type)

def _build_repository(config: Config) -> LocalCsvRepository:
    return LocalCsvRepository()