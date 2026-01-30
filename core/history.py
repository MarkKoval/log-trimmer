from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .segments import Segment


@dataclass
class EditState:
    remove_segments: List[Segment]


class UndoRedoStack:
    def __init__(self) -> None:
        self._undo: List[EditState] = []
        self._redo: List[EditState] = []

    def push(self, state: EditState) -> None:
        self._undo.append(state)
        self._redo.clear()

    def undo(self, current_state: EditState) -> EditState:
        if not self._undo:
            return current_state
        self._redo.append(current_state)
        return self._undo.pop()

    def redo(self, current_state: EditState) -> EditState:
        if not self._redo:
            return current_state
        self._undo.append(current_state)
        return self._redo.pop()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)
