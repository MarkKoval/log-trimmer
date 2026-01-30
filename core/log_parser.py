from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from pymavlink import DFReader

logger = logging.getLogger(__name__)


@dataclass
class LogInfo:
    path: Path
    size_bytes: int
    message_count: int
    start_time: float
    end_time: float
    log_type: str


@dataclass
class TimeSeries:
    name: str
    times: List[float]
    values: List[float]


@dataclass
class LogIndex:
    timestamps: List[float]
    message_numbers: List[int]

    @property
    def start(self) -> float:
        return self.timestamps[0] if self.timestamps else 0.0

    @property
    def end(self) -> float:
        return self.timestamps[-1] if self.timestamps else 0.0


class DataFlashParser:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._reader: Optional[DFReader.DFReader_binary] = None

    def _open(self) -> DFReader.DFReader_binary:
        if self._reader is None:
            self._reader = DFReader.DFReader_binary(str(self.path))
        return self._reader

    def iter_messages(self) -> Iterable[Tuple[int, float, object]]:
        reader = self._open()
        msg_index = 0
        while True:
            try:
                msg = reader.recv_msg()
            except Exception as exc:  # noqa: BLE001 - log and stop on parsing issues
                logger.exception("Error parsing DataFlash log: %s", exc)
                break
            if msg is None:
                break
            timestamp = extract_timestamp(msg, msg_index)
            yield msg_index, timestamp, msg
            msg_index += 1

    def build_index(self, stride: int = 50) -> LogIndex:
        timestamps: List[float] = []
        message_numbers: List[int] = []
        for msg_index, timestamp, _ in self.iter_messages():
            if msg_index % stride == 0:
                timestamps.append(timestamp)
                message_numbers.append(msg_index)
        if timestamps and timestamps[-1] != timestamp:
            timestamps.append(timestamp)
            message_numbers.append(msg_index)
        return LogIndex(timestamps=timestamps, message_numbers=message_numbers)

    def summarize(self) -> LogInfo:
        size_bytes = self.path.stat().st_size
        start_time = 0.0
        end_time = 0.0
        count = 0
        for msg_index, timestamp, _ in self.iter_messages():
            if count == 0:
                start_time = timestamp
            end_time = timestamp
            count = msg_index + 1
        log_type = "DataFlash"
        return LogInfo(
            path=self.path,
            size_bytes=size_bytes,
            message_count=count,
            start_time=start_time,
            end_time=end_time,
            log_type=log_type,
        )

    def collect_series(self, max_points: int = 6000) -> Dict[str, TimeSeries]:
        series: Dict[str, TimeSeries] = {
            "ALT": TimeSeries("ALT", [], []),
            "GPS_SPEED": TimeSeries("GPS Speed", [], []),
            "ATT_ROLL": TimeSeries("ATT Roll", [], []),
            "ATT_PITCH": TimeSeries("ATT Pitch", [], []),
            "ATT_YAW": TimeSeries("ATT Yaw", [], []),
            "THR": TimeSeries("Throttle", [], []),
        }
        total = 0
        for _, timestamp, msg in self.iter_messages():
            total += 1
            if total % 2 == 0:
                # light downsampling
                _append_series(series, timestamp, msg)
            if total >= max_points:
                break
        return series


def _append_series(series: Dict[str, TimeSeries], timestamp: float, msg: object) -> None:
    msg_type = msg.get_type()
    if msg_type == "BARO":
        value = getattr(msg, "Alt", None)
        if value is not None:
            series["ALT"].times.append(timestamp)
            series["ALT"].values.append(float(value))
    elif msg_type == "GPS":
        value = getattr(msg, "Spd", None)
        if value is not None:
            series["GPS_SPEED"].times.append(timestamp)
            series["GPS_SPEED"].values.append(float(value))
    elif msg_type == "ATT":
        roll = getattr(msg, "Roll", None)
        pitch = getattr(msg, "Pitch", None)
        yaw = getattr(msg, "Yaw", None)
        if roll is not None:
            series["ATT_ROLL"].times.append(timestamp)
            series["ATT_ROLL"].values.append(float(roll))
        if pitch is not None:
            series["ATT_PITCH"].times.append(timestamp)
            series["ATT_PITCH"].values.append(float(pitch))
        if yaw is not None:
            series["ATT_YAW"].times.append(timestamp)
            series["ATT_YAW"].values.append(float(yaw))
    elif msg_type == "RCOU":
        thr = getattr(msg, "C3", None)
        if thr is not None:
            series["THR"].times.append(timestamp)
            series["THR"].values.append(float(thr))


def extract_timestamp(msg: object, fallback_index: int) -> float:
    for field in ("TimeUS", "time_usec"):
        value = getattr(msg, field, None)
        if value is not None:
            return float(value) / 1_000_000.0
    for field in ("time_boot_ms", "TimeMS"):
        value = getattr(msg, field, None)
        if value is not None:
            return float(value) / 1_000.0
    return float(fallback_index)
