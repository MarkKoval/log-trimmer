from __future__ import annotations

from typing import Dict, Tuple

import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets


class TimelinePlot(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plot = pg.PlotWidget(title="Timeline")
        self.plot.showGrid(x=True, y=False, alpha=0.3)
        self.region = pg.LinearRegionItem(values=(0, 1))
        self.plot.addItem(self.region)
        layout.addWidget(self.plot)

    def set_times(self, times: list[float]) -> None:
        if not times:
            return
        self.plot.clear()
        self.plot.plot(times, [0 for _ in times], pen=pg.mkPen(color=(90, 110, 140), width=2))
        self.region = pg.LinearRegionItem(values=(times[0], times[-1]))
        self.plot.addItem(self.region)

    def selection(self) -> Tuple[float, float]:
        start, end = self.region.getRegion()
        return float(start), float(end)


class ChannelPlot(QtWidgets.QWidget):
    channelChanged = QtCore.Signal(str)

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel(title)
        self.combo = QtWidgets.QComboBox()
        self.combo.currentTextChanged.connect(self.channelChanged.emit)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.combo)
        layout.addLayout(header)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        layout.addWidget(self.plot)

    def set_channels(self, channels: list[str]) -> None:
        self.combo.clear()
        self.combo.addItems(channels)

    def set_series(self, times: list[float], values: list[float]) -> None:
        self.plot.clear()
        if not times:
            return
        self.plot.plot(times, values, pen=pg.mkPen(color=(46, 110, 200), width=2))


def populate_channel_plots(plots: Dict[str, ChannelPlot], data: Dict[str, Tuple[list, list]]) -> None:
    for label, plot in plots.items():
        if label not in data:
            continue
        times, values = data[label]
        plot.set_series(times, values)
