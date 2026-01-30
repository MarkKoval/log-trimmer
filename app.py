import sys

from PySide6 import QtWidgets

from core.logging_config import setup_logging
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> int:
    setup_logging()
    app = QtWidgets.QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
