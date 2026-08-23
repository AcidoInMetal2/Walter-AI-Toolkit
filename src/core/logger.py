"""
Central logger.
"""
import logging
from config.paths import LOGS_DIR

LOGS_DIR.mkdir(parents=True,exist_ok=True)

logging.basicConfig(
    filename=LOGS_DIR/"walter.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger=logging.getLogger("WalterAI")
