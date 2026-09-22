import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, soup, Tag
from playwright.sync_api import Browser, sync_playwright

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.utils import file_cache 
from src.core.interfaces.abstract_quest_scraper import AbstractQuestScraper
from src.core.dataclasses import QuestObject 

logger = logging.getLogger(__name__)

class FourQuestScraper(AbstractQuestScraper):
    """Partial Scraper Class that scrapes quest data for MH Four Ultimate.
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

        self.monster_data_path = self.utils["monster_data"]
        self.monster_links_path = self.utils["monster_links"]
        self.quest_links_path = self.utils["quest_links"]

    QUEST_URL = r"https://kiranico.com/en/mh4u/quest"
    MONSTER_URL = r"https://kiranico.com/en/mh4u/monster"

    @cached_property
    @file_cache(
        path_attr="self.cache_path", 
        overwrite_attr="self.overwrite",
    )
    def quest_data(self) -> list[dict[str,Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            _quest_data = [
                quest for link in self.quest_links
                if (quest := self.scrape_quest(browser, link))
                ]
            browser.close()
            return _quest_data

    @cached_property
    @file_cache(
        path_attr="self.monster_data_path",
        overwrite_attr="self.overwrite"
    )
    def monster_data(self) -> list[dict[str, Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            _monster_data = [
                monster for link in self.monster_links
                if (monster := self.scrape_monster(browser, link))
                ]
            browser.close()
            return _monster_data
    
    @cached_property
    @file_cache(
        path_attr="self.quest_link_path",
        overwrite_attr="self.overwrite",
    )
    def quest_links(self) -> list[str]:
        return self._scrape_links("quest")

    @cached_property
    @file_cache(
        path_attr="self.monster_link_path",
        overwrite_attr="self.overwrite",
    )
    def monster_links(self) -> list[str]:
        return self._scrape_links("monster")

    def scrape(self) -> list[QuestObject]:
        hp_lookup = {
            monster: hp
            for monster_dict in self.monster_data
            if (monster := monster_dict.get("monster"))
            and (hp := {
                "base": monster_dict.get("base_hp"),
                "lr": monster_dict.get("lr_hp"),
                "hr": monster_dict.get("hr_hp"),
                "mr": monster_dict.get("mr_hp")
            })
        }

        complete_data = []
        for quest in self.quest_data:
            if not quest.get("targets"):
                continue

            rank = quest.get("rank")
            target_hp = {}
            for target in quest.get("targets", []):
                if monster_hp := hp_lookup.get(target):
                    if hp_value := monster_hp.get(rank.lower() if rank else ""):
                        target_hp[target] = hp_value
                    elif base_hp := monster_hp.get("base"):
                        target_hp[target] = base_hp

            complete_data.append(
                QuestObject(
                    title=quest["title"],
                    game=self.game,
                    generation=self.generation,
                    rank=rank,
                    level=quest.get("level"),
                    is_assignment=quest.get("is_urgent"),
                    is_event=quest.get("is_event"),
                    targets=quest["targets"],
                    target_hp=target_hp,
                    reward_zenny=quest.get("zenny"),
                    reward_points=quest.get("points"),
                )
            )

        return complete_data

    def scrape_quest(self, browser:Browser, link:str) -> dict[str,Any]:
        soup = self.retrieve_rendered_soup(browser, link)

        div = soup.select_one("div.col-sm-3")
        assert isinstance(div, BeautifulSoup)

        h1_tag = soup.find("h1")
        assert isinstance(h1_tag, Tag)

        title = "".join([element for element in h1_tag.contents if isinstance(element, str)]).strip()

        targets = [
                target.text.strip()
                for target in div.find_all(
                    "a", string=True, href=re.compile(r"monster")
                    )
                ]
        
        quest_type = self._get_quest_attribute(div, "Type")
        if not quest_type in ["Hunting", "Slaying", "Special"] or targets is None:
            return {}

        hub = ""
        level = 0
        hub_tag = div.find("td", colspan="2", string=True)

        if hub_tag:
            hub_text = hub_tag.text.strip().split(" ")
            hub = hub_text[0]
            level = int(hub_text[1])

        raw_reward = self._get_quest_attribute(div, "Reward")
        zenny = int(raw_reward.replace(",","").replace("z","")) if raw_reward and raw_reward.replace(",","").replace("z","").strip().isdigit() else 0
        raw_hrp = self._get_quest_attribute(div, "HRP")
        points = int(raw_hrp) if raw_hrp and raw_hrp.strip().isdigit() else 0

        return {
            "title": title,
            "hub": hub,
            "rank": self._match_rank(hub, level, title),
            "level": level,
            "type": quest_type,
            "is_key": h1_tag.find("span", string="Key") is not None,
            "is_urgent": h1_tag.find("span", string="Urgent") is not None,
            "is_event": hub == "Event",
            "map": self._get_quest_attribute(div, "Map"),
            "targets": targets,
            "zenny": zenny,
            "points": points,
        }

    def scrape_monster(self, browser:Browser, link:str) -> dict[str,Any]:
        soup = self.retrieve_rendered_soup(browser, link)
        h1_tag = soup.find("h1")

        monster_name = "" 
        if isinstance(h1_tag, Tag):
            monster_name = "".join(
                element for element in h1_tag
                if isinstance(element, str)
                ).strip()

        hp_header = soup.find("h5", string="HP")
        size_header = soup.find("h5", string="Crown Sizes")
     
        assert isinstance(hp_header, Tag)
        assert isinstance(size_header, Tag)

        hp_table = hp_header.find_next("table")
        size_table = size_header.find_next("table")

        return {
            "monster": monster_name,
            "base_hp": float(self._get_quest_attribute(hp_table, "Base HP", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "lr_hp": float(self._get_quest_attribute(hp_table, "Low", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "hr_hp": float(self._get_quest_attribute(hp_table, "High", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "mr_hp": float(self._get_quest_attribute(hp_table, "G", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "small_size": float(self._get_quest_attribute(size_table, "Miniature", "0").replace("<","").replace(">","")), #type:ignore
            "large_size": float(self._get_quest_attribute(size_table, "Large", "0").replace("<","").replace(">","")), #type:ignore
            "max_size": float(self._get_quest_attribute(hp_table, "King", "0").replace("<","").replace(">","")), #type:ignore
        }

    def _get_quest_attribute(self, soup: BeautifulSoup, attribute: str, default: Any = None) -> Any | None:
        col = soup.find("td", string=re.compile(attribute))
        if col:
            td = col.find_next("td")
            if td:
                return td.get_text(strip=True)
        return default

    def _match_rank(self, hub:str, level:int, title:str) -> str:
        rank = "LR"
        if hub == "Caravan":
            if level > 6:
                rank = "HR"
            elif level == 10 and "Advanced" in title:
                rank = "MR"
        elif hub in ["Guild", "Event"]:
            if level > 3:
                rank = "HR"
            elif level > 7:
                rank = "MR"
        return rank

    def _scrape_links(self, type_: str) -> list[str]:
        if not type_.lower() in ["monster", "quest"]:
            raise AttributeError(f"Type {type_} no suitable category. Try MONSTER or QUEST...")

        url = getattr(self, f"{type_.upper()}_URL")
        soup = self.retrieve_soup(url)
        assert isinstance(soup, BeautifulSoup)

        return [
            link
            for row in soup.find_all(
                    "a", 
                    string=True, 
                    href=re.compile(rf"^https://kiranico.com/en/mh4u/{type_.lower()}/\d+/.*")
                    )
                    if isinstance(row, Tag) 
                    and (link := row.get("href"))
                    and isinstance(link, str)
        ]

