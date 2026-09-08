import logging
import sys
from pathlib import Path

import pandas as pd

from src.data_collection.scrapers import MHWikiScraper, RankingScraper, CompleteQuestScraper
from src.data_collection.scrapers.ranking_scraper import RankingScraper
from src.data_collection.repositories import DataMerger, LocalCsvRepository
from src.core.transformers.cross_game_normalizer import CrossGameNormalizer
from src.core.features.aggregator import Aggregator

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    # initialize paths and logger
    DATA_PATH = Path(__file__).resolve().parent / "data"
    monster_path = DATA_PATH / "subsets" / "attempt_merge.csv"
    quest_path = DATA_PATH / "quest_data.csv"

    logger = logging.getLogger(__name__)

    # read dfs
    df_monster = pd.read_csv(monster_path)
    df_quest = pd.read_csv(quest_path)

    # feature engineering
    normalizer = CrossGameNormalizer()
    df_quest_normalized = pd.DataFrame(
        normalizer.fit_transform(df_quest)
        )
    print(df_quest_normalized)

    aggregator = Aggregator(
        df_target=df_monster,
        df_source=df_quest_normalized,
    )
    df_aggregated = aggregator.aggregate()

    # save df
    repository = LocalCsvRepository()
    repository.save(
        monsters=df_aggregated,
        path=DATA_PATH,
        file_name="test_aggregate.csv"
    )

    logger.info(f"Aggregated test df saved to {DATA_PATH}.")

