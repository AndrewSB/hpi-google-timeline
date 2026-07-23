"""HPI discovery and diagnostics for Google Timeline phone exports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import my.config
from google_timeline_parser import Record, SourceRef, TimelineError, parse_file
from my.core import Paths, Res, Stats, get_files, make_config


_user_config = getattr(my.config, "google_timeline", object)


@dataclass
class google_timeline(_user_config):  # type: ignore[misc, valid-type]
    export_path: Paths = ""


config = make_config(google_timeline)
_KINDS = ("visit", "activity", "timelinePath", "timelineMemory")
_COMMON_KEYS = {"startTime", "endTime"}


def inputs() -> Sequence[Path]:
    return get_files(config.export_path, guess_compression=False)


def records() -> Iterator[Res[Record]]:
    try:
        paths = inputs()
    except Exception as error:
        yield TimelineError(
            f"input discovery: {type(error).__name__}: {error}",
            source=SourceRef(Path("<config>")),
        )
        return
    for path in paths:
        yield from parse_file(Path(path))


def _kind(kind: str) -> Iterator[Res[Record]]:
    for result in records():
        if isinstance(result, Exception) or result.kind == kind:
            yield result


def visits() -> Iterator[Res[Record]]:
    yield from _kind("visit")


def activities() -> Iterator[Res[Record]]:
    yield from _kind("activity")


def paths() -> Iterator[Res[Record]]:
    yield from _kind("timelinePath")


def memories() -> Iterator[Res[Record]]:
    yield from _kind("timelineMemory")


def common_locations() -> dict[str, int]:
    counts: Counter[str] = Counter()
    for result in visits():
        if isinstance(result, Exception):
            continue
        key = result.place_id
        if key is None and (coordinates := result.coordinates) is not None:
            key = f"geo:{coordinates[0]},{coordinates[1]}"
        if key is not None:
            counts[key] += 1
    return dict(counts)


def stats() -> Stats:
    counts: Stats = {kind: 0 for kind in _KINDS}
    counts.update({"records": 0, "start_dates": 0, "errors": 0, "unknown_fields": 0})
    dates: set[str] = set()
    starts: list[datetime] = []
    ends: list[datetime] = []
    for result in records():
        if isinstance(result, Exception):
            counts["errors"] += 1
            continue
        counts["records"] += 1
        counts[result.kind] += 1
        starts.append(result.start)
        ends.append(result.end)
        dates.add(result.start.date().isoformat())
        counts["unknown_fields"] += len(set(result.raw) - _COMMON_KEYS - {result.kind})
    counts["start_dates"] = len(dates)
    counts["earliest_start"] = min(starts).isoformat() if starts else None
    counts["latest_start"] = max(starts).isoformat() if starts else None
    counts["latest_end"] = max(ends).isoformat() if ends else None
    return counts


__all__ = [
    "activities",
    "common_locations",
    "config",
    "google_timeline",
    "inputs",
    "memories",
    "paths",
    "records",
    "stats",
    "visits",
]
