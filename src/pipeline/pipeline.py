from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score

from ...src.core.dataclasses import RankingObject, QuestObject, WikiObject
from ...src.core.interfaces import Model
from ...src.data_collection.scrapers import QuestScraper, WikiScraper, RankingScraper
from ...src.data_collection.repositories import LocalCsvRepository
from ...src.features import CrossGameNormalizer, FeatureAssembler, QuestFeatureBuilder

class Pipeline():
    """Class orchestrating the full pipeline, from scraping to model training."""
    
    def __init__(
            self,
            quest_scraper: QuestScraper,
            wiki_scraper: WikiScraper,
            ranking_scraper: RankingScraper,
            normalizer: CrossGameNormalizer,
            quest_feature_builder: QuestFeatureBuilder,
            assembler: FeatureAssembler,
            model: Model,
            repository: LocalCsvRepository,
            ) -> None:

        # Init scrapers
        self.ranking_scraper = ranking_scraper
        self.quest_scraper = quest_scraper
        self.wiki_scraper = wiki_scraper

        # Init feature engineering
        self.normalizer = normalizer
        self.quest_feature_builder = quest_feature_builder
        self.assembler = assembler

        # Init model
        self.model = model

        # Init data storage
        self.repository = repository

    def run(self) -> dict[str, float]:
        """Function calling the full pipeline."""

        # 1. Get data        
        ranking_data = self.ranking_scraper.scrape()
        quest_data = self.quest_scraper.scrape()
        wiki_data = self.wiki_scraper.scrape()

        # 2. Data augmentation
        df = self._feature_engineering(
            _ranking_data = ranking_data,
            _quest_data = quest_data,
            _wiki_data = wiki_data,
        )

        # 3. Split data
        X, y = self._split_target(df=df, target="rank")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 4. Model fit and predict
        self.model.fit(X_train, y_train) 
        predict = self.model.predict(X_test)

        # 5. Model evaluation
        return self._evaluate_mode(y_test=y_test, y_pred=predict)

    def _evaluate_mode(
            self,
            y_test: pd.Series,
            y_pred: pd.Series,
    ) -> dict[str, float]:

        return {
            "rmse": root_mean_squared_error(y_true=y_test, y_pred=y_pred),
            "r2": r2_score(y_true=y_test, y_pred=y_pred)
        }
        
    def _feature_engineering(
            self,
            _ranking_data: list[RankingObject],
            _quest_data: list[QuestObject],
            _wiki_data: list[WikiObject],
        ) -> pd.DataFrame:
        """Apply all transformers to data, aggregate and return the final, ready-to-fit DF."""

        df_ranking = pd.DataFrame(_ranking_data)
        df_quest = pd.DataFrame(_quest_data)
        df_wiki = pd.DataFrame(_wiki_data)

        df = self.assembler.assemble(
            target=df_ranking,
            sources=[
                df_quest,
                df_wiki,
            ]
        )

        df_normalized = self.normalizer.fit_transform(df)

        df_final = self.quest_feature_builder.transform(df_normalized)

        return df_final

    def _split_target(
            self,
            df: pd.DataFrame,
            target: str,
    ) -> tuple[pd.DataFrame, pd.Series]:
        
        y = df["target"]
        X = df.drop([target], axis=1)

        return X, y