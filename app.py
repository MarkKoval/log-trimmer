from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui import MainWindow, Theme


def configure_logging() -> Path:
    log_dir = Path.home() / ".log-trimmer" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_file


def main() -> None:
    log_file = configure_logging()
    app = QApplication([])
    theme = Theme(dark=False)
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow(log_file=log_file)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
