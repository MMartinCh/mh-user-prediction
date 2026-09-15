from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ...src.core.dataclasses import RankingObject, QuestObject, WikiObject
from ...src.data_collection.scrapers import QuestScraper, WikiScraper, RankingScraper
from ...src.data_collection.repositories import LocalCsvRepository
from ...src.features import Aggregator, CrossGameNormalizer

class Pipeline():
    """Class orchestrating the full pipeline, from scraping to model training."""
    
    def __init__(
            self,
            quest_scraper: QuestScraper,
            wiki_scraper: WikiScraper,
            ranking_scraper: RankingScraper,
            aggregator: Aggregator,
            normalizer: CrossGameNormalizer,
            repository: LocalCsvRepository,
            config = Dict[str, Any],
            ) -> None:

        # Init scrapers
        self.ranking_scraper = ranking_scraper
        self.quest_scraper = quest_scraper
        self.wiki_scraper = wiki_scraper

        # Init feature engineering
        self.aggregator = aggregator
        self.normalizer = normalizer

        # Init data storage
        self.repository = repository
        self.outpath = config["paths"]["outpath"]

        # Settings
        self.scraper_settings = config["scraper_settings"]
        self.model_settings = config["model_settings"]

    def pipeline(self) -> None:
        """Function calling the full pipeline."""

        # Get data        
        ranking_data = self.ranking_scraper.scrape()
        quest_data = self.quest_scraper.scrape()
        wiki_data = self.wiki_scraper.scrape()

        # Aggregate data as unified dataset
        df = self._feature_engineering(
            _ranking_data = ranking_data,
            _quest_data = quest_data,
            _wiki_data = wiki_data,
        )

        # Model fit
        predictor = self._train_model()

        # Model evaluation
        model_benchmark = self._evaluate_model()

    def _feature_engineering(
            self,
            _ranking_data: List[RankingObject],
            _quest_data: List[QuestObject],
            _wiki_data: List[WikiObject],
        ) -> np.ndarray:
        """Apply all transformers to data, aggregate and return the final, ready-to-fit DF."""
        df_ranking = pd.DataFrame(_ranking_data)
        df_quest = pd.DataFrame(_quest_data)
        df_wiki = pd.DataFrame(_wiki_data)

        df_aggregate = self.aggregator.aggregate(
            df_target = df_ranking,
            source_dfs = [
                df_quest,
                df_wiki
            ]
        )

        df_final = self.normalizer.fit_transform(df_aggregate)

        return df_final

    def _train_model(self):
        """Train ML model with config settings."""
        pass

    def _evaluate_model(self):
        """Evaluate trained model."""
        pass