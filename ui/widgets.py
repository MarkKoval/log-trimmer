from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class GlassPanel(QtWidgets.QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassPanel")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setGraphicsEffect(_blur_effect())


def _blur_effect() -> QtWidgets.QGraphicsEffect:
    effect = QtWidgets.QGraphicsBlurEffect()
    effect.setBlurRadius(8)
    effect.setBlurHints(QtWidgets.QGraphicsBlurEffect.QualityHint)
    return effect


class DropZone(QtWidgets.QFrame):
    fileDropped = QtCore.Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet(
            "background-color: rgba(255,255,255,120); border: 2px dashed rgba(0,0,0,60); "
            "border-radius: 16px;"
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.label = QtWidgets.QLabel("Drop log file here")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        for url in event.mimeData().urls():
            self.fileDropped.emit(url.toLocalFile())
            break
