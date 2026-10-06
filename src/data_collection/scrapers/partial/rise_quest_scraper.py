import logging
import re
from functools import cached_property
from typing import Any, Dict, List, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from config.config_dataclass import PartialQuestScraperConfig, WebSettings
from src.core.interfaces import AbstractQuestScraper
from src.core.utils import file_cache 
from src.core.dataclasses import QuestObject

logger = logging.getLogger(__name__)

class RiseQuestScraper(AbstractQuestScraper):
    """Partial Scraper Class that scrapes quest data for MH Rise/ Sunbreak.
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
        self.monster_links_path = config.utils["monster_links"]
        self.quest_links_path = config.utils["quest_links"]
        self.key_quest_path = config.utils["key_quests"]

    BASE_URL = "https://mhrise.mhrice.info/monster.html"
    KEY_QUEST_URL = "https://monsterhunterrise.wiki.fextralife.com/Hub+Quests"

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite"
    )
    def quest_data(self) -> list[dict[str,Any]]:
        return self.scrape_quest_data()

    @cached_property
    @file_cache(
        path_attr="monster_links_path",
        overwrite_attr="overwrite",
    )
    def monster_links(self) -> List[str]:
        return self._scrape_monster_links()

    @cached_property
    @file_cache(
        path_attr="quest_links_path",
        overwrite_attr="overwrite",
    )
    def quest_links(self) -> Set[str]:
        return set(self._scrape_quest_links())

    @cached_property
    @file_cache(
        path_attr="key_quest_path",
        overwrite_attr="overwrite",
        )
    def key_quests(self) -> set[str]:
        return set(self._scrape_key_quests())

    @cached_property
    @file_cache(
        path_attr="monster_data_path",
        overwrite_attr="overwrite",
    )
    def monster_page_data(self) -> dict[str, dict[str, int]]:
        return self.scrape_monster_page_data()

    def scrape(self) -> List[QuestObject]:
        """Get all Quest info for MH Rise/ Sunbreak and return list of structured quest data."""

        return [
            QuestObject(
                title=quest["title"],
                quest_id=quest["id"],
                game=self.game,
                generation=self.generation,
                rank=quest["rank"],
                level=quest["level"],
                is_assignment=quest["is_assignment"],
                is_event=quest["is_event"],
                targets=quest["targets"],
                target_hp=self._calculate_target_hp(quest),
                reward_zenny=quest["reward_zenny"],
                reward_points=quest["reward_rank_points"],
                )
            for quest in self.quest_data
            if quest.get("title") is not None
        ]

    def scrape_monster_page_data(self) -> dict[str, dict[str, int]]:
            """Scrape all data from all data from Monster pages. Save to csv and return df."""

            monster_page_data = {}
            for link in self.monster_links:
                try:
                    soup = self.retrieve_soup(link)
                    assert isinstance(soup, Tag)

                    monster_name = ""
                    header = soup.find("h1")
                    if isinstance(header, Tag):
                        assert isinstance(
                            monster_name_tag := header.find("span", class_="mh-lang", lang="en"),
                            Tag
                        )
                        monster_name = monster_name_tag.text.strip()

                    monster_size = 0.0
                    if isinstance(size_column := soup.find("span", string="Size"), Tag):
                        assert isinstance(size_info := size_column.find_next_sibling("span"), Tag)
                        size = size_info.text.strip()
                        monster_size = float(size.split("(")[0])

                    lr_base_hp, mr_base_hp = 0, 0
                    if isinstance(base_hp_column := soup.find("span", string=re.compile("Base HP")), Tag):
                        assert isinstance(base_hp_tag := base_hp_column.find_next_sibling("span"), Tag)
                        base_hp_info = base_hp_tag.text.strip()
                        hp_from_string = re.findall(r"(?<=R\) )\d+", base_hp_info)
                        lr_base_hp, mr_base_hp = map(int, hp_from_string)
    
                    monster_page_data[monster_name] = {
                        "monster_size": monster_size,
                        "lr_base_hp": lr_base_hp,
                        "mr_base_hp": mr_base_hp
                    }

                except AssertionError as e:
                    logger.warning(
                        "Unfamiliar page structure for url: %s \n Error: %s",
                        link,
                        e
                    )

                except KeyboardInterrupt:
                    logger.warning("RISE MONSTER INFO SCRAPING manually interrupted. Save data to %s", self.cache_path)
                    return monster_page_data

            return monster_page_data

    def scrape_quest_data(self) -> List[Dict[str,Any]]:
        """Get all quest links from specific Monster page and loop through each quest using get_quest_data-function."""
        
        quest_data = []
        for link in self.quest_links:
            try:
                quest_data.append(self._extract_quest_data(link))

            except (AttributeError, AssertionError) as e:
                logger.warning(
                    "Different data structure for %s \n Error: %s",
                    link,
                    e
                )

            except KeyboardInterrupt:
                logger.warning(f"RISE QUEST SCRAPING manually interrupted. Save data to {self.cache_path}.")
                return quest_data

        return quest_data

    def _extract_quest_data(self, link: str) -> dict[str, Any]:
        soup = self.retrieve_soup(link)
        assert isinstance(soup, Tag)

        quest_id_match = re.search(r"(\d+).html", link)
        quest_id = quest_id_match.group(1) if quest_id_match else None

        quest_title = ""
        if isinstance(
            quest_title_tag := soup.select_one("span.lang-default.mh-lang[lang='en'] span"), 
            Tag
        ):
            quest_title = quest_title_tag.text.strip()

        quest_rank, quest_level = "", 0
        is_event = False
        if isinstance(header := soup.find("h1"), Tag):
            assert isinstance(category_tag := header.find("span", class_=True), Tag)
            quest_category = category_tag.text.strip()

            if match := re.search(r"(?P<rank>[a-zA-Z]+)(?P<level>\d+)", quest_category):
                quest_rank = "LR" if (qr := match.group("rank").upper()) == "VI" else qr
                quest_level = match.group("level")

            is_event = header.find("span", class_="mh-quest-event tag") is not None

        reward_zenny, reward_rank_points = 0, 0
        if isinstance(basic_info := soup.find("section", id="s-basic"), Tag):
            reward_zenny = int(basic_info.find("span", string=re.compile("Reward money")).find_next_sibling("span").text.replace("z","").strip()) # HACK: use regex #type:ignore
            reward_rank_points = int(basic_info.find("span", string=re.compile("Reward rank point")).find_next_sibling("span").text.replace("z","").strip()) #type:ignore

        targets_hp_scaling = {}
        if isinstance(target_section := soup.find("section", id="s-stats"), Tag):
            target_table = target_section.find("tbody")

            targets_hp_scaling = {
                name_span.get_text().strip(): float(match.group(1))
                for row in target_table.select("tr:has(div.mh-quest-monster > span.is-primary.tag)") #type:ignore
                if (tag := row.select_one("div.mh-quest-monster > span.is-primary.tag")) and "Target" in tag.get_text()
                if (name_span := row.select_one("span.lang-default.mh-lang[lang='en']")) is not None
                if (match := next((m for td in row.find_all("td")[1:] if (m := re.search(r"x(\d+\.\d+)", td.get_text()))), None)) is not None
            }

        is_assignment = quest_title in self.key_quests

        if quest_rank == "A":
            logger.info("Quest skipped for Anomaly Quest: %s", link)
            return {}

        return {
            "id": quest_id,
            "title": quest_title,
            "rank": quest_rank,
            "level": quest_level,
            "reward_zenny": reward_zenny,
            "reward_rank_points": reward_rank_points, 
            "targets": list(targets_hp_scaling.keys()),
            "targets_hp_scaling": targets_hp_scaling,
            "is_assignment": is_assignment,
            "is_event": is_event,
            "is_village_quest": quest_rank == "VI"
        }

    def _calculate_target_hp(self, quest_data: dict[str, Any]) -> dict[str, int]:
        """Read target hp scaling from table, multiply with base hp and return dict of targets and their quest hp."""
        targets_hp_scaling: dict[str, int] = quest_data.get("targets_hp_scaling", "{}")
        quest_rank = quest_data.get("quest_rank", "")
        quest_rank = "LR" if quest_rank != "MR" else quest_rank

        targets_final_hp = {}
        for target, scaling in targets_hp_scaling.items():
            target_data: Dict[str, int] = self.monster_page_data.get(target, {})
            target_base = target_data.get(f"{quest_rank.lower()}_base_hp", None)
            if not target_base:
                continue

            targets_final_hp[target] = target_base * scaling

        return targets_final_hp

    def _scrape_monster_links(self) -> list[str]:
        """"Find all Monster page links from Monster overview page."""
        
        soup = self.retrieve_soup(self.BASE_URL)
        assert isinstance(soup, BeautifulSoup)

        monster_table = soup.find("ul", class_="mh-list-monster")
        if not isinstance(monster_table, Tag):
            raise AttributeError("Invalid page structure: %s", self.BASE_URL)

        return [
            urljoin(self.BASE_URL, relative_link) 
            for a in monster_table.find_all("a", href=True)
            if isinstance(a, Tag)
            and (relative_link := a.get("href", ""))
            and isinstance(relative_link, str)
        ]

    def _scrape_quest_links(self) -> set[str]:
        """Scrape all quest links through monster pages."""

        quest_links = set()
        for monster in self.monster_links:
            soup = self.retrieve_soup(monster)
            assert isinstance(soup, BeautifulSoup)

            quest_section = soup.find("section", id="s-quest")
            assert isinstance(quest_section, Tag)

            quest_rows = quest_section.select("tr:not(.mh-non-target):not(.mh-hidden) a[href^='quest/']") 

            found_links = [
                link.strip()
                for a in quest_rows 
                if isinstance(a, Tag)
                and isinstance(relative_link := a.get("href", ""), str)
                and (link := urljoin(self.BASE_URL, relative_link))
                
            ]

            quest_links.update(found_links)

        return quest_links

    def _scrape_key_quests(self) -> set[str]:
        """Scrape all key quests from Fextralife Wiki, if not previously initiated and save."""
        
        soup = self.retrieve_soup(self.KEY_QUEST_URL)
        assert isinstance(soup, BeautifulSoup)

        key_quest_tags = soup.select("p:has(img[title='key_quests_mhrise_wiki_guide_50px']) a")
        _key_quests = {a.text.strip() for a in key_quest_tags if a.text.strip()}

        return _key_quests 