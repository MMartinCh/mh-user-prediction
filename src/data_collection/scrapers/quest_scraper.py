import logging
from functools import cached_property
from typing import Any, Optional

from config.config_dataclass import QuestScrapersConfig, WebSettings 
from src.core.utils.file_cache_module import file_cache 
from src.core.dataclasses import QuestObject 
from src.core.interfaces import AbstractWebScraper
from src.data_collection.scrapers.partial import ( 
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
        
        super().__init__(
            cache=config.cache,
            overwrite=config.overwrite,
            web_settings=web_settings,
        )

        self.scrapers = [
            tri_quest_scraper,
            four_quest_scraper,
            freedom_quest_scraper,
            fu_quest_scraper,
            generations_quest_scraper,
            rise_quest_scraper,
            world_quest_scraper,
            wilds_quest_scraper,
        ]

    @cached_property
    @file_cache(
        path_attr="self.cache_path",
        overwrite_attr="self.overwrite",
    )
    def quest_data(self) -> list[QuestObject]:
        return self._call_partial_scrapers()

    def scrape(self) -> list[QuestObject]:
        return [data for data in self.quest_data]

    def _call_partial_scrapers(self) -> list[QuestObject]:
        """Call all partial quest scrapers and return as list of QuestObjects."""
        return [
            quest 
            for scraper in self.scrapers 
            for quest in scraper.scrape()
        ]

    def _unpack_quest_object(self, data: dict[str, Any]) -> QuestObject:
        return QuestObject(
            title=data["quest"],
            quest_id=data.get("id"),
            game=data["game"],
            generation=data["generation"],
            rank=data.get("rank"),
            level=data.get("level"),
            hub=data.get("hub"),
            location=data.get("location"),
            is_assignment=data.get("is_assignment", False),
            is_key=data.get("is_key", False),
            is_event=data.get("is_event", False),
            targets=data["targets"],
            target_hp=data.get("target_hp", {}),
            reward_zenny=data.get("reward_zenny", 0),
            reward_points=data.get("reward_points", 0),
            requirement=data.get("requirement"),
        )