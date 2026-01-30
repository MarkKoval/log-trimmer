from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class Segment:
    start: float
    end: float

    def is_valid(self) -> bool:
        return self.start < self.end

    def clamp(self, min_value: float, max_value: float) -> "Segment":
        return Segment(start=max(self.start, min_value), end=min(self.end, max_value))


class SegmentError(ValueError):
    pass


def normalize_segments(segments: Iterable[Segment]) -> List[Segment]:
    sorted_segments = sorted(segments, key=lambda s: (s.start, s.end))
    merged: List[Segment] = []
    for segment in sorted_segments:
        if not segment.is_valid():
            raise SegmentError(f"Invalid segment: {segment}")
        if not merged:
            merged.append(segment)
            continue
        last = merged[-1]
        if segment.start <= last.end:
            merged[-1] = Segment(start=last.start, end=max(last.end, segment.end))
        else:
            merged.append(segment)
    return merged


def clamp_segments(
    segments: Iterable[Segment], min_value: float, max_value: float
) -> List[Segment]:
    clamped = [segment.clamp(min_value, max_value) for segment in segments]
    return [segment for segment in clamped if segment.is_valid()]


def invert_segments(
    segments: Iterable[Segment], min_value: float, max_value: float
) -> List[Segment]:
    normalized = normalize_segments(clamp_segments(segments, min_value, max_value))
    inverted: List[Segment] = []
    cursor = min_value
    for segment in normalized:
        if cursor < segment.start:
            inverted.append(Segment(cursor, segment.start))
        cursor = segment.end
    if cursor < max_value:
        inverted.append(Segment(cursor, max_value))
    return inverted


def validate_bounds(start: float, end: float) -> None:
    if start >= end:
        raise SegmentError("Start time must be smaller than end time")


def apply_trim(
    keep_segment: Segment, min_value: float, max_value: float
) -> List[Segment]:
    validate_bounds(keep_segment.start, keep_segment.end)
    keep_segment = keep_segment.clamp(min_value, max_value)
    return invert_segments([keep_segment], min_value, max_value)


def apply_cut(
    remove_segments: Iterable[Segment], min_value: float, max_value: float
) -> List[Segment]:
    return normalize_segments(clamp_segments(remove_segments, min_value, max_value))


def serialize_segments(segments: Iterable[Segment]) -> List[Tuple[float, float]]:
    return [(segment.start, segment.end) for segment in segments]
