# Log Trimmer (ArduPilot DataFlash)

Production-ready desktop app for trimming and cutting ArduPilot DataFlash flight logs with a modern iOS-like UI.

## Features
- Open ArduPilot DataFlash `.BIN` logs with pymavlink DFReader.
- Interactive timeline with range selection, zoom & pan (pyqtgraph).
- Trim/Keep selection or Cut/Remove selection.
- Multiple remove segments with Undo/Redo history.
- Export a valid `.BIN` log for Mission Planner/MAVExplorer.
- Diagnostics panel with local logging.

## Project Structure
```
.
├── app.py
├── core/
│   ├── __init__.py
│   ├── dataflash.py
│   ├── indexer.py
│   ├── logging_setup.py
│   └── segments.py
├── ui/
│   ├── __init__.py
│   ├── diagnostics.py
│   ├── main_window.py
│   ├── plotting.py
│   ├── theme.py
│   └── widgets.py
├── tests/
│   └── test_segments.py
└── requirements.txt
```

## Installation
> Python 3.11+ required.

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

## UX Flow (Quick Guide)
1. **Open Log**: click "Open Log" or drop a `.BIN` file.
2. **Select Range**: drag the timeline handles to choose start/end.
3. **Trim / Cut**:
   - *Trim/Keep* keeps only the selection.
   - *Cut/Remove* removes the selection and joins the rest.
4. **Undo/Redo** as needed.
5. **Export As…** to save a new `.BIN` log.

## Export Details
- Exporting is streaming-based: the app parses the log with DFReader and copies raw record bytes into the new file while skipping removed segments.
- If timestamps are unavailable, a record counter is used as a fallback.

## Tests
```bash
pytest
```

## Packaging (Optional: PyInstaller)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py
```

## Notes
- The UI theme mimics iOS 26 “glass” styling using translucent panels and soft shadows.
- Logs are cached/parsed in a streaming fashion to avoid loading everything into memory.
