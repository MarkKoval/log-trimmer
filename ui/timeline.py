from __future__ import annotations

from typing import Tuple

import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets


class TimelineWidget(QtWidgets.QWidget):
    selection_changed = QtCore.Signal(float, float)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget(background=None)
        self.plot.showGrid(x=True, y=False, alpha=0.2)
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.setMenuEnabled(False)

        self.region = pg.LinearRegionItem(values=(0, 1), movable=True)
        self.region.setZValue(10)
        self.plot.addItem(self.region)
        self.region.sigRegionChanged.connect(self._on_region_change)

        layout.addWidget(self.plot)

    def _on_region_change(self) -> None:
        start, end = self.region.getRegion()
        self.selection_changed.emit(float(start), float(end))

    def set_bounds(self, start: float, end: float) -> None:
        self.plot.setXRange(start, end)
        self.region.setRegion((start, end))

    def set_preview(self, data: Tuple[list[float], list[float]]) -> None:
        self.plot.clear()
        times, values = data
        self.plot.plot(times, values, pen=pg.mkPen("#3a6ff7", width=2))
        self.plot.addItem(self.region)
        if times:
            self.set_bounds(times[0], times[-1])
