import pandas as pd


class QuestFeatureBuilder:
    """Transforms raw quest data into monster-level features."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create monster-level features from quest data."""

        df_exploded = self.explode_df(df)

        general_features = self.get_general_features(df_exploded)
        rank_features = self.get_rank_features(df_exploded)

        return general_features.join(rank_features)

    def get_general_features(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        return df.groupby("monster").agg(
            game_appearances=("game", "nunique"),
            quest_appearances=("quest", "nunique"),
            assignment_ratio=("is_assignment", "mean"),
            event_ratio=("is_event", "mean"),
        )

    def get_rank_features(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        features = (
            df.groupby(["monster", "rank"])
            .agg(
                mean_reward=("reward_zenny", "mean"),
                mean_points=("reward_points", "mean"),
                mean_hp=("monster_hp", "mean"),
            )
            .unstack("rank")
        )

        assert isinstance(features, pd.DataFrame)

        features.columns = [
            f"{feature}_{rank}" for feature, rank in features.columns
        ]

        return features

    def explode_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create one row per quest-monster relationship."""
        # Work on a copy to avoid mutating the original input DataFrame
        df_work = df.copy()
        df_work["n_targets"] = df_work["targets"].str.len()

        df_exploded = (
            df_work.explode("targets")
            .drop_duplicates(subset=["quest", "targets"])
            .rename(columns={"targets": "monster"})
            .reset_index(drop=True)
        )

        # Apply over df_exploded where the 'monster' column exists
        df_exploded["monster_hp"] = df_exploded.apply(
            self._get_hp,
            axis=1,
        )

        df_exploded.drop(columns=["target_hp"], inplace=True)

        return df_exploded

    def _get_hp(self, row: pd.Series) -> int:
        target_hp = row["target_hp"]
        monster_name = row["monster"]

        if isinstance(target_hp, dict):
            return target_hp.get(monster_name, 0)

        return 0