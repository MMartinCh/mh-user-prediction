from abc import ABC, abstractmethod

from config.config_dataclass import PartialQuestScraperConfig, WebSettings #type:ignore
from src.core.interfaces.abstract_web_scraper import AbstractWebScraper #type:ignore
from src.core.dataclasses.quest_object import QuestObject #type:ignore

class AbstractQuestScraper(AbstractWebScraper[QuestObject]):

    def __init__(
        self,
        config: PartialQuestScraperConfig,
        web_settings: WebSettings,
    ) -> None:
        super().__init__(web_settings=web_settings)

        self.game = config.game
        self.generation = config.generation
        self.cache_path = config.cache
        self.overwrite = config.overwrite
        self.utils = config.utils