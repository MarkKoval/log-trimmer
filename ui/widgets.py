from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget


class RangeSelector(QWidget):
    range_changed = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self._min = 0.0
        self._max = 1.0
        self._start = 0.2
        self._end = 0.8

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.start_slider = QSlider(Qt.Horizontal)
        self.end_slider = QSlider(Qt.Horizontal)
        for slider in (self.start_slider, self.end_slider):
            slider.setRange(0, 1000)
            slider.valueChanged.connect(self._emit)

        self.start_label = QLabel("Start")
        self.end_label = QLabel("End")

        layout.addWidget(self.start_label)
        layout.addWidget(self.start_slider, 1)
        layout.addWidget(self.end_label)
        layout.addWidget(self.end_slider, 1)

        self.set_range(0.0, 1.0)

    def set_range(self, min_value: float, max_value: float) -> None:
        self._min = min_value
        self._max = max_value
        self.set_selection(min_value, max_value)

    def set_selection(self, start: float, end: float) -> None:
        self._start = start
        self._end = end
        self.start_slider.blockSignals(True)
        self.end_slider.blockSignals(True)
        self.start_slider.setValue(self._to_slider(start))
        self.end_slider.setValue(self._to_slider(end))
        self.start_slider.blockSignals(False)
        self.end_slider.blockSignals(False)
        self._emit()

    def selection(self) -> tuple[float, float]:
        return self._start, self._end

    def _to_slider(self, value: float) -> int:
        if self._max <= self._min:
            return 0
        return int((value - self._min) / (self._max - self._min) * 1000)

    def _from_slider(self, value: int) -> float:
        return self._min + (self._max - self._min) * (value / 1000.0)

    def _emit(self) -> None:
        start = self._from_slider(self.start_slider.value())
        end = self._from_slider(self.end_slider.value())
        if start > end:
            start, end = end, start
        self._start = start
        self._end = end
        self.start_label.setText(f"Start {start:.2f}s")
        self.end_label.setText(f"End {end:.2f}s")
        self.range_changed.emit(start, end)
