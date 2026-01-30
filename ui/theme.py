from __future__ import annotations

from PySide6 import QtGui


def apply_theme(app) -> None:
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(242, 244, 248))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(20, 20, 25))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(240, 242, 246))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(20, 20, 25))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(248, 249, 252))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(20, 20, 25))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(53, 132, 228))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget {
            font-family: "SF Pro Display", "Segoe UI", "Helvetica Neue", sans-serif;
            font-size: 13px;
        }
        QMainWindow {
            background-color: #f2f4f8;
        }
        QPushButton {
            background-color: rgba(255, 255, 255, 180);
            border: 1px solid rgba(0, 0, 0, 20);
            border-radius: 14px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 230);
        }
        QPushButton:pressed {
            background-color: rgba(230, 235, 245, 230);
        }
        QFrame#GlassPanel {
            background-color: rgba(255, 255, 255, 200);
            border: 1px solid rgba(0, 0, 0, 30);
            border-radius: 16px;
        }
        QLabel#Title {
            font-size: 22px;
            font-weight: 600;
        }
        QLabel#Subtitle {
            color: #5b6472;
        }
        QComboBox {
            background-color: rgba(255, 255, 255, 200);
            border-radius: 10px;
            padding: 6px 10px;
        }
        QLineEdit {
            background-color: rgba(255, 255, 255, 200);
            border-radius: 10px;
            padding: 6px 10px;
        }
        QToolButton {
            background-color: rgba(255, 255, 255, 200);
            border-radius: 10px;
            padding: 6px 10px;
        }
        """
    )
