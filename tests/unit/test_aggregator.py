import pytest
import pandas as pd
import numpy as np

from src.features.aggregator import Aggregator #type:ignore

def test_explode_source():
    df_target = pd.DataFrame({
        "monster": ["Rathalos", "Rathian", "Fatalis"],
        "type" : ["Flying", "Flying", "Elder"]
    })

    df_source = pd.DataFrame({
        "quest": ["quest_1", "quest_2", "quest_3"],
        "game": ["FU", "Tri", "Four"],
        "targets": [
            ["Rathalos", "Rathalos"], 
            ["Rathalos", "Rathian"], 
            ["Fatalis"]
        ],
        "target_hp": [
            {"Rathalos": 1000},
            {"Rathalos": 1000, "Rathian": 800}, 
            {"Fatalis": 3000}
        ],
        "reward" : [1000, 2000, 3000],
    })

    aggregator = Aggregator(df_target, df_source)

    df_source_explode = aggregator.df_source_exploded

    expected = pd.DataFrame({
        "monster": ["Rathalos", "Rathalos", "Rathian", "Fatalis"],
        "quest": ["quest_1", "quest_2", "quest_2", "quest_3"],
        "game": ["FU", "Tri", "Tri", "Four"],
        "monster_hp": [1000, 1000, 800, 3000],
        "n_targets": [2, 2, 2, 1],
        "reward": [1000, 2000, 2000, 3000],
    })

    pd.testing.assert_frame_equal(df_source_explode, expected, check_like=True)

def test_aggregate():
    df_target = pd.DataFrame({
        "type": ["Flying", "Flying", "Elder"]
    }, index=["Rathalos", "Rathian", "Fatalis"])

    df_source = pd.DataFrame({
        "quest": ["quest_1", "quest_2", "quest_3", "quest_4"],
        "game": ["FU", "Tri", "Tri", "Four"],
        "generation": [2, 3, 3, 4],
        "targets": [
            ["Rathalos"],
            ["Rathalos", "Rathian"],
            ["Rathalos"],
            ["Fatalis"],
        ],
        "target_hp": [
            {"Rathalos": 1000},
            {"Rathalos": 1200, "Rathian": 800},
            {"Rathalos": 1400},
            {"Fatalis": 3000},
        ],
        "is_assignment": [True, True, False, True],
        "is_event": [False, False, True, False],
        "rank": ["LR", "HR", "HR", "MR"],
        "reward_zenny": [1000, 2000, 3000, 5000],
        "reward_points": [10, 20, 30, 50],
    })

    aggregator = Aggregator(df_target, df_source)

    actual = aggregator.aggregate()

    expected = pd.DataFrame({
        "type": [ "Flying", "Flying", "Elder"],
        "game_appearances": [2, 1, 1],
        "quest_appearances": [3, 1, 1],
        "assignment_ratio": [2 / 3, 1.0, 1.0],
        "event_ratio": [1 / 3, 0.0, 0.0],
        "mean_reward_LR": [1000.0, np.nan, np.nan],
        "mean_points_LR": [10.0, np.nan, np.nan],
        "mean_hp_LR": [1000.0, np.nan, np.nan],
        "mean_reward_HR": [2500.0, 2000.0, np.nan],
        "mean_points_HR": [25.0, 20.0, np.nan],
        "mean_hp_HR": [1300.0, 800.0, np.nan],
        "mean_reward_MR": [np.nan, np.nan, 5000.0],
        "mean_points_MR": [np.nan, np.nan, 50.0],
        "mean_hp_MR": [np.nan, np.nan, 3000.0],
    }, index=["Rathalos", "Rathian", "Fatalis"])

    pd.testing.assert_frame_equal(actual, expected, check_like=True)
