import logging
import re
import requests
from functools import cached_property
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
import pandas as pd

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.interfaces import AbstractQuestScraper
from src.core.dataclasses import QuestObject
from src.core.utils import file_cache

logger = logging.getLogger(__name__)

class WorldQuestScraper(AbstractQuestScraper):
    """Partial Scraper Class that scrapes quest data for MH World/ Icebreak.
    To be called via QuestScraper class.
    """

    def __init__(
            self, 
            config: PartialQuestScraperConfig, 
            web_settings: WebSettings
            ) -> None:
        super().__init__(
            config=config, 
            web_settings=web_settings,
            )

        self.monster_data_path = config.utils["monster_data"]
        self.stock_data_path = config.utils["stock_data"]
        self.monster_links_path = config.utils["monster_links"]
        self.quest_links_path = config.utils["quest_links"]

    BASE_URL = r"https://mhw.poedb.tw/eng/monsters/large"

    @cached_property
    @file_cache(
        path_attr="stock_data_path",
        overwrite_attr="overwrite",
    )
    def quest_base(self) -> pd.DataFrame:
        REPO_URL = r"https://raw.githubusercontent.com/gatheringhallstudios/MHWorldData/refs/heads/master/source_data/quests/quest_base.csv"
        return pd.read_csv(REPO_URL)

    @cached_property
    @file_cache(
        path_attr="monster_links_path",
        overwrite_attr="overwrite",
        )
    def monster_links(self) -> dict[str, str]:
        return self._scrape_monster_links()

    @cached_property
    @file_cache(
        path_attr="quest_links_path",
        overwrite_attr="overwrite",
        )
    def quest_links(self) -> list[str]:
        return self._scrape_quest_links_from_monster()

    @cached_property
    @file_cache(
        path_attr="monster_data_path",
        overwrite_attr="overwrite",
        )
    def monster_data(self) -> dict[str, dict[str, Any]]:
        return {
            monster : self.scrape_monster_data(link)
            for monster, link in self.monster_links.items()
        }

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
    )
    def quest_data(self) -> list[dict[str, Any]]:
        return [self.scrape_quest_data(link) for link in self.quest_links]

    def scrape(self) -> list[QuestObject]:
        """Extract quest data from Base Url."""
        category_lookup = self.quest_base.set_index("id")["category"].to_dict()
        print(category_lookup)

        return[
            QuestObject(
                title = quest["title"],
                quest_id = quest["id_"],
                game=self.game,
                generation=self.generation,
                rank = quest["rank"],
                level = quest["level"],
                is_assignment = category_lookup.get(int(quest["id_"])) == "assigned",
                is_event= category_lookup.get(int(quest["id_"])) == "event",
                targets = [monster for monster in quest["monsters_and_hp"]],
                target_hp = quest["monsters_and_hp"],
                reward_zenny = quest["zenny"],
                reward_points = quest["points"],
            ) 
            for quest in self.quest_data
            if quest.get("title") is not None
        ]

    def scrape_quest_data(self, link: str) -> dict[str, Any]:
        soup = self.retrieve_soup(link)
        
        if soup is None:
            logger.warning("No soup for: %s", link)
            return {}

        table_info = soup.select_one("div.card")
        if not isinstance(table_info, Tag):
            logger.warning(
                "Unusual structure for %s | table_info: %s",
                link,
                table_info
            )
            return {}

        table_header = table_info.select_one("div.card-header")

        level_match = re.search(r"(M?★)(\d+)(.+)", table_header.text)
        if not level_match:
            logger.warning(f"Level format not matching for {link}!")
            return {}

        level = int(level_match.group(2))
        rank_str = level_match.group(1).strip()
        rank = "MR"
        if not "M" in rank_str:
            if level > 5:
                rank = "HR"
            else:
                rank = "LR"

        table_monsters = table_info.find_next_sibling("div", class_="card")
        monsters_and_hp = {
            row.find("a", href=True).text.strip():
            int(row.find_all("td")[3].text)
            for row in table_monsters.find("tbody").find_all("tr")
            if "solo" in row.find_all("td")[1].text.lower()
        }

        return {
            "id_": self._get_row_attribute(table_info, "Quest ID"),
            "title": level_match.group(3).strip(),
            "rank": rank,
            "level": level, 
            "map": self._get_row_attribute(table_info, "Map"),
            "zenny": self._get_row_attribute(table_info, "Reward Money"),
            "points": self._get_row_attribute(table_info, "HRReward"),
            "conditions": self._get_row_attribute(table_info, "Conditions"),
            "monsters_and_hp": monsters_and_hp,
            }

    def scrape_monster_data(self, link: str) -> dict[str, Any]:
        soup = self.retrieve_soup(link)
        table_header = soup.select_one("div.card-header")
        table_body = soup.select_one("table.table.table-striped")

        return {
            "name": table_header.get_text(strip=True), 
            "ecology": self._get_row_attribute(table_body, "Ecology"),
            "base_hp": self._get_row_attribute(table_body, "Base HP").replace(",",""),
            "threat": self._get_row_attribute(table_body, "Threat Level"),
            "habitats": [
                habitat.text.strip()
                for habitat in self._get_row_attribute(table_body, "Ecology", next="a", text_=False)
                ],
            "size": re.search(r"Base: (\d+\.\d*)", self._get_row_attribute(table_body, "Size")).group(1), #type:ignore
        }
    
    def _get_row_attribute(self, table: BeautifulSoup, attribute: str, next: str = "td", text_: bool = True) -> Any:
        row = table.find("th", string=re.compile(attribute))
        if not row:
            return None
        return row.find_next(next).text.strip() if text_ else row.find_next(next) #type:ignore

    def _scrape_monster_links(self) -> dict[str, str]:
        soup = self.retrieve_soup(self.BASE_URL)
        return {
            a.text.strip(): urljoin(self.BASE_URL, a.get("href"))
            for a in soup.select("div.list-group.d-flex.flex-row.flex-wrap a.list-group-item[href]")
        }

    def _scrape_quest_links_from_monster(self) -> list[str]:
        quest_links = set()
        for link in self.monster_links.values():
            soup = self.retrieve_soup(link)
            quest_header = soup.find(
                lambda tag: tag.name == "div" 
                and "card-header" in tag.get("class", []) 
                and "Quest" in tag.get_text()
            )
            quest_table = quest_header.find_next("tbody")
            for row in quest_table.find_all("tr"):
                quest_links.add(
                    urljoin(self.BASE_URL, row.find("a", href=True).get("href"))
                    )                    
        return list(quest_links)
        