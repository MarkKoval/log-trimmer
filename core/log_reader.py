from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from pymavlink import mavutil


LOGGER = logging.getLogger(__name__)


@dataclass
class LogIndexPoint:
    timestamp: float
    file_offset: int


@dataclass
class LogSummary:
    path: Path
    message_count: int
    start_time: float
    end_time: float
    duration: float
    index: List[LogIndexPoint] = field(default_factory=list)
    sample_channels: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)


class DataFlashLogReader:
    """Stream DataFlash logs using pymavlink DFReader.

    DFReader/mavutil is used to parse the binary messages without loading the
    whole file into memory.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def _message_time(self, message) -> Optional[float]:
        if hasattr(message, "time_us"):
            return float(message.time_us) / 1_000_000.0
        if hasattr(message, "time_ms"):
            return float(message.time_ms) / 1_000.0
        if hasattr(message, "TimeUS"):
            return float(message.TimeUS) / 1_000_000.0
        if hasattr(message, "_timestamp"):
            return float(message._timestamp)
        return None

    def iter_messages(self) -> Iterator[Tuple[float, object, int]]:
        connection = mavutil.mavlink_connection(str(self.path), dialect="ardupilotmega")
        while True:
            offset = connection.file.tell()
            message = connection.recv_msg()
            if message is None:
                break
            timestamp = self._message_time(message)
            if timestamp is None:
                continue
            yield timestamp, message, offset

    def build_index(self, sample_stride: int = 20) -> LogSummary:
        message_count = 0
        index: List[LogIndexPoint] = []
        samples: Dict[str, List[Tuple[float, float]]] = {
            "ALT": [],
            "GPS_SPEED": [],
            "THR": [],
            "ROLL": [],
            "PITCH": [],
            "YAW": [],
        }
        start_time: Optional[float] = None
        end_time: Optional[float] = None

        for timestamp, message, offset in self.iter_messages():
            message_count += 1
            if start_time is None:
                start_time = timestamp
            end_time = timestamp

            if message_count % sample_stride == 0:
                index.append(LogIndexPoint(timestamp=timestamp, file_offset=offset))

            msg_type = message.get_type()
            if msg_type == "BARO" and hasattr(message, "Alt"):
                samples["ALT"].append((timestamp, float(message.Alt)))
            elif msg_type == "GPS" and hasattr(message, "Spd"):
                samples["GPS_SPEED"].append((timestamp, float(message.Spd)))
            elif msg_type in {"RCOU", "RCIN"} and hasattr(message, "C3"):
                samples["THR"].append((timestamp, float(message.C3)))
            elif msg_type == "ATT" and hasattr(message, "Roll"):
                samples["ROLL"].append((timestamp, float(message.Roll)))
                samples["PITCH"].append((timestamp, float(message.Pitch)))
                samples["YAW"].append((timestamp, float(message.Yaw)))

        if start_time is None or end_time is None:
            raise ValueError("No valid timestamps found in log")

        return LogSummary(
            path=self.path,
            message_count=message_count,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            index=index,
            sample_channels=samples,
        )
