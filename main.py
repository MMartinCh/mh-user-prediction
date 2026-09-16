import logging
import sys

from src.core.utils.load_config import load_config
from src.pipeline import build_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    
    config = load_config()

    pipeline = build_pipeline(config)

    results = pipeline.run()

    print(results)
