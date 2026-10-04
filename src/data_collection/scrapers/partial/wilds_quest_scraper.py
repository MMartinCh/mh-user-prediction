import logging
import re
from functools import cached_property
from typing import Any
from urllib.parse import urljoin

from bs4 import Tag

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.interfaces import AbstractQuestScraper
from src.core.dataclasses import QuestObject 
from src.core.utils import file_cache 

logger = logging.getLogger(__name__)

class WildsQuestScraper(AbstractQuestScraper):
    """Partial Scraper Class that scrapes quest data for MH Wilds from MH Wiki.
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

    MHWIKI_URL = r"https://monsterhunterwiki.org/wiki/MHWilds/Quests/"
    KIRANICO_URL = r"https://mhwilds.kiranico.com/data/quests"

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
    )
    def raw_quest_data(self) -> list[dict[str, Any]]:
        return self.scrape_raw_quests()

    @cached_property
    @file_cache(
        path_attr="monster_data_path",
        overwrite_attr="overwrite",
    )
    def hp_rp_data(self) -> dict[str, dict[str,int]]:
        return self.scrape_hp_and_rp()

    def scrape(self) -> list[QuestObject]:
        # TODO: for missing hp and rp - get base hp and use generic multiplier for lr and hr; same for rp
        quest_items = []
        raw_quest_data_ = self.raw_quest_data
        
        for i, quest in enumerate(raw_quest_data_):
            title = quest["title"]

            hp_rp = self.hp_rp_data.get(title, {})
            
            target_hp: int = hp_rp.get("targets_hp", 0) 
            reward_points: int = hp_rp.get("reward_points", 0)

            targets = quest["targets"]

            quest_items.append(
                QuestObject(
                    title=title,
                    quest_id=f"mh_wilds_{i}",
                    game=self.game,
                    generation=self.generation,
                    rank=quest["rank"],
                    level=quest["level"],
                    is_assignment=quest["is_assignment"],
                    is_event=quest["is_event"],
                    targets=targets,
                    target_hp={
                        target: target_hp
                        for target in targets
                    },
                    reward_zenny=quest["reward_zenny"],
                    reward_points=reward_points,
                )
            )
        return quest_items

    def scrape_raw_quests(self) -> list[dict [str, Any]]:
        """Scrape all MH Wilds quests and return as structured quest data per quest."""
        raw_rise_quests = []
        for quest_type in ["Assignments", "Optional_Quests", "Event_Quests"]:
            raw_rise_quests.extend(self._extract_quest_data(quest_type))
        return raw_rise_quests

    def _extract_quest_data(self, quest_type: str) -> list[dict [str,Any]]:
        full_link = urljoin(self.MHWIKI_URL, quest_type)
        soup = self.retrieve_soup(full_link)

        if soup is None:
            logger.warning("Invalid link: %s", full_link)
            return []

        quest_tables = soup.select('table.wikitable[style="text-align:center; width:100%"]')

        quest_data = []
        for table in quest_tables:
            header = table.find('th', colspan='3')
            title = header.find('a', href=True, title=True).text.strip()
            level = int(header.find('span', string=re.compile(r'\d+')).text.replace("★","").strip())
            rank = "LR" if level <= 3 else "HR"

            goal_td, details_td, _ = table.select('td[style^="width:33.33%"]')

            targets = [
                target.strip()
                for a in goal_td.find_all("a", href=True, text=True)
                if (target := a.text)
            ]

            requirements = details_td.find('b', string="Requirements:").next_sibling.strip()
            locale = details_td.find('b', string="Locale:").find_next_sibling('a').text.strip()
            reward_zenny = int(details_td.find('b', string="Reward Money:").next_sibling.replace("z","").strip())

            quest_data.append({
                "title": title,
                "level": level,
                "rank": rank,
                "targets": targets,
                "requirements": requirements,
                "locale": locale,
                "reward_zenny": reward_zenny,
                "is_assignment": quest_type == "Assignments",
                "is_event": quest_type == "Event_Quests",
            })
            print(quest_data)
        
        return quest_data

    def scrape_hp_and_rp(self) -> dict[str, dict[str, int]]:
        """Scrapes Rank Points and Monster Hp for every quest from the Monster Hunter Wilds Kiranico database."""
        soup = self.retrieve_soup(self.KIRANICO_URL)

        if soup is None:
            logger.warning("No soup for %s", self.KIRANICO_URL)
            return {}

        if not isinstance(table := soup.find("table", class_="w-full caption-bottom text-sm"), Tag):
            return {}
        
        quest_rows = table.find_all("tr")

        quest_rp_and_hp = {}
        for row in quest_rows:
            if not isinstance(row, Tag):
                continue

            cells = row.find_all("td")

            title = cells[0].text.split("]")[-1].strip()
            reward_points = int(cells[1].text.strip().replace(",", "").replace("HRP", ""))
            
            monsters_in_quest = [
                link.text.strip() 
                for link in cells[2].find_all("a") 
                if link.text.strip()
            ]
            monster_hp_divs = [
                div.text.strip() 
                for div in cells[3].find_all("div") 
                if div.text.strip()
            ]
            monster_hp = int(monster_hp_divs[0].replace(",", "").replace("HP", "")) if monster_hp_divs else None

            quest_rp_and_hp[title] = {
                "reward_points": reward_points,
                "targets": monsters_in_quest,
                "targets_hp": monster_hp,
            }
        return quest_rp_and_hp