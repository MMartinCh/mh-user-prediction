import logging
import sys
from pathlib import Path

from config.config_loader import ConfigLoader
from src.pipeline import PipelineFactory

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    BASE_PATH = Path(__file__).resolve().parent
    config_path = BASE_PATH / "config" / "config.yaml"
    
    config_loader = ConfigLoader(path=config_path)
    config = config_loader.load()

    pipeline = PipelineFactory(config)

    results = pipeline.run()

    print(results)
