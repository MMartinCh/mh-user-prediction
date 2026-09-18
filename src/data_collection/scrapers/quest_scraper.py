import logging
from functools import cached_property
from typing import Optional

from ....config.config_dataclass import QuestScrapersConfig, WebSettings
from core.utils.file_cache_module import file_cache #type:ignore
from src.core.dataclasses import QuestObject #type:ignore
from src.core.interfaces import AbstractWebScraper #type:ignore
from src.data_collection.scrapers.partial import ( #type:ignore
    TriQuestScraper,
    FourQuestScraper,
    FreedomQuestScraper,
    FUQuestScraper,
    GenerationsQuestScraper,
    RiseQuestScraper,
    WildsQuestScraper,
    WorldQuestScraper,
)

logger = logging.getLogger(__name__)

class QuestScraper(AbstractWebScraper[QuestObject]):
    """Pipeline calling all PartialQuestScraper classes and merging them into a complete quest dataset."""

    def __init__(
        self,
        config: QuestScrapersConfig,
        web_settings: WebSettings,
        tri_quest_scraper: Optional[TriQuestScraper] = None,
        four_quest_scraper: Optional[FourQuestScraper] = None,
        freedom_quest_scraper: Optional[FreedomQuestScraper] = None,
        fu_quest_scraper: Optional[FUQuestScraper] = None,
        generations_quest_scraper: Optional[GenerationsQuestScraper] = None,
        rise_quest_scraper: Optional[RiseQuestScraper] = None, 
        wilds_quest_scraper: Optional[WildsQuestScraper] = None, 
        world_quest_scraper: Optional[WorldQuestScraper] = None,
    ) -> None:
        super().__init__(web_settings=web_settings)

        self.cache_path = config.cache

        self.scrapers: list[AbstractWebScraper[QuestObject]] = [
            tri_quest_scraper or TriQuestScraper(),
            four_quest_scraper or FourQuestScraper(),
            freedom_quest_scraper or FreedomQuestScraper(),
            fu_quest_scraper or FUQuestScraper(),
            generations_quest_scraper or GenerationsQuestScraper(),
            rise_quest_scraper or RiseQuestScraper(),
            world_quest_scraper or WorldQuestScraper(),
            wilds_quest_scraper or WildsQuestScraper(),
        ]

    @cached_property
    @file_cache("self.cache_path")
    def quest_data(self) -> list[QuestObject]:
        return self._call_partial_scrapers()

    def scrape(self) -> list[QuestObject]:
        return self.quest_data

    def _call_partial_scrapers(self) -> list[QuestObject]:
        """Call all partial quest scrapers and return as list of QuestObjects."""
        return [
            quest 
            for scraper in self.scrapers 
            for quest in scraper.scrape()
        ]