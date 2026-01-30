from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "log_trimmer.log"


def setup_logging(base_dir: Optional[Path] = None) -> Path:
    if base_dir is None:
        base_dir = Path.cwd()
    log_dir = base_dir / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_path
