from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class Segment:
    start: float
    end: float

    def validate(self, min_time: float, max_time: float) -> None:
        if self.start >= self.end:
            raise ValueError("Segment start must be before end.")
        if self.start < min_time or self.end > max_time:
            raise ValueError("Segment outside of log bounds.")


def normalize_segments(segments: Iterable[Segment]) -> List[Segment]:
    ordered = sorted(segments, key=lambda s: s.start)
    merged: List[Segment] = []
    for seg in ordered:
        if not merged:
            merged.append(seg)
            continue
        last = merged[-1]
        if seg.start <= last.end:
            merged[-1] = Segment(start=last.start, end=max(last.end, seg.end))
        else:
            merged.append(seg)
    return merged


def remove_segments(duration_start: float, duration_end: float, remove: Iterable[Segment]) -> List[Segment]:
    remove_list = normalize_segments(remove)
    keep: List[Segment] = []
    cursor = duration_start
    for seg in remove_list:
        if cursor < seg.start:
            keep.append(Segment(cursor, seg.start))
        cursor = max(cursor, seg.end)
    if cursor < duration_end:
        keep.append(Segment(cursor, duration_end))
    return keep


def contains_time(segments: Iterable[Segment], ts: float) -> bool:
    for seg in segments:
        if seg.start <= ts <= seg.end:
            return True
    return False


def remove_contains_time(segments: Iterable[Segment], ts: float) -> bool:
    for seg in segments:
        if seg.start <= ts <= seg.end:
            return True
    return False


def validate_segments(segments: Iterable[Segment], min_time: float, max_time: float) -> None:
    for seg in segments:
        seg.validate(min_time, max_time)
