import logging
from pathlib import Path


LOG_DIR = Path.home() / ".log_trimmer"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger("pymavlink").setLevel(logging.WARNING)
    return LOG_FILE
