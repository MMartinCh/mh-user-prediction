import itertools
import logging
import yaml
from functools import cached_property
from pathlib import Path
from typing import Any

from bs4 import Tag

from config.config_dataclass import RankingScraperConfig, WebSettings 
from data.metadata.metadata_class import Metadata
from src.core.dataclasses import RankingObject 
from src.core.interfaces import AbstractWebScraper 
from src.core.utils import file_cache 

logger = logging.getLogger(__name__)

class RankingScraper(AbstractWebScraper[RankingObject]):
    """Scrapes monster names and rankings from MH 20th anniversary website."""

    def __init__(
            self,
            config: RankingScraperConfig,
            web_settings: WebSettings,
            metadata: Metadata,
    ) -> None:
        
        super().__init__(
            cache=config.cache,
            overwrite=config.overwrite,
            url=config.url,
            web_settings=web_settings
        )

        self.metadata = metadata

    @cached_property
    @file_cache(
        path_attr="cache_path",
        overwrite_attr="overwrite",
    )
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
        top_three = self.metadata.top_three_monster

        return [
            {"monster": top_three.get(1), "rank": 1},
            {"monster": top_three.get(2), "rank": 2},
            {"monster": top_three.get(3), "rank": 3}
            ]
    
    def _get_4_to_228(self) -> list[dict [str, Any]]:
        top_4_to_bottom = []
        
        assert self.url is not None
        soup = self.retrieve_soup(self.url)

        if not soup:
            raise ValueError("Url %s invalid or missing.", self.url)

        ranking = soup.find('div', class_= 'ranking')
        assert isinstance(ranking, Tag)

        li_top_20_tags = ranking.find_all('li', class_ = 'no-4-18')
        li_bottom_tags = ranking.find_all('li', class_ = 'no-img')

        for li in itertools.chain(li_top_20_tags, li_bottom_tags):
            assert isinstance(li, Tag)

            name_div = li.find('div', class_ = 'name')
            rank_div = li.find('div', class_ = 'no')

            if name_div and rank_div:
                name = name_div.text.strip()
                rank = int(rank_div.text.split('.')[-1].strip())

                rank_dict = {"monster": name, "rank": rank}

                top_4_to_bottom.append(rank_dict)

        logger.info("Scrape Ranking 4-229 completed. %i items scraped.", len(top_4_to_bottom))
        
        return top_4_to_bottom

    def _pack_ranking_object(self, data: dict[str, Any]):
        return RankingObject(
            monster=data["monster"],
            rank=data["rank"],
        )