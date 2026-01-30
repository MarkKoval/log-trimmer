from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Segment:
    start: float
    end: float

    def normalized(self) -> "Segment":
        if self.start <= self.end:
            return self
        return Segment(self.end, self.start)


class SegmentError(ValueError):
    """Raised when segment validation fails."""


class SegmentHistory:
    def __init__(self) -> None:
        self._undo_stack: List[List[Segment]] = []
        self._redo_stack: List[List[Segment]] = []
        self._current: List[Segment] = []

    @property
    def current(self) -> List[Segment]:
        return list(self._current)

    def set_segments(self, segments: Iterable[Segment]) -> None:
        self._undo_stack.append(self.current)
        self._redo_stack.clear()
        self._current = list(segments)

    def undo(self) -> Optional[List[Segment]]:
        if not self._undo_stack:
            return None
        self._redo_stack.append(self.current)
        self._current = self._undo_stack.pop()
        return self.current

    def redo(self) -> Optional[List[Segment]]:
        if not self._redo_stack:
            return None
        self._undo_stack.append(self.current)
        self._current = self._redo_stack.pop()
        return self.current


def normalize_segments(segments: Iterable[Segment]) -> List[Segment]:
    normalized = [segment.normalized() for segment in segments]
    normalized.sort(key=lambda seg: seg.start)

    merged: List[Segment] = []
    for segment in normalized:
        if not merged:
            merged.append(segment)
            continue
        last = merged[-1]
        if segment.start <= last.end:
            merged[-1] = Segment(last.start, max(last.end, segment.end))
        else:
            merged.append(segment)
    return merged


def validate_segments(segments: Iterable[Segment], time_range: Tuple[float, float]) -> List[Segment]:
    start, end = time_range
    if start >= end:
        raise SegmentError("Invalid time range: start must be < end")

    normalized = normalize_segments(segments)
    for segment in normalized:
        if segment.start < start or segment.end > end:
            raise SegmentError("Segment outside of log time range")
        if segment.start >= segment.end:
            raise SegmentError("Segment start must be < end")
    return normalized


def trim_to_selection(time_range: Tuple[float, float], selection: Segment) -> List[Segment]:
    selection = selection.normalized()
    start, end = time_range
    if selection.start < start or selection.end > end:
        raise SegmentError("Selection outside of log time range")
    if selection.start >= selection.end:
        raise SegmentError("Selection start must be < end")

    segments: List[Segment] = []
    if selection.start > start:
        segments.append(Segment(start, selection.start))
    if selection.end < end:
        segments.append(Segment(selection.end, end))
    return segments


def add_remove_segment(segments: Iterable[Segment], selection: Segment) -> List[Segment]:
    selection = selection.normalized()
    if selection.start >= selection.end:
        raise SegmentError("Selection start must be < end")
    combined = list(segments) + [selection]
    return normalize_segments(combined)


def segments_to_keep(time_range: Tuple[float, float], remove_segments: Iterable[Segment]) -> List[Segment]:
    start, end = time_range
    remove_segments = normalize_segments(remove_segments)
    keep: List[Segment] = []
    cursor = start
    for segment in remove_segments:
        if segment.start > cursor:
            keep.append(Segment(cursor, segment.start))
        cursor = max(cursor, segment.end)
    if cursor < end:
        keep.append(Segment(cursor, end))
    return keep
