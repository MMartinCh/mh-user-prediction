import logging
import re
from functools import cached_property
from typing import Any
from urllib.parse import urljoin

from config.config_dataclass import WebSettings, WikiScraperConfig #type:ignore
from src.core.dataclasses import WikiObject #type:ignore
from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.helpers import file_cache #type:ignore

logger = logging.getLogger(__name__)

class WikiScraper(AbstractWebScraper[WikiObject]):

    def __init__(
            self,
            config: WikiScraperConfig,
            web_settings: WebSettings,
    ) -> None:
        super().__init__(
            url= config.url,
            web_settings=web_settings,
        )

        self.overwrite = config.overwrite

        self.cache_path = config.cache
        self.monster_links_path = config.utils["monster_links"]

    @cached_property
    @file_cache("self.monster_links_path")
    def monster_links(self) -> list[str]:
        return self._get_monster_links()

    @cached_property
    @file_cache("self.cache_path")
    def wiki_data(self) -> list[dict[str, Any]]:
        return self._scrape_wiki_data()

    def scrape(self) -> list[WikiObject]:
        return [
            self._pack_wiki_object(monster)
            for monster in self.wiki_data
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
        name_from_link = link.split("/")[-1]

        monster_info = {}
        try:
            info_table = soup.find("table", class_ = "wikitable monster-game-info")

            monster_info["monster"] = info_table.find("span", class_ = "custom-gallery").get("data-monster").strip()
            
            for attribute in ["Original", "Latest", "Classification"]:
                row = info_table.find("th", string=re.compile(attribute)).find_parent("tr")
                monster_info[attribute.lower()] = row.find("td").text.strip()

            for attribute in ["Elements", "Status Effects", "Weakest To"]:
                row = info_table.find("th", string=re.compile(attribute)).find_parent("tr")
                containers = row.find_all("span", typeof="mw:File")
                monster_info[attribute.lower()] = [c.find("a").get("title").strip() for c in containers]

            size_table = soup.find("table", class_="wikitable", align="right", style="margin: 0rem 0rem 1rem 1rem; max-width:450px; clear:both;")

            size_dimensions = []
            for attribute in ["Length", "Height", "Foot Size"]:
                row = size_table.find("th", string=re.compile(attribute)).find_parent("tr")
                size_dimensions.append(row.find("td").text)

            monster_info["size"] = size_dimensions

            row_habitats = size_table.find("th", string=re.compile("Habitats")).find_parent("tr").find_next_sibling("tr")
            monster_info["habitats"] = [h.text.strip() for h in row_habitats.find_all("a")]

            label_header = soup.find("h3", string="Categories")
            label_table = label_header.find_next_sibling("div", class_="mw-portlet-body")
            labels = [label.text for label in label_table.find_all("li")]

            for label in ["Flagship Monsters", "Subspecies", "Variants", "Deviants", "Rare Species", "Collaboration Monsters", "Final Boss Monsters", "Monsters with Themes"]:
                monster_info[label] = label in labels
            
            logger.info(f"Data successfully scraped for {name_from_link}")

        except AttributeError as e:
            logger.warning(f"Attribute not found: {e}. Article suspected as category headline: {name_from_link}")

        return monster_info

    def _get_monster_links(self) -> list[str]:
        logger.info("Extracting Monster Links from MH Wiki...")
        soup = self.retrieve_soup(self.url)
        start_headline = soup.find("span", class_="mw-headline", id="Large_Monsters")

        if not start_headline:
            logger.warning("Start headline not found!")
            return []
        
        logger.debug(f"Start headline found: {start_headline}")

        start_h2 = start_headline.find_parent("h2")
        
        scrape_range = []
        for sibling in start_h2.next_siblings:
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

    def _pack_wiki_object(self, data: dict[str, Any]) -> WikiObject:
        return WikiObject(
            monster=data["monster"],
            first_appearance=data.get("original"),
            latest_appearance=data.get("latest"),
            classification=data.get("classification"),
            elements=data.get("elements", []),
            ailments=data.get("status effects", []),
            weaknesses=data.get("weakest to", []),
            size=data["size"],
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