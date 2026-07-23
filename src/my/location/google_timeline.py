"""Project Google Timeline records into HPI Location observations."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta

from google_timeline_parser import TimelineError
from my.core import Res
from my.google_timeline.parser import records
from my.location.common import Location


def _location(coordinates: tuple[float, float], dt) -> Location:
    latitude, longitude = coordinates
    return Location(
        lat=latitude,
        lon=longitude,
        dt=dt,
        accuracy=None,
        elevation=None,
        datasource="google_timeline",
    )


def locations() -> Iterator[Res[Location]]:
    for result in records():
        if isinstance(result, Exception):
            yield result
            continue
        try:
            if result.kind == "visit":
                if (coordinates := result.coordinates) is not None:
                    yield _location(coordinates, result.start)
            elif result.kind == "activity":
                if (coordinates := result.activity_start_coordinates) is not None:
                    yield _location(coordinates, result.start)
                if (coordinates := result.activity_end_coordinates) is not None:
                    yield _location(coordinates, result.end)
            elif result.kind == "timelinePath":
                for point in result.path_points():
                    if (coordinates := point.coordinates) is None:
                        continue
                    dt = point.explicit_time
                    if dt is None:
                        offset = point.minutes_from_start
                        if offset is None:
                            continue
                        dt = result.start + timedelta(minutes=offset)
                    yield _location(coordinates, dt)
        except Exception as error:
            yield TimelineError(
                f"location projection: {type(error).__name__}: {error}",
                source=result.source,
            )


__all__ = ["locations"]

