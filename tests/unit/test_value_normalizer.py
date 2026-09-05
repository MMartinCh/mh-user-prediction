import pytest
import numpy as np
import pandas as pd

from src.core.transformers.cross_game_normalizer import CrossGameNormalizer

def test_normalizer():
    """Test CrossGameNormalizer on sample data."""

    sample = pd.DataFrame({
        "game": ["A", "A", "A", "B", "B", "B"],
        "level": [1, 2, 3, 10, 20, 30]
    })

    normalizer = CrossGameNormalizer(
        columns_to_normalize=["level"]
    )
    normalizer.fit(sample)

    assert normalizer.game_stats_["A"]["level"]["mean"] == 2
    assert normalizer.game_stats_["A"]["level"]["std"] == 1

    assert normalizer.game_stats_["B"]["level"]["mean"] == 20
    assert normalizer.game_stats_["B"]["level"]["std"] == 10

    results = normalizer.transform(sample)
    expected = [-1, 0, 1, -1, 0, 1]

    np.testing.assert_allclose(
        results["level_norm"],
        expected
    )


