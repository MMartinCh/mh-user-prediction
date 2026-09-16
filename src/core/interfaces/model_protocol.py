from typing import Any, Protocol

import pandas as pd

class Model(Protocol):
    def fit(self, X: Any, y: Any) -> Any:
        ...

    def predict(self, X: Any) -> Any:
        ...