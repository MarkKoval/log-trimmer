from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from pymavlink import mavutil

from .segments import Segment, normalize_segments


LOGGER = logging.getLogger(__name__)


class DataFlashExporter:
    """Export DataFlash logs by streaming with pymavlink DFReader."""

    def __init__(self, source_path: Path) -> None:
        self.source_path = source_path

    def export(self, output_path: Path, remove_segments: Iterable[Segment]) -> None:
        segments = normalize_segments(remove_segments)
        LOGGER.info("Exporting log to %s with %d remove segments", output_path, len(segments))

        connection = mavutil.mavlink_connection(str(self.source_path), dialect="ardupilotmega")
        writer = mavutil.mavlink_connection(str(output_path), dialect="ardupilotmega",
                                            input=False, write=True)

        segment_index = 0
        current_segment = segments[segment_index] if segments else None

        while True:
            message = connection.recv_msg()
            if message is None:
                break

            timestamp = getattr(message, "_timestamp", None)
            if timestamp is None and hasattr(message, "time_us"):
                timestamp = float(message.time_us) / 1_000_000.0
            if timestamp is None and hasattr(message, "time_ms"):
                timestamp = float(message.time_ms) / 1_000.0

            if current_segment and timestamp is not None:
                if timestamp >= current_segment.end:
                    segment_index += 1
                    current_segment = segments[segment_index] if segment_index < len(segments) else None
                if current_segment and current_segment.start <= timestamp < current_segment.end:
                    continue

            writer.write(message)

        writer.close()
        connection.close()
