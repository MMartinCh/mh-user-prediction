import yaml
from pathlib import Path
from ..dataclasses.config_dataclass import Config

def load_config():
    config_path = Path(__file__).resolve().parent / "config" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return Config(*yaml.safe_load(f))