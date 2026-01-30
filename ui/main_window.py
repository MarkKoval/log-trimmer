from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from PySide6 import QtCore, QtGui, QtWidgets

from core.dataflash import DataFlashExporter, DataFlashReader, read_channel_samples
from core.indexer import build_time_index
from core.segments import (
    Segment,
    SegmentHistory,
    SegmentError,
    add_remove_segment,
    trim_to_selection,
    validate_segments,
)
from ui.diagnostics import DiagnosticsDialog
from ui.plotting import ChannelPlot, TimelinePlot, populate_channel_plots
from ui.widgets import DropZone, GlassPanel

logger = logging.getLogger(__name__)

CHANNELS = {
    "ALT": ("BARO", "Alt"),
    "GPS Speed": ("GPS", "Spd"),
    "ATT Roll": ("ATT", "Roll"),
    "ATT Pitch": ("ATT", "Pitch"),
    "Throttle": ("RCOU", "C3"),
}


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, diagnostics_log_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.log_path = Path()
        self.diagnostics_log_path = diagnostics_log_path
        self.setWindowTitle("Log Trimmer")
        self.resize(1200, 780)
        self.history = SegmentHistory()
        self.log_info = None
        self.time_index = None
        self.channel_data: Dict[str, tuple[list, list]] = {}

        self._setup_ui()
        self._connect_actions()

    def _setup_ui(self) -> None:
        self.central = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.central)

        self.welcome_screen = QtWidgets.QWidget()
        welcome_layout = QtWidgets.QVBoxLayout(self.welcome_screen)
        welcome_layout.setAlignment(QtCore.Qt.AlignCenter)
        title = QtWidgets.QLabel("Flight Log Trimmer")
        title.setObjectName("Title")
        subtitle = QtWidgets.QLabel("Open an ArduPilot DataFlash log to begin")
        subtitle.setObjectName("Subtitle")
        welcome_layout.addWidget(title)
        welcome_layout.addWidget(subtitle)

        self.open_button = QtWidgets.QPushButton("Open Log")
        self.recent_list = QtWidgets.QListWidget()
        self.recent_list.setMaximumWidth(400)
        self.recent_list.addItem("No recent logs")
        self.drop_zone = DropZone()

        welcome_layout.addWidget(self.open_button)
        welcome_layout.addWidget(self.drop_zone)
        welcome_layout.addWidget(QtWidgets.QLabel("Recent"))
        welcome_layout.addWidget(self.recent_list)

        self.editor_screen = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(self.editor_screen)
        editor_layout.setContentsMargins(20, 20, 20, 20)
        editor_layout.setSpacing(18)

        self.info_panel = GlassPanel()
        info_layout = QtWidgets.QVBoxLayout(self.info_panel)
        info_layout.setSpacing(12)
        self.info_label = QtWidgets.QLabel("No log loaded")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(QtWidgets.QLabel("Log Info"))
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()

        self.center_panel = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(self.center_panel)
        center_layout.setSpacing(12)
        self.timeline_plot = TimelinePlot()
        center_layout.addWidget(self.timeline_plot)

        graphs_layout = QtWidgets.QGridLayout()
        self.channel_plots: Dict[str, ChannelPlot] = {}
        available_channels = list(CHANNELS.keys())
        for index, label in enumerate(available_channels[:3]):
            plot = ChannelPlot(label)
            plot.set_channels(available_channels)
            plot.combo.setCurrentText(label)
            plot.channelChanged.connect(self.update_plot_channel)
            self.channel_plots[label] = plot
            graphs_layout.addWidget(plot, index // 2, index % 2)
        center_layout.addLayout(graphs_layout)

        self.tools_panel = GlassPanel()
        tools_layout = QtWidgets.QVBoxLayout(self.tools_panel)
        tools_layout.setSpacing(10)
        tools_layout.addWidget(QtWidgets.QLabel("Edit Tools"))
        self.trim_button = QtWidgets.QPushButton("Trim")
        self.cut_button = QtWidgets.QPushButton("Cut")
        self.keep_button = QtWidgets.QPushButton("Keep selection")
        self.remove_button = QtWidgets.QPushButton("Remove selection")
        self.undo_button = QtWidgets.QPushButton("Undo")
        self.redo_button = QtWidgets.QPushButton("Redo")
        self.export_button = QtWidgets.QPushButton("Export As…")
        self.diagnostics_button = QtWidgets.QPushButton("Diagnostics")

        for button in (
            self.trim_button,
            self.cut_button,
            self.keep_button,
            self.remove_button,
            self.undo_button,
            self.redo_button,
            self.export_button,
            self.diagnostics_button,
        ):
            tools_layout.addWidget(button)
        tools_layout.addStretch()

        editor_layout.addWidget(self.info_panel, 1)
        editor_layout.addWidget(self.center_panel, 3)
        editor_layout.addWidget(self.tools_panel, 1)

        self.central.addWidget(self.welcome_screen)
        self.central.addWidget(self.editor_screen)

    def _connect_actions(self) -> None:
        self.open_button.clicked.connect(self.open_log_dialog)
        self.drop_zone.fileDropped.connect(self.open_log)
        self.export_button.clicked.connect(self.export_log)
        self.trim_button.clicked.connect(self.trim_to_selection)
        self.keep_button.clicked.connect(self.trim_to_selection)
        self.cut_button.clicked.connect(self.remove_selection)
        self.remove_button.clicked.connect(self.remove_selection)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.diagnostics_button.clicked.connect(self.show_diagnostics)

    def open_log_dialog(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open DataFlash Log",
            "",
            "DataFlash Logs (*.bin *.BIN *.log *.tlog);;All Files (*.*)",
        )
        if path:
            self.open_log(path)

    def open_log(self, path: str) -> None:
        try:
            self.log_path = Path(path)
            reader = DataFlashReader(self.log_path)
            self.log_info = reader.get_info()
            self.time_index = build_time_index(self.log_path)
            self._update_info_panel()
            self.timeline_plot.set_times(self.time_index.times)
            self.channel_data = read_channel_samples(self.log_path, CHANNELS)
            populate_channel_plots(self.channel_plots, self.channel_data)
            self.central.setCurrentWidget(self.editor_screen)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to open log")
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))

    def _update_info_panel(self) -> None:
        if not self.log_info:
            return
        info = self.log_info
        text = (
            f"File: {info.path.name}\n"
            f"Size: {info.size_bytes / (1024 * 1024):.2f} MB\n"
            f"Messages: {info.message_count}\n"
            f"Time range: {info.time_range[0]:.2f}s → {info.time_range[1]:.2f}s\n"
            f"Has time: {'Yes' if info.has_time else 'Fallback'}"
        )
        self.info_label.setText(text)

    def _selection_segment(self) -> Segment:
        start, end = self.timeline_plot.selection()
        return Segment(start, end)

    def trim_to_selection(self) -> None:
        if not self.log_info:
            return
        try:
            selection = self._selection_segment()
            segments = trim_to_selection(self.log_info.time_range, selection)
            self.history.set_segments(segments)
            QtWidgets.QMessageBox.information(self, "Trim", "Selection kept. Ready to export.")
        except SegmentError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid selection", str(exc))

    def remove_selection(self) -> None:
        if not self.log_info:
            return
        try:
            selection = self._selection_segment()
            segments = add_remove_segment(self.history.current, selection)
            validate_segments(segments, self.log_info.time_range)
            self.history.set_segments(segments)
            QtWidgets.QMessageBox.information(self, "Cut", "Selection removed. Ready to export.")
        except SegmentError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid selection", str(exc))

    def undo(self) -> None:
        if self.history.undo() is None:
            QtWidgets.QMessageBox.information(self, "Undo", "Nothing to undo.")

    def redo(self) -> None:
        if self.history.redo() is None:
            QtWidgets.QMessageBox.information(self, "Redo", "Nothing to redo.")

    def export_log(self) -> None:
        if not self.log_info:
            return
        try:
            segments = validate_segments(self.history.current, self.log_info.time_range)
        except SegmentError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid segments", str(exc))
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export DataFlash Log",
            f"{self.log_info.path.stem}_trimmed.BIN",
            "DataFlash Logs (*.BIN);;All Files (*.*)",
        )
        if not path:
            return
        progress = QtWidgets.QProgressDialog("Exporting...", "Cancel", 0, self.log_info.message_count, self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()

        exporter = DataFlashExporter(self.log_path)

        def on_progress(count: int) -> None:
            progress.setValue(count)
            QtWidgets.QApplication.processEvents()

        try:
            exporter.export(Path(path), [(s.start, s.end) for s in segments], progress=on_progress)
            progress.setValue(self.log_info.message_count)
            QtWidgets.QMessageBox.information(self, "Export", "Export completed successfully.")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Export failed")
            QtWidgets.QMessageBox.critical(self, "Export failed", str(exc))

    def show_diagnostics(self) -> None:
        dialog = DiagnosticsDialog(self.diagnostics_log_path, self)
        dialog.exec()

    def update_plot_channel(self, channel_name: str) -> None:
        if not self.channel_data or channel_name not in self.channel_data:
            return
        sender = self.sender()
        if not isinstance(sender, ChannelPlot):
            return
        times, values = self.channel_data[channel_name]
        sender.title_label.setText(channel_name)
        sender.set_series(times, values)
