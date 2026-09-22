import logging
import re
from functools import cached_property
from typing import cast, Any

from bs4 import Tag
from playwright.sync_api import sync_playwright

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.utils import file_cache 
from src.core.interfaces.abstract_quest_scraper import AbstractQuestScraper 
from src.core.dataclasses import QuestObject

logger = logging.getLogger(__name__)

class FreedomQuestScraper(AbstractQuestScraper):
    """Partial Scraper Class that scrapes quest data for MH Freedom.
    To be called via QuestScraper class."""

    def __init__(
            self,
            config: PartialQuestScraperConfig,
            web_settings: WebSettings,
    ) -> None:
        super().__init__(
            config=config,
            web_settings=web_settings,
        )
        self.monster_list_path = self.utils["monster_list"]

    VILLAGE_QUEST_URL = r"https://monsterhunter.fandom.com/wiki/MHF1:_Village_Quests"
    GUILD_QUEST_URL = r"https://monsterhunter.fandom.com/wiki/MHF1:_Guild_Quests"
    MONSTER_URL = r"https://monsterhunter.fandom.com/wiki/MHF1:_Monsters"

    @cached_property
    @file_cache(
        path_attr="self.cache_path",
        overwrite_attr="self.overwrite",
    )
    def quest_data(self) -> list[dict[str, Any]]:
        _quest_data = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            for url in [self.VILLAGE_QUEST_URL, self.GUILD_QUEST_URL]:
                hub = "Village" if "Village" in url else "Guild"
                soup = self.retrieve_rendered_soup(browser, url)
                quest_tables = soup.find_all("table", class_="themetable")

                _quest_data.extend(
                    [
                        quest 
                        for table in quest_tables
                        if isinstance(table, Tag)
                        and (quest := self.scrape_quest(table, hub))
                    ]
                )

            browser.close()
        return _quest_data

    @cached_property
    @file_cache(
        path_attr="self.monster_list_path",
        overwrite_attr="self.overwrite",
    )
    def monster_list(self) -> list[str]:
        return self._scrape_monster_list()

    def scrape(self) -> list[QuestObject]:
        return [
            QuestObject(
                title= quest["title"],
                quest_id= f"{self.game}_{i}",
                game= self.game,
                generation= self.generation,
                rank= quest.get("rank"),
                level= quest.get("level"),
                is_assignment= quest.get("is_urgent"),
                targets= quest["objective"],
                reward_zenny= quest.get("zenny"),
                reward_points= quest.get("points"),
            ) for i, quest in enumerate(self.quest_data)
        ]

    def scrape_quest(self, table: Tag, hub: str) -> dict[str, Any] | None:
        rows = cast(list[Tag], table.find_all("tr"))

        header_row = rows[0].find_all("th") 
        objective_row = cast(Tag, rows[1])

        targets = [
                target 
                for objective in cast(list[Tag], objective_row.find_all("a", href=True, title=True))
                if (target := objective.get("title"))
            ]
        if not targets: 
            return {}

        tab_header = cast(Tag, table.find_parent("div", class_="wds-tab__content"))
        tab_string = cast(Tag, tab_header.find("span", class_="mw-headline", id=True)).get_text(strip=True)
        rank_info = self._match_rank(tab_string, hub)

        return {
            "title": header_row[1].text.strip(),
            "hub": hub,
            "level": rank_info.get("level"), 
            "rank": rank_info.get("rank"),
            "objective": targets,
            "map": self._get_attribute(table, "Location"),
            "is_urgent": "Urgent" in header_row[0].get_text(strip=True),
            "is_key": "Key" in header_row[0].get_text(strip=True),
            "zenny": self._get_attribute(table, "Reward", "int"),
            "points": self._get_attribute(table, "HR Points", "int"),
        }

    def _get_attribute(self, section: Tag, attribute: str, type_: str = "str") -> str | int | None:
        th_match = section.find(
            lambda tag: tag.name == "th" and re.search(rf"\b{attribute}\b", tag.get_text(), re.IGNORECASE) #type:ignore
        )

        if not th_match:
            return None

        parent_tr = cast(Tag, th_match.find_parent("tr"))
        if not parent_tr:
            return None

        td_cell = parent_tr.find("td")
        if not td_cell:
            return None

        content = td_cell.get_text(strip=True)
        if type_ == "int":
            match = re.search(r"(\d+)", content)
            content = match.group(1) if match else 0

        return content

    def _match_rank(self, tab_string:str, hub: str) -> dict[str,str|int]:
        level, rank = 0, "LR"
        match = re.search(r"(★+)", tab_string)
        if match:
            level = len(match.group(1))
        elif "Urgent" in tab_string:
            if hub == "Village":
                level = 6
            elif hub == "Guild":
                level = 9

        if hub != "Village":
            if level > 5:
                rank = "MR"
            elif level > 3:
                rank = "HR"
        
        return {
            "level": level,
            "rank": rank
        }

    def _scrape_monster_list(self) -> list[str]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            soup = self.retrieve_rendered_soup(browser=browser, url=self.MONSTER_URL)
            start_header = soup.find("span", class_="mw-headline", id="Large_Monsters", string="Large Monsters")

            assert isinstance(start_header, Tag)
            
            t1 = start_header.find_next("table")
            t1 = t1 if isinstance(t1, Tag) else None
            
            t2 = t1.find_next("table") if t1 else None
            t2 = t2 if isinstance(t2, Tag) else None
            
            tables = [t for t in (t1, t2) if t]

            browser.close()

        return [
            title.strip()
            for table in tables
            for a in table.find_all("a", href=True, title=True)
            if isinstance(a, Tag)                     
            and a.find("font") is not None            
            and isinstance(title := a.get("title"), str) 
        ]
