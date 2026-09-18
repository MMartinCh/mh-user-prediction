import itertools
import logging
import yaml
from functools import cached_property
from pathlib import Path
from typing import Any

from config.config_dataclass import RankingScraperConfig, WebSettings #type:ignore
from ....src.core.dataclasses import RankingObject #type:ignore
from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.helpers import file_cache #type:ignore

logger = logging.getLogger(__name__)

class RankingScraper(AbstractWebScraper[RankingObject]):
    """Scrapes monster names and rankings from MH 20th anniversary website."""

    def __init__(
            self,
            config: RankingScraperConfig,
            web_settings: WebSettings,
            metadata_path: Path,
    ) -> None:
        super().__init__(
            url=config.url,
            web_settings=web_settings,
        )

        self.cache_path = config.cache
        self.metadata_path = metadata_path

    @cached_property
    @file_cache("self.cache_path")
    def ranking_data(self) -> list[dict[str, Any]]:
        return self.get_full_ranking()

    def scrape(self) -> list[RankingObject]:
        return [
            self._pack_ranking_object(monster)
            for monster in self.ranking_data
        ]

    def get_full_ranking(self) -> list[dict[str, Any]]:
        rankings = []
        rankings.extend(self._get_top_3())
        rankings.extend(self._get_4_to_228())
        return rankings
    
    def _get_top_3(self) -> list[dict[str, Any]]:
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

        top_3_data = meta["monster_metadata"]["top_3"]

        return [
            {"monster": top_3_data.get(1), "rank": 1},
            {"monster": top_3_data.get(2), "rank": 2},
            {"monster": top_3_data.get(3), "rank": 3}
            ]
    
    def _get_4_to_228(self) -> list[dict [str, Any]]:
        top_4_to_bottom = []

        soup = self.retrieve_soup(self.url)
        ranking = soup.find('div', class_= 'ranking')

        li_top_20_tags = ranking.find_all('li', class_ = 'no-4-18')
        li_bottom_tags = ranking.find_all('li', class_ = 'no-img')

        for li in itertools.chain(li_top_20_tags, li_bottom_tags):
            name_div = li.find('div', class_ = 'name')
            rank_div = li.find('div', class_ = 'no')

            try:
                name = name_div.text.strip()
                rank = int(rank_div.text.split('.')[-1].strip())

                rank_dict = {"monster_name": name, "rank": rank}

                top_4_to_bottom.append(rank_dict)

            except AttributeError:
                logger.warning(f"No text found!")

        logger.info(f"Ranks 4 to 229 successfully scraped! {len(top_4_to_bottom)} items scraped.")
        return top_4_to_bottom

    def _pack_ranking_object(self, data: dict[str, Any]):
        return RankingObject(
            monster=data["monster"],
            rank=data["rank"],
        )