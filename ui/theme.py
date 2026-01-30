from __future__ import annotations

from PySide6.QtGui import QColor


class Theme:
    def __init__(self, dark: bool = False) -> None:
        self.dark = dark
        self.background = QColor("#F4F5F8") if not dark else QColor("#111317")
        self.surface = QColor("#FFFFFF") if not dark else QColor("#1A1D24")
        self.surface_glass = QColor(255, 255, 255, 190) if not dark else QColor(30, 34, 44, 200)
        self.primary = QColor("#3A7BFF")
        self.text = QColor("#1C1D22") if not dark else QColor("#F4F5F8")
        self.text_muted = QColor("#6B7280") if not dark else QColor("#A0A7B4")

    def stylesheet(self) -> str:
        radius = 16
        return f"""
        QWidget {{
            color: {self.text.name()};
            font-family: "SF Pro Display", "Helvetica Neue", "Inter", sans-serif;
            font-size: 13px;
        }}
        QMainWindow {{
            background: {self.background.name()};
        }}
        QPushButton {{
            background: rgba(58, 123, 255, 0.12);
            border: 1px solid rgba(58, 123, 255, 0.25);
            padding: 10px 16px;
            border-radius: {radius}px;
        }}
        QPushButton:hover {{
            background: rgba(58, 123, 255, 0.2);
        }}
        QPushButton:pressed {{
            background: rgba(58, 123, 255, 0.3);
        }}
        QFrame#glass {{
            background: rgba(255, 255, 255, 0.6);
            border-radius: {radius}px;
            border: 1px solid rgba(255, 255, 255, 0.35);
        }}
        QFrame#panel {{
            background: {self.surface.name()};
            border-radius: {radius}px;
            border: 1px solid rgba(0,0,0,0.05);
        }}
        QListWidget {{
            background: transparent;
        }}
        QSlider::groove:horizontal {{
            height: 6px;
            background: rgba(120, 120, 120, 0.15);
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {self.primary.name()};
            width: 16px;
            height: 16px;
            border-radius: 8px;
            margin: -5px 0;
        }}
        QComboBox {{
            padding: 8px 12px;
            border-radius: {radius}px;
            border: 1px solid rgba(0,0,0,0.08);
            background: {self.surface.name()};
        }}
        """
