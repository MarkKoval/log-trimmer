# Log Trimmer (ArduPilot DataFlash)

Production-ready desktop tool for trimming ArduPilot DataFlash flight logs (`.BIN`). Built with **Python 3.11+**, **PySide6**, and **pyqtgraph**.

## Features
- Import `.BIN` (DataFlash) logs with streaming parsing (pymavlink DFReader).
- iOS-style glass UI with light theme and rounded panels.
- Timeline selection with zoom/pan and multi-panel charts.
- Trim/Keep selection, Cut/Remove selection, Undo/Redo history.
- Export trimmed `.BIN` without loading whole log into memory.
- Diagnostics panel and file logging.

## Project Structure
```
log-trimmer/
├── app.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── exporter.py
│   ├── history.py
│   ├── log_reader.py
│   ├── logging_config.py
│   └── segments.py
├── ui/
│   ├── __init__.py
│   ├── charts.py
│   ├── diagnostics.py
│   ├── main_window.py
│   ├── theme.py
│   └── timeline.py
└── tests/
    └── test_segments.py
```

## Requirements
- Python 3.11+
- Works on Windows, macOS, and Linux

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

## Tests
```bash
pytest
```

## UX Flow (Quick Guide)
1. **Open Log** from the landing screen or drag & drop `.BIN` file.
2. Inspect **file stats** on the left, see the **timeline** and **charts** in the center.
3. Drag the selection window on the timeline to choose a time range.
4. Click **Trim/Keep Selection** or **Cut/Remove Selection** to build segments.
5. Use **Undo/Redo** to adjust.
6. Click **Export As…** to save a valid DataFlash `.BIN` for Mission Planner/MAVExplorer.

## Notes
- Parsing and indexing are streamed via **pymavlink DFReader**. For very large logs, the app stores lightweight index points and chart samples.
- Diagnostics are stored in `~/.log_trimmer/app.log` and can be viewed from the UI.

## Packaging (optional)
Use PyInstaller:
```bash
pyinstaller --noconfirm --name LogTrimmer --windowed app.py
```
