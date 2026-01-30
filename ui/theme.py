from PySide6 import QtGui


def apply_theme(app: QtGui.QGuiApplication) -> None:
    font = QtGui.QFont("SF Pro Display", 11)
    app.setFont(font)

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#f3f4f8"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#1c1c1e"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#f0f1f5"))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#1c1c1e"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#1c1c1e"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#1c1c1e"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#007aff"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))

    app.setPalette(palette)
    app.setStyleSheet(
        """
        QWidget {
            color: #1c1c1e;
        }
        QMainWindow {
            background: #f3f4f8;
        }
        .glass-panel {
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.6);
            border-radius: 16px;
        }
        QPushButton {
            background: #ffffff;
            border-radius: 14px;
            padding: 10px 16px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        }
        QPushButton:hover {
            background: #f7f7fa;
        }
        QPushButton:pressed {
            background: #eceef4;
        }
        QLineEdit, QComboBox {
            background: #ffffff;
            border-radius: 12px;
            padding: 8px 12px;
            border: 1px solid rgba(0, 0, 0, 0.08);
        }
        QProgressBar {
            background: #e5e7ee;
            border-radius: 8px;
            height: 12px;
        }
        QProgressBar::chunk {
            background: #007aff;
            border-radius: 8px;
        }
        """
    )
