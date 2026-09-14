import numpy as np
import pandas as pd
from functools import cached_property
from typing import List

class Aggregator:
    """Transforms data from df_source and joins onto df_target."""

    def __init__(self, df_target: pd.DataFrame, df_source: pd.DataFrame):
        self.df_target = df_target
        self.df_source = df_source

    @cached_property
    def df_source_exploded(self) -> pd.DataFrame:
        return self.explode_source()

    def aggregate(self) -> pd.DataFrame:
        """Aggregate quest data per monster, average and join to monster data. Return monster data with quest features."""

        general_features = (
            self.df_source_exploded
            .groupby("monster")
            .agg(
                game_appearances=("game", "nunique"),
                quest_appearances=("quest", "nunique"),
                assignment_ratio=("is_assignment", "mean"),
                event_ratio=("is_event", "mean"),
            )
        )
        print("GENERAL FEATURES")
        print(general_features)

        features_by_rank = (
            self.df_source_exploded
            .groupby(["monster", "rank"])
            .agg(
                mean_reward=("reward_zenny", "mean"),
                mean_points=("reward_points", "mean"),
                mean_hp=("monster_hp", "mean"),
            )
            .unstack("rank")
        )
        print("\n")
        print("FEATURES BY RANK")
        print(features_by_rank)

        features_by_rank.columns = [ #type:ignore
            f"{feature}_{rank}"
            for feature, rank in features_by_rank.columns #type:ignore
        ]

        quest_features = general_features.join(features_by_rank)

        return self.df_target.join(quest_features)
    
    def explode_source(self) -> pd.DataFrame:
        """Explode quest targets into one row per quest-monster relationship."""
        df = self.df_source.copy()
        df["n_targets"] = df["targets"].str.len()

        df_transformed = (
            df
            .explode("targets")
            .drop_duplicates(subset=["quest", "targets"])
            .rename(columns={"targets": "monster"})
            .reset_index(drop=True)
        )

        df_transformed["monster_hp"] = df_transformed.apply(self._get_hp, axis=1,)

        df_transformed.drop(["target_hp"], axis=1, inplace=True)

        return df_transformed

    def _get_hp(self, row: pd.Series) -> int:
        target_hp = row.get("target_hp")
        monster_name = row.get("monster")

        if isinstance(target_hp, dict) and monster_name in target_hp:
            return target_hp[monster_name]
        return 0 