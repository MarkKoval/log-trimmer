from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pyqtgraph as pg
from PySide6.QtCore import QObject, Qt, Signal, QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core import (
    DataFlashExporter,
    DataFlashParser,
    LogInfo,
    Segment,
    normalize_segments,
    remove_segments,
    validate_segments,
)
from ui.diagnostics import DiagnosticsDialog
from ui.widgets import RangeSelector

logger = logging.getLogger(__name__)


class LogLoadWorker(QObject):
    finished = Signal(LogInfo, dict)
    failed = Signal(str)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def run(self) -> None:
        try:
            parser = DataFlashParser(self.path)
            log_info = parser.summarize()
            series = parser.collect_series()
            self.finished.emit(log_info, series)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to open log: %s", exc)
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, log_file: Path) -> None:
        super().__init__()
        self.setWindowTitle("Log Trimmer")
        self.resize(1280, 860)

        self.log_file = log_file
        self.current_path: Optional[Path] = None
        self.log_info: Optional[LogInfo] = None
        self.series: Dict[str, object] = {}
        self.remove_segments: List[Segment] = []
        self.history: List[List[Segment]] = []
        self.history_index = -1
        self.load_thread: Optional[QThread] = None
        self.load_dialog: Optional[QProgressDialog] = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_view = self._build_home()
        self.editor_view = self._build_editor()
        self.stack.addWidget(self.home_view)
        self.stack.addWidget(self.editor_view)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".bin":
                self.open_log(path)
                break
        else:
            QMessageBox.warning(self, "Unsupported file", "Please drop a .BIN DataFlash log file.")

    def _build_home(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(24)

        title = QLabel("Log Trimmer")
        title.setStyleSheet("font-size: 32px; font-weight: 600;")
        subtitle = QLabel("Open an ArduPilot DataFlash log to begin.")
        subtitle.setStyleSheet("color: #6B7280; font-size: 14px;")

        open_btn = QPushButton("Open Log")
        open_btn.setFixedWidth(180)
        open_btn.clicked.connect(self._open_file_dialog)

        recent_label = QLabel("Recent")
        recent_list = QListWidget()
        recent_list.addItem("No recent files")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(open_btn)
        layout.addWidget(recent_label)
        layout.addWidget(recent_list, 1)
        layout.addStretch(1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.info_panel = self._panel()
        self.info_layout = QVBoxLayout(self.info_panel)
        self.info_layout.addWidget(QLabel("File info"))
        self.info_items = QListWidget()
        self.info_layout.addWidget(self.info_items, 1)

        center_panel = self._panel()
        center_layout = QVBoxLayout(center_panel)

        self.timeline = RangeSelector()
        self.timeline.range_changed.connect(self._on_range_change)

        self.plot_primary = self._plot_widget()
        self.plot_secondary = self._plot_widget()
        self.plot_tertiary = self._plot_widget()

        plot_controls = QHBoxLayout()
        self.primary_combo = self._channel_combo()
        self.secondary_combo = self._channel_combo()
        self.tertiary_combo = self._channel_combo()
        plot_controls.addWidget(QLabel("Plot 1"))
        plot_controls.addWidget(self.primary_combo)
        plot_controls.addWidget(QLabel("Plot 2"))
        plot_controls.addWidget(self.secondary_combo)
        plot_controls.addWidget(QLabel("Plot 3"))
        plot_controls.addWidget(self.tertiary_combo)

        center_layout.addWidget(QLabel("Timeline"))
        center_layout.addWidget(self.timeline)
        center_layout.addLayout(plot_controls)
        center_layout.addWidget(self.plot_primary, 1)
        center_layout.addWidget(self.plot_secondary, 1)
        center_layout.addWidget(self.plot_tertiary, 1)

        self.tool_panel = self._panel()
        tool_layout = QVBoxLayout(self.tool_panel)
        tool_layout.addWidget(QLabel("Edit tools"))

        self.trim_btn = QPushButton("Trim to selection")
        self.cut_btn = QPushButton("Remove selection")
        self.keep_btn = QPushButton("Keep selection")
        self.remove_btn = QPushButton("Cut selection")
        self.undo_btn = QPushButton("Undo")
        self.redo_btn = QPushButton("Redo")
        self.export_btn = QPushButton("Export As…")
        self.diagnostics_btn = QPushButton("Diagnostics")

        for btn in (
            self.trim_btn,
            self.cut_btn,
            self.keep_btn,
            self.remove_btn,
            self.undo_btn,
            self.redo_btn,
            self.export_btn,
            self.diagnostics_btn,
        ):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tool_layout.addWidget(btn)

        tool_layout.addStretch(1)

        layout.addWidget(self.info_panel, 0, 0, 2, 1)
        layout.addWidget(center_panel, 0, 1, 2, 2)
        layout.addWidget(self.tool_panel, 0, 3, 2, 1)

        self.trim_btn.clicked.connect(self._trim)
        self.cut_btn.clicked.connect(self._remove)
        self.keep_btn.clicked.connect(self._trim)
        self.remove_btn.clicked.connect(self._remove)
        self.undo_btn.clicked.connect(self._undo)
        self.redo_btn.clicked.connect(self._redo)
        self.export_btn.clicked.connect(self._export)
        self.diagnostics_btn.clicked.connect(self._show_diagnostics)

        self.primary_combo.currentIndexChanged.connect(self._refresh_plots)
        self.secondary_combo.currentIndexChanged.connect(self._refresh_plots)
        self.tertiary_combo.currentIndexChanged.connect(self._refresh_plots)

        return widget

    def _panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel")
        frame.setFrameShape(QFrame.StyledPanel)
        return frame

    def _plot_widget(self) -> pg.PlotWidget:
        plot = pg.PlotWidget(background=None)
        plot.showGrid(x=True, y=True, alpha=0.2)
        return plot

    def _channel_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.addItems(["ALT", "GPS_SPEED", "ATT_ROLL", "ATT_PITCH", "ATT_YAW", "THR"])
        return combo

    def _open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Log", str(Path.home()), "DataFlash (*.BIN *.bin)")
        if path:
            self.open_log(Path(path))

    def open_log(self, path: Path) -> None:
        if path.suffix.lower() != ".bin":
            QMessageBox.warning(self, "Unsupported file", "Only .BIN DataFlash logs are supported.")
            return
        self.load_dialog = QProgressDialog("Loading log…", None, 0, 0, self)
        self.load_dialog.setWindowTitle("Loading")
        self.load_dialog.setWindowModality(Qt.WindowModal)
        self.load_dialog.setMinimumDuration(0)
        self.load_dialog.show()

        self.load_thread = QThread()
        worker = LogLoadWorker(path)
        worker.moveToThread(self.load_thread)
        self.load_thread.started.connect(worker.run)
        worker.finished.connect(self._on_log_loaded)
        worker.failed.connect(self._on_log_failed)
        worker.finished.connect(self.load_thread.quit)
        worker.failed.connect(self.load_thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        self.load_thread.finished.connect(self.load_thread.deleteLater)
        self.load_thread.start()

    def _on_log_loaded(self, log_info: LogInfo, series: dict) -> None:
        if self.load_dialog:
            self.load_dialog.close()
        self.log_info = log_info
        self.series = series
        self.current_path = log_info.path
        self._populate_info()
        self._load_series()
        self._set_history([])
        self.stack.setCurrentWidget(self.editor_view)

    def _on_log_failed(self, message: str) -> None:
        if self.load_dialog:
            self.load_dialog.close()
        QMessageBox.critical(self, "Open error", f"Failed to open log: {message}")

    def _populate_info(self) -> None:
        if not self.log_info:
            return
        info = self.log_info
        self.info_items.clear()
        self.info_items.addItem(f"Path: {info.path}")
        self.info_items.addItem(f"Size: {info.size_bytes / (1024*1024):.2f} MB")
        self.info_items.addItem(f"Messages: {info.message_count}")
        self.info_items.addItem(f"Start: {info.start_time:.2f}s")
        self.info_items.addItem(f"End: {info.end_time:.2f}s")
        self.info_items.addItem(f"Type: {info.log_type}")

    def _load_series(self) -> None:
        if not self.series or not self.log_info:
            return
        self.timeline.set_range(self.log_info.start_time, self.log_info.end_time)
        self.primary_combo.setCurrentText("ALT")
        self.secondary_combo.setCurrentText("GPS_SPEED")
        self.tertiary_combo.setCurrentText("ATT_ROLL")
        self._refresh_plots()

    def _refresh_plots(self) -> None:
        self._plot_series(self.plot_primary, self.primary_combo.currentText())
        self._plot_series(self.plot_secondary, self.secondary_combo.currentText())
        self._plot_series(self.plot_tertiary, self.tertiary_combo.currentText())

    def _plot_series(self, plot: pg.PlotWidget, key: str) -> None:
        plot.clear()
        series = self.series.get(key)
        if not series:
            return
        plot.plot(series.times, series.values, pen=pg.mkPen(color="#3A7BFF", width=2))

    def _on_range_change(self, start: float, end: float) -> None:
        self.trim_btn.setEnabled(start < end)
        self.cut_btn.setEnabled(start < end)

    def _trim(self) -> None:
        if not self.log_info:
            return
        start, end = self.timeline.selection()
        remove = remove_segments(self.log_info.start_time, self.log_info.end_time, [Segment(start, end)])
        self._set_history(remove)

    def _remove(self) -> None:
        if not self.log_info:
            return
        start, end = self.timeline.selection()
        updated = normalize_segments(self.remove_segments + [Segment(start, end)])
        self._set_history(updated)

    def _set_history(self, segments: List[Segment]) -> None:
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]
        self.history.append(list(segments))
        self.history_index += 1
        self.remove_segments = list(segments)
        self._update_history_buttons()

    def _undo(self) -> None:
        if self.history_index > 0:
            self.history_index -= 1
            self.remove_segments = list(self.history[self.history_index])
        self._update_history_buttons()

    def _redo(self) -> None:
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.remove_segments = list(self.history[self.history_index])
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        self.undo_btn.setEnabled(self.history_index > 0)
        self.redo_btn.setEnabled(self.history_index < len(self.history) - 1)

    def _export(self) -> None:
        if not self.current_path or not self.log_info:
            return
        try:
            validate_segments(self.remove_segments, self.log_info.start_time, self.log_info.end_time)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid selection", str(exc))
            return
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export As…",
            str(self.current_path.with_name(self.current_path.stem + "_trimmed.bin")),
            "DataFlash (*.BIN *.bin)",
        )
        if not dest:
            return

        progress = QProgressDialog("Exporting…", "Cancel", 0, 100, self)
        progress.setWindowTitle("Export")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        exporter = DataFlashExporter(self.current_path)

        def on_progress(state) -> None:
            if state.total:
                progress.setValue(int(state.current / state.total * 100))
            if progress.wasCanceled():
                raise RuntimeError("Export canceled")

        try:
            exporter.export(
                Path(dest),
                self.remove_segments,
                progress_cb=on_progress,
                total_messages=self.log_info.message_count,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Export failed: %s", exc)
            QMessageBox.critical(self, "Export failed", f"Export failed: {exc}")
            return
        progress.setValue(100)
        QMessageBox.information(self, "Export complete", "Trimmed log exported successfully.")

    def _show_diagnostics(self) -> None:
        dialog = DiagnosticsDialog(self.log_file, self)
        dialog.exec()
