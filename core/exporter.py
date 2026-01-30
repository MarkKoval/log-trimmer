from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .log_parser import DataFlashParser
from .segments import Segment, normalize_segments, remove_contains_time

logger = logging.getLogger(__name__)


@dataclass
class ExportProgress:
    current: int
    total: int


class DataFlashExporter:
    def __init__(self, source: Path) -> None:
        self.source = source

    def export(
        self,
        destination: Path,
        remove_segments: Iterable[Segment],
        progress_cb=None,
        total_messages: int | None = None,
    ) -> None:
        remove_list = normalize_segments(remove_segments)
        reader = DataFlashParser(self.source)
        index = 0
        total = total_messages or 0
        with open(destination, "wb") as dest_fp:
            for _, timestamp, msg in reader.iter_messages():
                if not remove_contains_time(remove_list, timestamp):
                    # DFReader exposes the raw bytes via the message for DataFlash logs.
                    raw = getattr(msg, "_buf", None)
                    if raw is not None:
                        dest_fp.write(raw)
                index += 1
                if progress_cb:
                    progress_cb(ExportProgress(current=index, total=total))
        logger.info("Exported trimmed log to %s", destination)
