from __future__ import annotations

from pathlib import Path

import my.google_timeline.parser as timeline
from google_timeline_parser import Record


FIXTURE = Path(__file__).parent / "fixtures" / "ios_timeline.json"


def test_hpi_iterators_and_content_free_stats(monkeypatch) -> None:
    monkeypatch.setattr(timeline.config, "export_path", FIXTURE)
    assert len([r for r in timeline.visits() if isinstance(r, Record)]) == 1
    assert len([r for r in timeline.activities() if isinstance(r, Record)]) == 1
    assert len([r for r in timeline.paths() if isinstance(r, Record)]) == 1
    assert len([r for r in timeline.memories() if isinstance(r, Record)]) == 1
    assert timeline.stats() == {
        "visit": 1,
        "activity": 1,
        "timelinePath": 1,
        "timelineMemory": 1,
        "records": 4,
        "start_dates": 3,
        "errors": 0,
        "unknown_fields": 1,
        "earliest_start": "2026-07-01T10:00:00-04:00",
        "latest_start": "2026-07-03T00:00:00+00:00",
        "latest_end": "2026-07-03T01:00:00+00:00",
    }
    assert timeline.common_locations() == {"synthetic-place-1": 1}

