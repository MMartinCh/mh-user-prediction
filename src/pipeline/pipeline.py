import yaml
from pathlib import Path

class Pipeline():
    """Class orchestrating the full pipeline, from scraping to model training."""
    
    def __init__(self, config_path: Path) -> None:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)["default"]
            paths = yaml.safe_load(f)["paths"]

        self.overwrite = config["overwrite"]
        self.outpath = paths["out"]