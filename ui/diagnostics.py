from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets


class DiagnosticsDialog(QtWidgets.QDialog):
    def __init__(self, log_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        layout = QtWidgets.QVBoxLayout(self)
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        if log_path.exists():
            self.text.setPlainText(log_path.read_text(encoding="utf-8", errors="ignore"))
        else:
            self.text.setPlainText("No diagnostics log found.")

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
