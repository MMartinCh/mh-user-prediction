import pandas as pd

class FeatureAssembler:
    """Class merging source dfs to target df on key."""

    def assemble(
            self,
            target: pd.DataFrame,
            sources: list[pd.DataFrame],
            on: str = "monster",
    ) -> pd.DataFrame:

        result = target.copy()

        for df in sources:
            result = result.join(
                df.set_index(on),
                on=on,
                how="left"
            )

        return result
