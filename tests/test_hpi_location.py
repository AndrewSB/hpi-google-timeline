from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import my.google_timeline.parser as timeline
from my.location.google_timeline import locations


FIXTURE = Path(__file__).parent / "fixtures" / "ios_timeline.json"


def test_all_projection_rules(monkeypatch) -> None:
    monkeypatch.setattr(timeline.config, "export_path", FIXTURE)
    results = list(locations())
    assert not any(isinstance(result, Exception) for result in results)
    assert len(results) == 5
    assert [(r.lat, r.lon) for r in results] == [
        (12.5, -34.25),
        (12.6, -34.3),
        (12.7, -34.4),
        (12.8, -34.5),
        (12.9, -34.6),
    ]
    assert results[3].dt == datetime(2026, 7, 2, 12, 35, tzinfo=timezone.utc)
    assert results[4].dt == datetime(2026, 7, 2, 12, 42, tzinfo=timezone.utc)
    assert all(r.accuracy is None and r.elevation is None for r in results)
    assert all(r.datasource == "google_timeline" for r in results)
    assert all(r.dt.tzinfo is not None for r in results)

