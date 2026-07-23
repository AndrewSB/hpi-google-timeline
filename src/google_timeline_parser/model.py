"""Public source-faithful Google Timeline models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterator


class ExportFormat(str, Enum):
    IOS = "ios"
    ANDROID = "android"


@dataclass(frozen=True)
class SourceRef:
    path: Path
    record_index: int = -1
    point_index: int | None = None


class TimelineError(Exception):
    """A parsing error with deterministic source context."""

    def __init__(self, message: str, *, source: SourceRef) -> None:
        self.message = message
        self.source = source
        super().__init__(message)

    def __str__(self) -> str:
        location = str(self.source.path)
        if self.source.record_index >= 0:
            location += f", record {self.source.record_index}"
        if self.source.point_index is not None:
            location += f", point {self.source.point_index}"
        return f"Google Timeline {location}: {self.message}"


def timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"invalid {label}: {value!r}") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone: {value!r}")
    return result


def number(value: Any, label: str) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as error:
            raise ValueError(f"{label} must be numeric or null") from error
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{label} must be numeric or null")
    return value


def geo(value: Any, label: str = "location") -> tuple[float, float] | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.startswith("geo:"):
        raise ValueError(f"{label} must use geo:latitude,longitude")
    try:
        latitude, longitude = value[4:].split(",", maxsplit=1)
        result = float(latitude), float(longitude)
    except ValueError as error:
        raise ValueError(f"invalid {label}: {value!r}") from error
    if not -90 <= result[0] <= 90 or not -180 <= result[1] <= 180:
        raise ValueError(f"{label} is outside valid latitude/longitude bounds")
    return result


@dataclass(frozen=True)
class PathPoint:
    raw: dict[str, Any]
    source: SourceRef

    @property
    def coordinates(self) -> tuple[float, float] | None:
        return geo(self.raw.get("point"), "path point")

    @property
    def minutes_from_start(self) -> int | float | None:
        return number(
            self.raw.get("durationMinutesOffsetFromStartTime"),
            "path point minute offset",
        )

    @property
    def explicit_time(self) -> datetime | None:
        value = self.raw.get("time", self.raw.get("timestamp"))
        return None if value is None else timestamp(value, "path point timestamp")


_KINDS = ("visit", "activity", "timelinePath", "timelineMemory")


@dataclass(frozen=True)
class Record:
    raw: dict[str, Any]
    source: SourceRef

    @property
    def kind(self) -> str:
        present = [key for key in _KINDS if key in self.raw]
        if len(present) != 1:
            raise ValueError(f"record must contain one known payload, found {len(present)}")
        return present[0]

    @property
    def start(self) -> datetime:
        return timestamp(self.raw.get("startTime"), "startTime")

    @property
    def end(self) -> datetime:
        return timestamp(self.raw.get("endTime"), "endTime")

    @property
    def payload(self) -> dict[str, Any] | list[Any]:
        value = self.raw.get(self.kind)
        if not isinstance(value, (dict, list)):
            raise TypeError(f"{self.kind} payload has invalid type")
        return value

    def _object_payload(self) -> dict[str, Any]:
        value = self.payload
        if not isinstance(value, dict):
            raise TypeError(f"{self.kind} payload must be an object")
        return value

    @property
    def probability(self) -> int | float | None:
        payload = self._object_payload()
        candidate = self._candidate()
        if candidate is not None and "probability" in candidate:
            return number(candidate.get("probability"), "candidate probability")
        return number(payload.get("probability"), "probability")

    def _candidate(self) -> dict[str, Any] | None:
        candidate = self._object_payload().get("topCandidate")
        if candidate is None:
            return None
        if not isinstance(candidate, dict):
            raise TypeError("topCandidate must be an object or null")
        return candidate

    def _candidate_string(self, key: str, label: str) -> str | None:
        candidate = self._candidate()
        if candidate is None:
            return None
        value = candidate.get(key)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{label} must be a string or null")
        return value

    @property
    def place_id(self) -> str | None:
        return self._candidate_string("placeID", "placeID")

    @property
    def semantic_type(self) -> str | None:
        return self._candidate_string("semanticType", "semanticType")

    @property
    def coordinates(self) -> tuple[float, float] | None:
        candidate = self._candidate()
        if candidate is None:
            return None
        return geo(candidate.get("placeLocation"), "candidate location")

    @property
    def activity_type(self) -> str | None:
        return self._candidate_string("type", "activity type")

    @property
    def activity_start_coordinates(self) -> tuple[float, float] | None:
        return geo(self._object_payload().get("start"), "activity start")

    @property
    def activity_end_coordinates(self) -> tuple[float, float] | None:
        return geo(self._object_payload().get("end"), "activity end")

    @property
    def distance_meters(self) -> int | float | None:
        return number(self._object_payload().get("distanceMeters"), "distanceMeters")

    def path_points(self) -> Iterator[PathPoint]:
        if self.kind != "timelinePath":
            return
        payload = self.payload
        if not isinstance(payload, list):
            raise TypeError("timelinePath payload must be an array")
        for index, raw in enumerate(payload):
            source = SourceRef(self.source.path, self.source.record_index, index)
            if not isinstance(raw, dict):
                raise TimelineError("path point must be an object", source=source)
            yield PathPoint(raw, source)

    @property
    def destination_ids(self) -> tuple[str, ...]:
        values = self._object_payload().get("destinations", [])
        if not isinstance(values, list):
            raise TypeError("destinations must be an array")
        result: list[str] = []
        for value in values:
            if not isinstance(value, dict) or not isinstance(value.get("identifier"), str):
                raise TypeError("destination must contain an identifier")
            result.append(value["identifier"])
        return tuple(result)

    @property
    def distance_from_origin_kms(self) -> int | float | None:
        return number(self._object_payload().get("distanceFromOriginKms"), "distanceFromOriginKms")


__all__ = ["ExportFormat", "PathPoint", "Record", "SourceRef", "TimelineError"]
