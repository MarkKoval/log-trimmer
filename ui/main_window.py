from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from core.exporter import DataFlashExporter
from core.history import EditState, UndoRedoStack
from core.log_reader import DataFlashLogReader, LogSummary
from core.segments import Segment, apply_cut, apply_trim
from core.logging_config import LOG_FILE
from ui.charts import ChartsArea
from ui.diagnostics import DiagnosticsDialog
from ui.timeline import TimelineWidget


LOGGER = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Log Trimmer")
        self.setMinimumSize(1280, 820)
        self.setAcceptDrops(True)

        self._summary: Optional[LogSummary] = None
        self._remove_segments: list[Segment] = []
        self._history = UndoRedoStack()
        self._selection: Optional[Segment] = None

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.landing_page = self._build_landing()
        self.editor_page = self._build_editor()

        self.stack.addWidget(self.landing_page)
        self.stack.addWidget(self.editor_page)

    def _build_landing(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)

        title = QtWidgets.QLabel("Flight Log Trimmer")
        title.setFont(QtGui.QFont("SF Pro Display", 28, QtGui.QFont.Weight.Bold))

        subtitle = QtWidgets.QLabel(
            "Import ArduPilot DataFlash logs, select time ranges, and export clean logs."
        )
        subtitle.setStyleSheet("color: #5c5c66;")

        open_button = QtWidgets.QPushButton("Open Log")
        open_button.setFixedWidth(160)
        open_button.clicked.connect(self.open_log)

        recent_label = QtWidgets.QLabel("Recent")
        recent_label.setFont(QtGui.QFont("SF Pro Display", 16, QtGui.QFont.Weight.Medium))

        self.recent_list = QtWidgets.QListWidget()
        self.recent_list.setFixedHeight(160)
        self.recent_list.itemDoubleClicked.connect(self._open_recent)

        drag_label = QtWidgets.QLabel("Drag & drop a .BIN log here")
        drag_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        drag_label.setObjectName("glass-panel")
        drag_label.setStyleSheet("padding: 36px; font-size: 15px; color: #5c5c66;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(open_button, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(recent_label)
        layout.addWidget(self.recent_list)
        layout.addStretch()
        layout.addWidget(drag_label)

        return widget

    def _build_editor(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QtWidgets.QHBoxLayout()
        self.file_label = QtWidgets.QLabel("No log loaded")
        self.file_label.setFont(QtGui.QFont("SF Pro Display", 18, QtGui.QFont.Weight.Medium))
        header.addWidget(self.file_label)
        header.addStretch()

        export_button = QtWidgets.QPushButton("Export As…")
        export_button.clicked.connect(self.export_log)
        diag_button = QtWidgets.QPushButton("Diagnostics")
        diag_button.clicked.connect(self.show_diagnostics)

        header.addWidget(diag_button)
        header.addWidget(export_button)

        layout.addLayout(header)

        content = QtWidgets.QHBoxLayout()
        content.setSpacing(16)

        self.info_panel = self._build_info_panel()
        content.addWidget(self.info_panel)

        center_panel = QtWidgets.QVBoxLayout()
        center_panel.setSpacing(16)
        self.timeline = TimelineWidget()
        self.timeline.selection_changed.connect(self._update_selection)
        self.timeline.setObjectName("glass-panel")
        self.timeline.setStyleSheet("padding: 12px;")

        self.charts = ChartsArea()

        center_panel.addWidget(self.timeline, stretch=2)
        center_panel.addWidget(self.charts, stretch=3)

        content.addLayout(center_panel, stretch=3)

        self.tools_panel = self._build_tools_panel()
        content.addWidget(self.tools_panel)

        layout.addLayout(content)
        return widget

    def _build_info_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QFrame()
        panel.setObjectName("glass-panel")
        panel.setStyleSheet("padding: 16px;")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(12)

        self.info_labels = {}
        for label in ["Size", "Duration", "Time Range", "Type", "Messages"]:
            title = QtWidgets.QLabel(label)
            title.setStyleSheet("color: #6b6b75;")
            value = QtWidgets.QLabel("-")
            value.setWordWrap(True)
            self.info_labels[label] = value
            layout.addWidget(title)
            layout.addWidget(value)

        layout.addStretch()
        return panel

    def _build_tools_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QFrame()
        panel.setObjectName("glass-panel")
        panel.setStyleSheet("padding: 16px;")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(12)

        self.trim_button = QtWidgets.QPushButton("Trim / Keep Selection")
        self.cut_button = QtWidgets.QPushButton("Cut / Remove Selection")
        self.undo_button = QtWidgets.QPushButton("Undo")
        self.redo_button = QtWidgets.QPushButton("Redo")
        self.undo_button.setEnabled(False)
        self.redo_button.setEnabled(False)

        self.trim_button.clicked.connect(self.trim_selection)
        self.cut_button.clicked.connect(self.cut_selection)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)

        layout.addWidget(self.trim_button)
        layout.addWidget(self.cut_button)
        layout.addStretch()
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        return panel

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            self._load_log(Path(urls[0].toLocalFile()))

    def open_log(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open DataFlash Log",
            str(Path.home()),
            "Log Files (*.bin *.BIN *.log *.tlog)",
        )
        if path:
            self._load_log(Path(path))

    def _open_recent(self, item: QtWidgets.QListWidgetItem) -> None:
        self._load_log(Path(item.text()))

    def _load_log(self, path: Path) -> None:
        try:
            LOGGER.info("Loading log %s", path)
            reader = DataFlashLogReader(path)
            summary = reader.build_index()
        except Exception as exc:
            LOGGER.exception("Failed to open log")
            QtWidgets.QMessageBox.critical(self, "Open log failed", str(exc))
            return

        self._summary = summary
        self._remove_segments = []
        self._history = UndoRedoStack()
        self._selection = Segment(summary.start_time, summary.end_time)
        self._update_info(summary)
        self._update_recent(path)
        self._update_charts(summary)
        self._update_history_buttons()

        preview = summary.sample_channels.get("ALT")
        if preview:
            times = [item[0] for item in preview]
            values = [item[1] for item in preview]
            self.timeline.set_preview((times, values))
        else:
            self.timeline.set_bounds(summary.start_time, summary.end_time)

        self.stack.setCurrentWidget(self.editor_page)

    def _update_recent(self, path: Path) -> None:
        existing = [self.recent_list.item(i).text() for i in range(self.recent_list.count())]
        if str(path) not in existing:
            self.recent_list.insertItem(0, str(path))

    def _update_info(self, summary: LogSummary) -> None:
        size = summary.path.stat().st_size / (1024 * 1024)
        self.file_label.setText(summary.path.name)
        self.info_labels["Size"].setText(f"{size:.2f} MB")
        self.info_labels["Duration"].setText(f"{summary.duration:.2f} s")
        self.info_labels["Time Range"].setText(
            f"{summary.start_time:.2f} → {summary.end_time:.2f}"
        )
        self.info_labels["Type"].setText("ArduPilot DataFlash (.BIN)")
        self.info_labels["Messages"].setText(str(summary.message_count))

    def _update_charts(self, summary: LogSummary) -> None:
        self.charts.bind_channels(summary.sample_channels)

    def _update_selection(self, start: float, end: float) -> None:
        if not self._summary:
            return
        self._selection = Segment(start, end)

    def trim_selection(self) -> None:
        if not self._summary or not self._selection:
            return
        self._history.push(EditState(remove_segments=self._remove_segments.copy()))
        self._remove_segments = apply_trim(
            self._selection, self._summary.start_time, self._summary.end_time
        )
        self._update_history_buttons()

    def cut_selection(self) -> None:
        if not self._summary or not self._selection:
            return
        self._history.push(EditState(remove_segments=self._remove_segments.copy()))
        self._remove_segments = apply_cut(
            self._remove_segments + [self._selection],
            self._summary.start_time,
            self._summary.end_time,
        )
        self._update_history_buttons()

    def undo(self) -> None:
        self._remove_segments = self._history.undo(EditState(self._remove_segments)).remove_segments
        self._update_history_buttons()

    def redo(self) -> None:
        self._remove_segments = self._history.redo(EditState(self._remove_segments)).remove_segments
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        self.undo_button.setEnabled(self._history.can_undo())
        self.redo_button.setEnabled(self._history.can_redo())

    def export_log(self) -> None:
        if not self._summary:
            return
        output_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Log",
            str(self._summary.path.with_name(self._summary.path.stem + "_trimmed.BIN")),
            "DataFlash (*.BIN *.bin)",
        )
        if not output_path:
            return
        progress = QtWidgets.QProgressDialog("Exporting…", "Cancel", 0, 0, self)
        progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        progress.show()
        QtWidgets.QApplication.processEvents()

        try:
            exporter = DataFlashExporter(self._summary.path)
            exporter.export(Path(output_path), self._remove_segments)
        except Exception as exc:
            LOGGER.exception("Export failed")
            QtWidgets.QMessageBox.critical(self, "Export failed", str(exc))
        finally:
            progress.close()

    def show_diagnostics(self) -> None:
        dialog = DiagnosticsDialog(LOG_FILE, self)
        dialog.exec()
