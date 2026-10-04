import logging
import re
from functools import cached_property
from typing import Any
from urllib.parse import urljoin

from bs4 import Tag
from bs4.element import NavigableString

from config.config_dataclass import WebSettings, WikiScraperConfig 
from src.core.dataclasses import WikiObject 
from src.core.interfaces import AbstractWebScraper 
from src.core.utils import file_cache 

logger = logging.getLogger(__name__)

class WikiScraper(AbstractWebScraper[WikiObject]):

    def __init__(
            self,
            config: WikiScraperConfig,
            web_settings: WebSettings,
    ) -> None:
        
        super().__init__(
            cache=config.cache,
            overwrite=config.overwrite,
            url=config.url,
            web_settings=web_settings,
        )

        self.monster_links_path = config.utils["monster_links"]

    @cached_property
    @file_cache(
        path_attr="monster_links_path",
        overwrite_attr="overwrite",
    )
    def monster_links(self) -> list[str]:
        return self._get_monster_links()

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
    )
    def wiki_data(self) -> list[dict[str, Any]]:
        return self._scrape_wiki_data()

    def scrape(self) -> list[WikiObject]:
        return [
            monster_data
            for monster in self.wiki_data
            if (monster_data := self._pack_wiki_object(monster))
        ]

    def _scrape_wiki_data(self) -> list[dict[str, Any]]:
        """Scrape all monster data from Monster Hunter Wiki and return as list of structured data."""
        logger.info("Start scraping from MH Wiki...")

        wiki_data = []
        try:
            for link in self.monster_links:
                monster_data = self._get_monster_info(link)
                if monster_data is not None:
                    wiki_data.append(monster_data)
            
            logger.info(f"MH Wiki successfully scraped! {len(wiki_data)} entries collected.")
            
        except KeyboardInterrupt:
            logger.info(f"Manually interrupted with keybord interrupt!")

        return wiki_data

    def _get_monster_info(self, link: str) -> dict[str, Any]:
        """Extract one MHWikiItem for Monster from individual monster page."""

        soup = self.retrieve_soup(link)
        
        name_from_link = (link
                          .split("/")[-1]
                          .replace("_", " ")
                          .strip()
                          )
        
        if soup is None:
            logger.warning(
                "No soup found for %s. Link: %s",            
                name_from_link, 
                link
                )
            return {}

        monster_data = {}
        monster_data["monster"] = name_from_link

        info_table = soup.find("table", class_ = "wikitable monster-game-info")

        if not isinstance(info_table, Tag):
            logger.warning(
                "No Info Table found for %s. Link: %s", 
                name_from_link, 
                link
                )
            return {}

        for attribute in ["Original", "Latest", "Classification"]:
            th_element = info_table.find("th", string=re.compile(attribute, re.IGNORECASE))
            
            if th_element:
                row = th_element.find_parent("tr")
                
                if isinstance(row, Tag) and isinstance(row_a := row.find("a"), Tag):
                    monster_data[attribute.lower()] = row_a.text.strip()

        for attribute in [
            "Elements", 
            "Status Effects", 
            "Weakest To"
        ]:
            row = info_table.find("th", string=re.compile(attribute))
            assert isinstance(row, Tag)

            if row_tr := row.find_parent("tr"):
                assert isinstance(row_tr, Tag)
                containers = row_tr.find_all("span", typeof="mw:File")
                assert isinstance(containers, list)

                elements = []
                for container in containers:
                    assert isinstance(container, Tag)
                    
                    a = container.find("a")
                    assert isinstance(a, Tag)

                    title = a.get("title")
                    assert isinstance(title, str)

                    elements.append(title)              

                    monster_data[attribute.lower()] = elements

        size_table = soup.find(
            "table", 
            class_="wikitable", 
            align="right",
            style="margin: 0rem 0rem 1rem 1rem; max-width:350px; clear:both;",
        )

        assert isinstance(size_table, Tag)

        habitat_rows = size_table.find_all("td", colspan="2")

        monster_data["habitats"] = [
            habitat.text.strip()
            for row in habitat_rows
            if isinstance(row, Tag)
            if (habitat := row.find("a"))
        ]

        labels = []
        label_header = soup.find("h3", string="Categories")
        if label_header:
            label_table = label_header.find_next_sibling("div", class_="mw-portlet-body")
            assert isinstance(label_table, Tag)

            labels = [label.text for label in label_table.find_all("li")]

        for label in [
            "Flagship Monsters", 
            "Subspecies", 
            "Variants", 
            "Deviants", 
            "Rare Species", 
            "Collaboration Monsters", 
            "Final Boss Monsters", 
            "Monsters with Themes"
            ]:
            monster_data[label] = label in labels
        
        logger.info("Data successfully scraped for %s", name_from_link)

        return monster_data

    def _get_monster_links(self) -> list[str]:
        logger.info("Extracting Monster Links from MH Wiki...")
        
        assert isinstance(self.url, str)
        soup = self.retrieve_soup(self.url)
        if soup is None:
            raise AttributeError(f"{self.url} did not return valid Soup.")

        start_headline = soup.find("span", class_="mw-headline", id="Large_Monsters")

        if not start_headline:
            logger.warning("Start headline not found!")
            return []
        
        logger.debug(f"Start headline found: {start_headline}")

        start_h2 = start_headline.find_parent("h2")
        assert isinstance(start_h2, Tag)
        
        scrape_range = []
        for sibling in start_h2.next_siblings:
            assert isinstance(sibling, NavigableString | Tag), f"Sibling Type: {type(sibling)}"

            if sibling.name == "h2":
                break

            if sibling.name is not None:
                scrape_range.append(sibling)

        monster_urls = []
        pattern = re.compile(r"^/wiki/(?!(?:MH[a-zA-Z0-9]*)(?:$|_))([^:]+)$")

        for el in scrape_range:
            a_tag = el.find("a", href=pattern)
            relative_link = a_tag["href"]
            
            if relative_link not in monster_urls:
                complete_link = urljoin(self.url, relative_link)
                monster_urls.append(complete_link)

        logger.debug(f"Monster urls extracted! {len(monster_urls)} elements found.")
    
        return monster_urls

    def _pack_wiki_object(self, data: dict[str, Any]) -> WikiObject | None:
        if data.get("monster") is None:
            return
        
        return WikiObject(
            monster=data["monster"],
            first_appearance=data.get("original"),
            latest_appearance=data.get("latest"),
            classification=data.get("classification"),
            elements=data.get("elements", []),
            ailments=data.get("status effects", []),
            weaknesses=data.get("weakest to", []),
            size=data.get("size"),
            habitats=data.get("habitats", []),
            is_flagship=data.get("Flagship Monsters", False),
            is_subspecies=data.get("Subspecies", False),
            is_variant=data.get("Variants", False),
            is_deviant=data.get("Deviants", False),
            is_rare_species=data.get("Rare Species", False),
            is_collaboration=data.get("Collaboration Monsters", False),
            is_final_boss=data.get("Final Boss Monsters", False),
            has_theme=data.get("Monsters with Themes", False)
            )