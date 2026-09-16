import pandas as pd
from src.features.quest_feature_builder import QuestFeatureBuilder  # type: ignore

df = pd.DataFrame({
    "quest": ["A", "B", "C"],
    "game": ["World", "World", "Rise"],
    "rank": ["LR", "LR", "HR"],
    "targets": [
        ["Rathalos", "Tigrex"],
        ["Rathalos"],
        ["Rathalos", "Rathian"],
    ],
    "target_hp": [
        {"Rathalos": 1000, "Tigrex": 1500},
        {"Rathalos": 1200},
        {"Rathalos": 2000, "Rathian": 1500},
    ],
    "is_assignment": [True, True, False],
    "is_event": [False, True, False],
    "reward_zenny": [150, 100, 300],
    "reward_points": [15, 10, 30],
})

feature_builder = QuestFeatureBuilder(df)

def test_explode_df():
    expected = pd.DataFrame({
        "quest": ["A", "A", "B", "C", "C"],
        "game": ["World", "World", "World", "Rise", "Rise"],
        "rank": ["LR", "LR", "LR", "HR", "HR"],
        "monster": [
            "Rathalos",
            "Tigrex",
            "Rathalos",
            "Rathalos",
            "Rathian",
        ],
        "is_assignment": [True, True, True, False, False],
        "is_event": [False, False, True, False, False],
        "reward_zenny": [150, 150, 100, 300, 300],
        "reward_points": [15, 15, 10, 30, 30],
        "n_targets": [2, 2, 1, 2, 2],
        "monster_hp": [1000, 1500, 1200, 2000, 1500],
    })

    actual = feature_builder.explode_df()

    pd.testing.assert_frame_equal(expected, actual)

def test_general_features():
    df_exploded = feature_builder.explode_df()

    expected = pd.DataFrame(
        {
            "game_appearances": [2, 1, 1],
            "quest_appearances": [3, 1, 1],
            "assignment_ratio": [2 / 3, 0.0, 1.0],
            "event_ratio": [1 / 3, 0.0, 0.0],
        },
        index=pd.Index(
            ["Rathalos", "Rathian", "Tigrex"],
            name="monster",
        ),
    )

    actual = feature_builder.get_general_features(df_exploded)

    pd.testing.assert_frame_equal(expected, actual)

def test_rank_features():
    df_exploded = feature_builder.explode_df()

    expected = pd.DataFrame(
        {
            "mean_reward_HR": [300.0, 300.0, float("nan")],
            "mean_reward_LR": [125.0, float("nan"), 150.0],
            "mean_points_HR": [30.0, 30.0, float("nan")],
            "mean_points_LR": [12.5, float("nan"), 15.0],
            "mean_hp_HR": [2000.0, 1500.0, float("nan")],
            "mean_hp_LR": [1100.0, float("nan"), 1500.0],
        },
        index=pd.Index(
            ["Rathalos", "Rathian", "Tigrex"],
            name="monster",
        ),
    )

    actual = feature_builder.get_rank_features(df_exploded)

    pd.testing.assert_frame_equal(expected, actual)

def test_transform():
    expected = pd.DataFrame(
        {
            "game_appearances": [2, 1, 1],
            "quest_appearances": [3, 1, 1],
            "assignment_ratio": [2 / 3, 0.0, 1.0],
            "event_ratio": [1 / 3, 0.0, 0.0],
            "mean_reward_HR": [300.0, 300.0, float("nan")],
            "mean_reward_LR": [125.0, float("nan"), 150.0],
            "mean_points_HR": [30.0, 30.0, float("nan")],
            "mean_points_LR": [12.5, float("nan"), 15.0],
            "mean_hp_HR": [2000.0, 1500.0, float("nan")],
            "mean_hp_LR": [1100.0, float("nan"), 1500.0],
        },
        index=pd.Index(
            ["Rathalos", "Rathian", "Tigrex"],
            name="monster",
        ),
    )

    actual = feature_builder.transform()

    pd.testing.assert_frame_equal(expected, actual)