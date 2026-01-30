from pathlib import Path

from PySide6 import QtCore, QtWidgets


class DiagnosticsDialog(QtWidgets.QDialog):
    def __init__(self, log_path: Path, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.setMinimumSize(600, 400)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        if log_path.exists():
            self.text.setPlainText(log_path.read_text(encoding="utf-8", errors="ignore"))
        else:
            self.text.setPlainText("No diagnostics available yet.")

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
