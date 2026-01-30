from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout


class DiagnosticsDialog(QDialog):
    def __init__(self, log_file: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.resize(560, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Log file: {log_file}"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        button_row = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_row.addStretch(1)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

        if log_file.exists():
            lines = log_file.read_text(errors="ignore").splitlines()[-200:]
            for line in lines:
                self.list_widget.addItem(line)
        else:
            self.list_widget.addItem("No diagnostics available.")
