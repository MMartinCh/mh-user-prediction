import numpy as np
import pandas as pd
from typing import List

from sklearn.base import BaseEstimator, TransformerMixin

class CrossGameNormalizer(BaseEstimator, TransformerMixin):
    def __init__(self, columns_to_normalize: List[str]|None = None):
        self.columns_to_normalize = columns_to_normalize or ["level", "reward_zenny", "reward_points"]
        self.game_stats_ = {}

    def fit(self, X: pd.DataFrame, y=None):
        df = X.copy()

        if "game" not in df.columns:
            raise ValueError("DF must contain 'game' column for normalization!")

        for game, group in df.groupby('game'):
            self.game_stats_[game] = {}
            for col in self.columns_to_normalize:
                if col in group.columns:
                    vals = group[col].astype(float).fillna(0)
                    self.game_stats_[game][col] = {
                        "mean": vals.mean(),
                        "std": vals.std(),
                    }
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        processed_rows = []

        for _, row in df.iterrows():
            row_dict = row.to_dict()
            game = row_dict.get('game', 'unknown')

            for col in self.columns_to_normalize:
                if col in row_dict:
                    val = float(row_dict.get(col, 0.0) or 0.0)

                    if game in self.game_stats_ and col in self.game_stats_[game]:
                        stats = self.game_stats_[game][col]
                        std = stats['std']
                        
                        if std and not np.isnan(std) and std > 0:
                            row_dict[f"{col}_norm"] = (val - stats['mean']) / std
                        else:
                            row_dict[f"{col}_norm"] = 0.0
                    else:
                        row_dict[f"{col}_norm"] = 0.0

            processed_rows.append(row_dict)

        return pd.DataFrame(processed_rows)

    