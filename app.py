from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtWidgets

from core.logging_setup import setup_logging
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> int:
    base_dir = Path.cwd()
    log_path = setup_logging(base_dir)
    app = QtWidgets.QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow(log_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
