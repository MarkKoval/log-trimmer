from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from .dataflash import DataFlashReader


@dataclass(frozen=True)
class TimeIndex:
    times: List[float]


def build_time_index(
    path: Path,
    max_points: int = 5000,
    progress: Optional[Callable[[int], None]] = None,
) -> TimeIndex:
    reader = DataFlashReader(path)
    times: List[float] = []
    for idx, record in enumerate(reader.iter_records()):
        if progress and idx % 5000 == 0:
            progress(idx)
        if idx % 5 != 0:
            continue
        times.append(record.timestamp)
        if len(times) >= max_points:
            break
    return TimeIndex(times=times)
