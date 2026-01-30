from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, Optional, Tuple

from pymavlink import DFReader

logger = logging.getLogger(__name__)

TimeExtractor = Callable[[object], float]


@dataclass(frozen=True)
class LogInfo:
    path: Path
    size_bytes: int
    message_count: int
    time_range: Tuple[float, float]
    has_time: bool


@dataclass(frozen=True)
class LogRecord:
    timestamp: float
    offset_start: int
    offset_end: int
    message: object


def _extract_timestamp(msg: object) -> Optional[float]:
    """Extract timestamp from a DataFlash message.

    Uses common ArduPilot fields. Returns seconds if available.
    """
    for field, divisor in (
        ("TimeUS", 1_000_000.0),
        ("TimeMS", 1_000.0),
        ("time_usec", 1_000_000.0),
        ("time_boot_ms", 1_000.0),
    ):
        if hasattr(msg, field):
            value = getattr(msg, field)
            if value is not None:
                return float(value) / divisor
    return None


class DataFlashReader:
    """Streaming reader for ArduPilot DataFlash (.BIN).

    Uses pymavlink DFReader to parse DataFlash logs while preserving
    file offsets for exporting raw records.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def _open_reader(self):
        log_file = open(self.path, "rb")
        # DFReader_binary provides robust parsing for DataFlash BIN logs.
        reader = DFReader.DFReader_binary(log_file, zero_time_base=True)
        return log_file, reader

    def iter_records(self) -> Iterator[LogRecord]:
        log_file, reader = self._open_reader()
        fallback_counter = 0.0
        try:
            while True:
                offset_start = log_file.tell()
                msg = reader.read_next()
                if msg is None:
                    break
                offset_end = log_file.tell()
                timestamp = _extract_timestamp(msg)
                if timestamp is None:
                    timestamp = fallback_counter
                    fallback_counter += 1.0
                yield LogRecord(timestamp, offset_start, offset_end, msg)
        finally:
            log_file.close()

    def get_info(self, progress: Optional[Callable[[int], None]] = None) -> LogInfo:
        size_bytes = self.path.stat().st_size
        message_count = 0
        start_time: Optional[float] = None
        end_time: Optional[float] = None
        has_time = False
        for record in self.iter_records():
            message_count += 1
            if progress and message_count % 5000 == 0:
                progress(message_count)
            if start_time is None:
                start_time = record.timestamp
            end_time = record.timestamp
            has_time = has_time or _extract_timestamp(record.message) is not None
        if start_time is None or end_time is None:
            start_time = 0.0
            end_time = 0.0
        return LogInfo(
            path=self.path,
            size_bytes=size_bytes,
            message_count=message_count,
            time_range=(float(start_time), float(end_time)),
            has_time=has_time,
        )


class DataFlashExporter:
    def __init__(self, source: Path) -> None:
        self.source = source

    def export(self, destination: Path, remove_segments: Iterable[Tuple[float, float]],
               progress: Optional[Callable[[int], None]] = None) -> None:
        remove_segments = list(remove_segments)
        reader = DataFlashReader(self.source)

        with open(self.source, "rb") as raw_file, open(destination, "wb") as out_file:
            for index, record in enumerate(reader.iter_records()):
                if progress and index % 5000 == 0:
                    progress(index)
                if _is_removed(record.timestamp, remove_segments):
                    continue
                raw_file.seek(record.offset_start)
                chunk = raw_file.read(record.offset_end - record.offset_start)
                out_file.write(chunk)


def _is_removed(timestamp: float, remove_segments: Iterable[Tuple[float, float]]) -> bool:
    for start, end in remove_segments:
        if start <= timestamp <= end:
            return True
    return False


def read_channel_samples(
    path: Path,
    channels: Dict[str, Tuple[str, str]],
    max_points: int = 5000,
) -> Dict[str, Tuple[list, list]]:
    """Read time-series samples for selected channels.

    channels: mapping label -> (message_type, field_name)
    Returns mapping label -> (times, values)
    """
    reader = DataFlashReader(path)
    samples: Dict[str, Tuple[list, list]] = {
        label: ([], []) for label in channels
    }
    message_counts: Dict[str, int] = {label: 0 for label in channels}

    for record in reader.iter_records():
        msg = record.message
        msg_type = getattr(msg, "get_type", lambda: "")()
        for label, (expected_type, field) in channels.items():
            if msg_type != expected_type:
                continue
            if not hasattr(msg, field):
                continue
            message_counts[label] += 1
            if message_counts[label] % 3 != 0:
                continue
            times, values = samples[label]
            times.append(record.timestamp)
            values.append(float(getattr(msg, field)))
            if len(times) >= max_points:
                return samples
    return samples
