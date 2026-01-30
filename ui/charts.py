from __future__ import annotations

from typing import Dict, List, Tuple

import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets


class ChartPanel(QtWidgets.QWidget):
    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(title)
        self.combo = QtWidgets.QComboBox()
        self.combo.setMinimumWidth(160)
        header.addWidget(self.label)
        header.addStretch()
        header.addWidget(self.combo)

        self.plot = pg.PlotWidget(background=None)
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setMenuEnabled(False)

        layout.addLayout(header)
        layout.addWidget(self.plot)

    def set_channels(self, channels: List[str]) -> None:
        self.combo.clear()
        self.combo.addItems(channels)

    def set_data(self, data: Tuple[List[float], List[float]]) -> None:
        self.plot.clear()
        times, values = data
        if not times:
            return
        self.plot.plot(times, values, pen=pg.mkPen("#0f9d58", width=2))


class ChartsArea(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.panels = [
            ChartPanel("Primary"),
            ChartPanel("Secondary"),
            ChartPanel("Attitude"),
        ]

        for panel in self.panels:
            panel.setObjectName("glass-panel")
            panel.setStyleSheet("padding: 12px;")
            layout.addWidget(panel)

    def bind_channels(self, channels: Dict[str, List[Tuple[float, float]]]) -> None:
        available = list(channels.keys())
        for panel in self.panels:
            panel.set_channels(available)

        def update(panel: ChartPanel) -> None:
            name = panel.combo.currentText()
            series = channels.get(name, [])
            times = [item[0] for item in series]
            values = [item[1] for item in series]
            panel.set_data((times, values))

        for panel in self.panels:
            panel.combo.currentTextChanged.connect(lambda _text, p=panel: update(p))
            update(panel)
