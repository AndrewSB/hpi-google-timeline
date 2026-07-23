"""Format detection and isolated parsing for Google Timeline exports."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .model import ExportFormat, Record, SourceRef, TimelineError

Result = Record | TimelineError


def detect_format(value: object) -> ExportFormat:
    if isinstance(value, list):
        return ExportFormat.IOS
    if isinstance(value, dict) and any(
        key in value for key in ("semanticSegments", "rawSignals", "userLocationProfile")
    ):
        return ExportFormat.ANDROID
    raise ValueError("unrecognized Google Timeline export format")


def _validate(record: Record) -> None:
    kind = record.kind
    record.start
    record.end
    if kind == "visit":
        record.probability
        record.place_id
        record.semantic_type
        record.coordinates
    elif kind == "activity":
        record.probability
        record.activity_type
        record.activity_start_coordinates
        record.activity_end_coordinates
        record.distance_meters
    elif kind == "timelinePath":
        for point in record.path_points():
            point.coordinates
            point.minutes_from_start
            point.explicit_time
    else:
        record.destination_ids
        record.distance_from_origin_kms


def parse_value(value: object, *, source: SourceRef) -> Iterator[Result]:
    try:
        export_format = detect_format(value)
    except Exception as error:
        yield TimelineError(f"{type(error).__name__}: {error}", source=source)
        return
    if export_format is ExportFormat.ANDROID:
        yield TimelineError("Android semanticSegments exports are not supported in version 0.1", source=source)
        return
    assert isinstance(value, list)
    for index, raw in enumerate(value):
        record_source = SourceRef(source.path, index)
        if not isinstance(raw, dict):
            yield TimelineError("record must be an object", source=record_source)
            continue
        record = Record(raw, record_source)
        try:
            _validate(record)
        except Exception as error:
            if isinstance(error, TimelineError):
                yield error
            else:
                yield TimelineError(f"{type(error).__name__}: {error}", source=record_source)
            continue
        yield record


def parse_file(path: Path) -> Iterator[Result]:
    source = SourceRef(Path(path))
    try:
        value: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as error:
        yield TimelineError(f"{type(error).__name__}: {error}", source=source)
        return
    yield from parse_value(value, source=source)


__all__ = ["Result", "detect_format", "parse_file", "parse_value"]

