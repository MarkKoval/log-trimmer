# Log Trimmer

Desktop app for trimming ArduPilot DataFlash logs with an iOS-inspired UI.

## Features
- Open `.BIN` DataFlash logs (ArduPlane/ArduPilot).
- Interactive timeline with selection range and zoom.
- Trim/Remove segments with undo/redo.
- Export trimmed logs to `.BIN`.
- Diagnostics panel with recent errors.

## Requirements
- Python 3.11+
- Windows/macOS (Linux supported)

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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

## Optional packaging (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile app.py --name LogTrimmer
```

## UX Flow
1. **Open Log** or drag-and-drop a `.BIN` file.
2. Review file info in the left panel.
3. Select time range on the timeline.
4. Use **Trim/Remove** to build edits (undo/redo supported).
5. Export via **Export As…**.

## Notes
- Parsing uses `pymavlink.DFReader` for DataFlash logs.
- Export runs in streaming mode to avoid loading the whole file.
