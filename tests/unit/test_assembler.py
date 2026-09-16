import pandas as pd
from src.features.feature_assembler import FeatureAssembler #type:ignore

def test_assember():
    join_key = "join"
    assembler = FeatureAssembler()

    target = pd.DataFrame({
        join_key: ["id_1", "id_2", "id_3"],
        "val_1": [1, 2, 3],
    })

    source_1 = pd.DataFrame({
        join_key: ["id_1", "id_2", "id_3"],
        "val_2": ["a", "b", "c"],
    })
    source_2 = pd.DataFrame({
        join_key: ["id_1", "id_2", "id_3", "id_4"],
        "val_3": ["one", "two", "three", "four"],
    })

    actual = assembler.assemble(
        target=target,
        sources=[source_1, source_2],
        on=join_key
    )

    expected = pd.DataFrame({
        join_key: ["id_1", "id_2", "id_3"],
        "val_1": [1, 2, 3],
        "val_2": ["a", "b", "c"],
        "val_3": ["one", "two", "three"]
    })

    pd.testing.assert_frame_equal(actual, expected)