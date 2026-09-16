import pandas as pd

class QuestFeatureBuilder:
    """Transforms raw quest data into monster-level features."""

    def __init__(self, df_quest: pd.DataFrame) -> None:
        self.df_quest = df_quest

    def transform(self) -> pd.DataFrame:
        """Create monster-level features from quest data."""

        df = self.explode_df()

        general_features = self.get_general_features(df)
        rank_features = self.get_rank_features(df)

        return general_features.join(rank_features)

    def get_general_features(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        return (
            df
            .groupby("monster")
            .agg(
                game_appearances=("game", "nunique"),
                quest_appearances=("quest", "nunique"),
                assignment_ratio=("is_assignment", "mean"),
                event_ratio=("is_event", "mean"),
            )
        )

    def get_rank_features(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        features = (
            df
            .groupby(["monster", "rank"])
            .agg(
                mean_reward=("reward_zenny", "mean"),
                mean_points=("reward_points", "mean"),
                mean_hp=("monster_hp", "mean"),
            )
            .unstack("rank")
        )

        assert type(features) == pd.DataFrame

        features.columns = [
            f"{feature}_{rank}"
            for feature, rank in features.columns
        ]

        return features

    def explode_df(self) -> pd.DataFrame:
        """Create one row per quest-monster relationship."""

        df = self.df_quest.copy()

        df["n_targets"] = df["targets"].str.len()

        df = (
            df
            .explode("targets")
            .drop_duplicates(subset=["quest", "targets"])
            .rename(columns={"targets": "monster"})
            .reset_index(drop=True)
        )

        df["monster_hp"] = df.apply(
            self._get_hp,
            axis=1,
        )

        df.drop(columns=["target_hp"], inplace=True)

        return df

    def _get_hp(self, row: pd.Series) -> int:
        target_hp = row["target_hp"]
        monster_name = row["monster"]

        if isinstance(target_hp, dict):
            return target_hp.get(monster_name, 0)

        return 0