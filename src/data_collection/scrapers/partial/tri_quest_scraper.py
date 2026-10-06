import logging
import re
from functools import cached_property
from typing import Any

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Browser, sync_playwright

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.dataclasses import QuestObject
from src.core.interfaces import AbstractQuestScraper
from src.core.utils import file_cache


logger = logging.getLogger(__name__)


class TriQuestScraper(AbstractQuestScraper):
    """Partial scraper class that scrapes quest data for MH Tri/Tri Ultimate.

    To be called via the QuestScraper class.
    """

    def __init__(
        self,
        config: PartialQuestScraperConfig,
        web_settings: WebSettings,
    ) -> None:
        super().__init__(
            config=config,
            web_settings=web_settings,
        )

        self.quest_links_path = config.utils["quest_links"]

    QUEST_URL = "https://kiranico.com/en/mh3u/quest"

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
    )
    def quest_data(self) -> list[dict[str, Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            _quest_data = [
                quest
                for link in self.quest_links
                if (quest := self.scrape_quest(browser, link))
            ]

            browser.close()

        return _quest_data

    @cached_property
    @file_cache(
        path_attr="quest_links_path", 
        overwrite_attr="overwrite",
    )
    def quest_links(self) -> list[str]:
        return self._scrape_quest_links()

    def scrape(self) -> list[QuestObject]:
        return [
            QuestObject(
                title=quest["title"],
                game=self.game,
                generation=self.generation,
                rank=quest.get("rank"),
                level=quest.get("level"),
                is_assignment=quest.get("is_urgent"),
                is_event=quest.get("is_event"),
                targets=quest["targets"],
                reward_zenny=quest.get("zenny"),
                reward_points=quest.get("points"),
            )
            for quest in self.quest_data
        ]

    def scrape_quest(
        self,
        browser: Browser,
        link: str,
    ) -> dict[str, Any]:
        soup = self.retrieve_rendered_soup(browser, link)
        div = soup.select_one("div.col-sm-3")
        h1_tag = soup.find("h1")

        if not isinstance(div, Tag) or not isinstance(h1_tag, Tag):
            logger.info("Invalid structure for %s", link)
            return {}

        title = (
            h1_string.text.strip()
            if (h1_string := h1_tag.find(text=True, recursive=False))
            else ""
        )

        targets = [
            target.text.strip()
            for target in div.find_all(
                "a",
                string=True,
                href=re.compile(r"monster"),
            )
        ]

        quest_type = self._get_quest_attribute(div, "Type")

        if not targets or quest_type not in [
            "Hunt",
            "Slay",
            "Special",
            "Endurance",
        ]:
            logger.info(
                f"No hunting quest: {title}, quest_type: {quest_type}"
            )
            return {}

        is_urgent = h1_tag.find("span", string="Urgent") is not None

        hub_tag = (
            div_text.text.strip()
            if (div_text := div.find("td", colspan="2", string=True))
            and isinstance(div_text, Tag)
            else ""
        )


        hub, level = hub_tag.split(" ")

        raw_reward = self._get_quest_attribute(div, "Reward")
        zenny = (
            int(raw_reward.replace(",", "").replace("z", ""))
            if raw_reward
            and raw_reward.replace(",", "").replace("z", "").strip().isdigit()
            else 0
        )

        raw_hrp = self._get_quest_attribute(div, "HRP")
        points = (
            int(raw_hrp)
            if raw_hrp and raw_hrp.strip().isdigit()
            else 0
        )

        quest_dict = {
            "title": title,
            "hub": hub,
            "rank": self._match_rank(hub, int(level), is_urgent),
            "level": int(level),
            "type": quest_type,
            "is_key": h1_tag.find("span", string="Key") is not None,
            "is_urgent": is_urgent,
            "is_event": hub == "Event",
            "map": self._get_quest_attribute(div, "Map"),
            "targets": targets,
            "zenny": zenny,
            "points": points,
        }

        return quest_dict

    def _get_quest_attribute(
        self,
        soup: BeautifulSoup | Tag,
        attribute: str,
        default: Any = None,
    ) -> Any | None:
        
        col = soup.find("td", string=re.compile(attribute))
        if col is None:
            logging.warning("%s not found in %s", attribute, soup)
            return default

        col_td = col.find_next("td")
        if col_td is None:
            logging.warning("%s not found ind %s", attribute, col)
            return default

        return col_td.get_text(strip=True)

    def _match_rank(self, hub: str, level: int, is_urgent: bool) -> str:
        if hub == "Village":
            if level == 9 and is_urgent:
                return "MR"
            if level > 5:
                return "HR"
            return "LR"

        if hub in {"Port", "Event"}:
            if level > 5:
                return "MR"
            if level > 2:
                return "HR"

        return "LR"

    def _scrape_quest_links(self) -> list[str]:
        soup = self.retrieve_soup(self.QUEST_URL)

        if soup is None:
            raise AttributeError("Tri Quest url not working: %s", self.QUEST_URL)

        quest_rows = soup.find_all(
            "a",
            string=True,
            href=re.compile(r"quest/\w*/\d+")
        )
        
        return [
            link
            for row in quest_rows
            if isinstance(row, Tag) 
            and isinstance(link := row.get("href"), str)
        ]

