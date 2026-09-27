import re
from functools import cached_property
from typing import Any

from bs4 import BeautifulSoup, Tag

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.dataclasses import QuestObject
from src.core.interfaces.abstract_quest_scraper import AbstractQuestScraper
from src.core.utils import file_cache


class GenerationsQuestScraper(AbstractQuestScraper):
    """Partial scraper class that scrapes quest data for MH G/GU.

    To be called via QuestScraper class.
    """

    KIRANICO_URL = "https://mhgu.kiranico.com/"

    def __init__(
        self,
        config: PartialQuestScraperConfig,
        web_settings: WebSettings,
    ) -> None:
        super().__init__(
            config=config,
            web_settings=web_settings,
        )

        self.monster_data_path = config.utils["monster_data"]
        self.quest_links_path = config.utils["quest_links"]
        self.monster_links_path = config.utils["monster_links"]

    @cached_property
    @file_cache(
        path_attr="self.cache_path",
        overwrite_attr="self.overwrite",
    )
    def quest_data(self) -> list[dict[str, Any]]:
        return [
            self.scrape_quest(quest)
            for quest in self.quest_links
        ]

    @cached_property
    @file_cache(
        path_attr="self.monster_data_path",
        overwrite_attr="self.overwrite",
    )
    def monster_data(self) -> list[dict[str, Any]]:
        return [
            self.scrape_monster(monster)
            for monster in self.monster_links
        ]

    @cached_property
    @file_cache(
        path_attr="self.quest_links_path",
        overwrite_attr="self.overwrite",
    )
    def quest_links(self) -> list[str]:
        return self.scrape_quest_links()

    @cached_property
    @file_cache(
        path_attr="self.monster_links_path",
        overwrite_attr="self.overwrite",
    )
    def monster_links(self) -> list[str]:
        return self.scrape_monster_links()

    def scrape(self) -> list[QuestObject]:
        return [
            QuestObject(
                title=quest["title"],
                quest_id=quest.get("id_"),
                game=self.game,
                generation=self.generation,
                rank=quest.get("rank"),
                level=quest.get("level"),
                is_assignment=quest.get("is_urgent"),
                is_event=quest.get("is_event"),
                targets=quest["targets"],
                target_hp=quest.get("targets_hp"),
                reward_zenny=quest.get("zenny"),
                reward_points=quest.get("hr_points"),
            )
            for quest in self.quest_data
            if quest.get("hub") in {"Village", "Hub"}
        ]

    def scrape_quest(self, link: str) -> dict[str, Any]:
        soup = self.retrieve_soup(link)

        if not isinstance(soup, BeautifulSoup):
            raise AttributeError(f"Quest URL not working: {link}")

        header_tag = soup.find("h2", string=True)

        if not isinstance(header_tag, Tag):
            raise AttributeError(
                f"Quest page has no valid header: {link}"
            )

        header_text = header_tag.get_text(strip=True)
        header_data = self._match_header(header_text)

        tag_div = header_tag.find_next("div")

        if not isinstance(tag_div, Tag):
            raise AttributeError(
                f"Quest page has no valid quest data container: {link}"
            )

        reward_tag = header_tag.find_next(
            "div",
            class_="card-footer text-muted",
        )

        if not isinstance(reward_tag, Tag):
            raise AttributeError(
                f"Quest page has no reward information: {link}"
            )

        reward_raw = reward_tag.get_text().split("/")

        rewards = [
            float(match.group(1).replace(",", ""))
            for reward in reward_raw
            if (
                match := re.search(
                    r"([\d,]+\.?\d*)",
                    reward,
                )
            ) is not None
        ]

        if len(rewards) < 3:
            raise AttributeError(
                f"Quest page has incomplete reward information: {link}"
            )

        monster_header = soup.find("h5", string="Monster")

        monster_hp: dict[str, float] = {}

        if isinstance(monster_header, Tag):
            monster_table = monster_header.find_next(
                "div",
                class_="row",
            )

            if isinstance(monster_table, Tag):
                for row in monster_table.find_all("tr"):
                    monster = row.find(
                        "a",
                        href=True,
                        string=True,
                    )

                    if not isinstance(monster, Tag):
                        continue

                    hp_cell = row.find(
                        lambda tag: (
                            isinstance(tag, Tag)
                            and tag.name == "td"
                            and bool(tag.get_text())
                            and "HP" in tag.get_text()
                        )
                    )

                    if not isinstance(hp_cell, Tag):
                        continue

                    match = re.search(
                        r"([\d,]+\.?\d*)",
                        hp_cell.get_text(),
                    )

                    if match is None:
                        continue

                    monster_hp[monster.get_text(strip=True)] = float(
                        match.group(1).replace(",", "")
                    )

        map_link = tag_div.find(
            "a",
            href=True,
            string=True,
        )

        if not isinstance(map_link, Tag):
            raise AttributeError(
                f"Quest page has no map information: {link}"
            )

        return {
            "id_": link.rstrip("/").split("/")[-1],
            "title": header_data.get("title"),
            "rank": header_data.get("rank"),
            "level": header_data.get("level"),
            "hub": header_data.get("hub"),
            "map": map_link.get_text(strip=True),
            "is_urgent": tag_div.find(
                "span",
                string="Urgent",
            ) is not None,
            "is_key": tag_div.find(
                "span",
                string="Key",
            ) is not None,
            "is_event": "DLC" in header_text,
            "targets": list(monster_hp),
            "targets_hp": monster_hp,
            "zenny": rewards[0],
            "points": rewards[1],
            "hr_points": rewards[2],
        }

    def _match_header(self, header: str) -> dict[str, str | int]:
        header_match = re.search(
            r"(\w+)\s(G?\d+★?) // (.*)",
            header,
        )

        if header_match is None:
            hub, title = header.split("//", maxsplit=1)
            rank = "unknown"
            level = 0
        else:
            hub = header_match.group(1)
            rank_tag = header_match.group(2)
            title = header_match.group(3)

            level_match = re.search(r"(\d+)", rank_tag)
            level = int(level_match.group(1)) if level_match else 0

            rank = "G"
            is_village = "Village" in hub

            if is_village:
                rank = "HR" if level > 6 else "LR"
            elif "G" not in rank_tag:
                rank = "HR" if level > 3 else "LR"

        return {
            "title": title.strip(),
            "hub": hub.strip(),
            "rank": rank,
            "level": level,
        }

    def scrape_monster(self, link: str) -> dict[str, Any]:
        soup = self.retrieve_soup(link, polite=False)

        size_header = soup.find(
            "h5",
            string=re.compile("Size"),
        )

        size_text = (
            size_header.get_text(strip=True)
            if isinstance(size_header, Tag)
            else ""
        )

        size = None
        match = re.search(
            r"([\d,]+\.?\d*)",
            size_text,
        )

        if match:
            size = float(match.group(1).replace(",", ""))

        map_header = soup.find(
            "h5",
            string="Map List",
        )

        maps: list[str] = []

        if isinstance(map_header, Tag):
            map_table = map_header.find_next("table")

            if isinstance(map_table, Tag):
                maps = [
                    map_.get_text(strip=True)
                    for map_ in map_table.find_all(
                        "a",
                        href=True,
                    )
                    if map_.get_text(strip=True)
                ]

        name_header = soup.find(
            "h2",
            string=True,
        )

        if not isinstance(name_header, Tag):
            raise AttributeError(
                f"Monster page has no valid name: {link}"
            )

        return {
            "name": name_header.get_text(strip=True),
            "size": size,
            "maps": maps,
            "quests": self._scrape_quest_links_for_monster(soup),
        }

    def scrape_quest_links(self) -> list[str]:
        quest_links: set[str] = set()

        for link in self.monster_links:
            soup = self.retrieve_soup(link)

            if not isinstance(soup, BeautifulSoup):
                continue

            quest_links.update(
                self._scrape_quest_links_for_monster(soup)
            )

        return list(quest_links)

    def _scrape_quest_links_for_monster(
        self,
        soup: BeautifulSoup,
    ) -> list[str]:
        header = soup.find(
            "h5",
            string="Quest List",
        )

        if not isinstance(header, Tag):
            return []

        table = header.find_next("table")

        if not isinstance(table, Tag):
            return []

        return [
            href
            for link in table.find_all(
                "a",
                href=True,
            )
            if isinstance(href := link.get("href"), str)
        ]

    def scrape_monster_links(self) -> list[str]:
        soup = self.retrieve_soup(self.KIRANICO_URL)

        if not isinstance(soup, BeautifulSoup):
            return []

        header = soup.find(
            "p",
            string="Monster",
        )

        if not isinstance(header, Tag):
            return []

        table = header.find_next("table")

        if not isinstance(table, Tag):
            return []

        return [
            href
            for cell in table.find_all(
                "a",
                href=True,
            )
            if isinstance(href := cell.get("href"), str)
        ]