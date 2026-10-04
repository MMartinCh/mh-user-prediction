import logging
from functools import cached_property
from typing import Any, Optional

from config.config_dataclass import QuestScrapersConfig, WebSettings 
from src.core.utils.file_cache_module import file_cache 
from src.core.dataclasses import QuestObject 
from src.core.interfaces import AbstractWebScraper, AbstractQuestScraper 

logger = logging.getLogger(__name__)

class QuestScraper(AbstractWebScraper[QuestObject]):
    """Pipeline calling all PartialQuestScraper classes and merging them into a complete quest dataset."""

    def __init__(
        self,
        config: QuestScrapersConfig,
        web_settings: WebSettings,
        partial_quest_scrapers: list[AbstractQuestScraper],
    ) -> None:
        
        super().__init__(
            cache=config.cache,
            overwrite=config.overwrite,
            web_settings=web_settings,
        )

        self.scrapers = partial_quest_scrapers

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
        dataclass_cls=QuestObject,
    )
    def quest_data(self) -> list[QuestObject]:
        return self._call_partial_scrapers()

    def scrape(self) -> list[QuestObject]:
        return [data for data in self.quest_data]

    def _call_partial_scrapers(self) -> list[QuestObject]:
        """Call all partial quest scrapers and return as list of QuestObjects."""
        
        data = []
        for scraper in self.scrapers:
            logger.info("Start Quest scraping for %s", scraper.game)

            data.extend(scraper.scrape())

            logger.info("Quest scraping completed for %s\n", scraper.game)

        return data

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