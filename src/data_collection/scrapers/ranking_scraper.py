import itertools
import logging
import yaml
from functools import cached_property
from pathlib import Path
from typing import List

from src.core.dataclasses import RankingObject #type:ignore
from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.helpers import file_cache #type:ignore

logger = logging.getLogger(__name__)

class RankingScraper(AbstractWebScraper[RankingObject]):
    """Scrapes monster names and rankings from MH 20th anniversary website."""

    def __init__(
            self,
            url: str,
            out_path: str,
            meta_path: str,
    ) -> None:
        self.url = url

        base_dir = Path(__file__).resolve().parent
        self.out_path = base_dir / out_path / "subsets"
        self.meta_path = base_dir / meta_path

    @cached_property
    @file_cache("self.out_path")
    def ranking_data(self) -> List[RankingObject]:
        return self.scrape()

    def scrape(self) -> List[RankingObject]:
        logger.info("Start scraping Official Capcom Fan Ranking.")

        rankings = []
        rankings.extend(self.get_top_3())
        rankings.extend(self.get_4_to_228())

        return rankings
    
    def get_top_3(self) -> List[RankingObject]:
        with open(self.meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

        top_3_data = meta["monster_metadata"]["top_3"]

        top_3 = [
            {"monster_name": top_3_data.get(1), "rank": 1},
            {"monster_name": top_3_data.get(2), "rank": 2},
            {"monster_name": top_3_data.get(3), "rank": 3}
            ]

        return [RankingObject(**entry) for entry in top_3]
    
    def get_4_to_228(self) -> List[RankingObject]:
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

                top_4_to_bottom.append(RankingObject(**rank_dict))

            except AttributeError:
                logger.warning(f"No text found!")

        logger.info(f"Ranks 4 to 229 successfully scraped! {len(top_4_to_bottom)} items scraped.")
        return top_4_to_bottom