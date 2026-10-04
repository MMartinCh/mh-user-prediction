import logging
import requests
from functools import cached_property
from typing import Any, Dict, List

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.utils import file_cache 
from src.core.interfaces.abstract_quest_scraper import AbstractQuestScraper
from src.core.dataclasses import QuestObject 

logger = logging.getLogger(__name__)

class FUQuestScraper(AbstractQuestScraper):
    """Scrapes quests for Freedom Unite and returns list of quest items."""

    def __init__(
            self, 
            config: PartialQuestScraperConfig, 
            web_settings: WebSettings
            ) -> None:
        super().__init__(
            config=config, 
            web_settings=web_settings,
            )

        self.quest_data_path = config.utils["stock_data"]

    SOURCE_REPO = r"Kolyn090/mhfu-db/refs/heads/main/Quests/"

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
        )
    def cached_quest_data(self) -> list[dict[str, Any]]:
        return self.fetch_quest_data()

    @cached_property
    def raw_cache_data(self) -> dict[str, list[dict[str, Any]]]:
        return self._fetch_handler_data_from_github() 

    def scrape(self) -> list[QuestObject]:
        return [
            QuestObject(
                title=quest["name"],
                game=self.game,
                generation=self.generation,
                rank=self._match_rank(handler = quest.get("handler")),
                level=quest.get("difficulty"),
                is_assignment=quest.get("quest-type", "").strip() == "key",
                targets=quest["main-monsters"],
                reward_zenny=quest.get("reward")
            )
            for quest in self.cached_quest_data
        ]

    def _match_rank(self, handler) -> str:
        match handler:
            case "Elder":
                rank = "LR"
            case "Nekoht":
                rank = "HR"
            case "Guild_LR":
                rank = "LR"
            case "Guild_HR":
                rank = "HR"
            case "Guild_MR":
                rank = "MR"
            case _:
                rank = f"unknown: {handler}"
        return rank

    def fetch_quest_data(self) -> list[dict[str, Any]]:
        return [
            {**quest, "handler": handler}
            for handler, quest_list in self.raw_cache_data.items()
            for quest in quest_list
            if isinstance(quest, dict) 
        ]

    def _fetch_handler_data_from_github(self) -> dict[str, list[dict[str, Any]]]:
        files_to_fetch = {
            "Elder" : "elder.json",
            "Nekoht" : "nekoht.json",
            "Guild_LR" : "gal-1.json",
            "Guild_HR" : "gal-2.json",
            "Guild_MR" : "gal-3.json",
        }

        raw_quest_data = {}
        for handler, file in files_to_fetch.items():
            url = f"https://raw.githubusercontent.com/{self.SOURCE_REPO}/{file}"
            response = requests.get(url)
            logger.info(f"Fetching data from {url}...")

            if response.status_code == 200:
                raw_quest_data[handler] = response.json()
            else:
                logger.warning(f"Issue with fetching {handler}-data: {response.status_code}")

        return raw_quest_data