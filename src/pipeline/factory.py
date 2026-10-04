from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from src.data_collection.repositories import LocalCsvRepository
from src.data_collection.scrapers import QuestScraper, WikiScraper, RankingScraper
from src.data_collection.scrapers.partial import (
    FourQuestScraper,
    FreedomQuestScraper,
    FUQuestScraper,
    GenerationsQuestScraper,
    RiseQuestScraper,
    TriQuestScraper,
    WildsQuestScraper,
    WorldQuestScraper,
)
from src.features import FeatureAssembler, CrossGameNormalizer, QuestFeatureBuilder
from config.config_dataclass import Config
from src.core.interfaces import Model, AbstractQuestScraper
from .pipeline import Pipeline

class PipelineFactory():

    def __init__(self, config: Config) -> None:
        self.config = config

    def build_pipeline(self) -> Pipeline:
        """"Build complete Pipeline from Config."""

        return Pipeline(
            quest_scraper=self._build_quest_scraper(),
            wiki_scraper=self._build_wiki_scraper(),
            ranking_scraper=self._build_ranking_scraper(),
            quest_feature_builder=self._build_quest_feature_builder(),
            assembler=self._build_assembler(),
            normalizer=self._build_normalizer(),
            model=self._build_model(),
            repository=self._build_repository(),
        )

    def _build_quest_scraper(self) -> QuestScraper:
        return QuestScraper(
            config=self.config.scraper.quest,
            web_settings=self.config.scraper.web_settings,
            partial_quest_scrapers=self._build_partial_quest_scrapers()
        )

    def _build_partial_quest_scrapers(self) -> list[AbstractQuestScraper]:
        partial_configs = self.config.scraper.quest.partial
        web_settings = self.config.scraper.web_settings

        return [
            FourQuestScraper(
                config=partial_configs["four"], 
                web_settings=web_settings
            ),
            FreedomQuestScraper(
                config=partial_configs["freedom"],
                web_settings=web_settings,
            ),
            FUQuestScraper(
                config=partial_configs["freedom_unite"],
                web_settings=web_settings,
            ),
            GenerationsQuestScraper(
                config=partial_configs["generations"],
                web_settings=web_settings,
            ),
            RiseQuestScraper(
                config=partial_configs["rise"],
                web_settings=web_settings,
            ),
            TriQuestScraper(
                config=partial_configs["tri"],
                web_settings=web_settings,
            ),
            WildsQuestScraper(
                config=partial_configs["wilds"],
                web_settings=web_settings,
            ),
            WorldQuestScraper(
                config=partial_configs["world"],
                web_settings=web_settings
            ),
        ]

    def _build_wiki_scraper(self) -> WikiScraper:
        return WikiScraper(
            config=self.config.scraper.wiki,
            web_settings=self.config.scraper.web_settings
        )

    def _build_ranking_scraper(self) -> RankingScraper:
        return RankingScraper(
            config=self.config.scraper.ranking,
            web_settings=self.config.scraper.web_settings,
            metadata=self.config.metadata,
        )

    def _build_quest_feature_builder(self) -> QuestFeatureBuilder:
        return QuestFeatureBuilder()

    def _build_assembler(self) -> FeatureAssembler:
        return FeatureAssembler()

    def _build_normalizer(self) -> CrossGameNormalizer:
        return CrossGameNormalizer()

    def _build_model(self) -> Model: 
        settings = self.config.model

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

    def _build_repository(self) -> LocalCsvRepository:
        return LocalCsvRepository()