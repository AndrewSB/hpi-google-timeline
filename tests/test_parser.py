from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from google_timeline_parser import ExportFormat, Record, SourceRef, TimelineError
from google_timeline_parser import detect_format, parse_file, parse_value


FIXTURES = Path(__file__).parent / "fixtures"


def values(results):
    return [result for result in results if isinstance(result, Record)]


def test_detects_both_current_export_families() -> None:
    assert detect_format([]) is ExportFormat.IOS
    assert detect_format({"semanticSegments": []}) is ExportFormat.ANDROID


def test_records_preserve_raw_and_expose_typed_fields() -> None:
    visit, activity, path, memory = values(parse_file(FIXTURES / "ios_timeline.json"))
    assert visit.raw["futureField"] == {"preserved": True}
    assert visit.source.record_index == 0
    assert visit.start.utcoffset() == -timedelta(hours=4)
    assert visit.coordinates == (12.5, -34.25)
    assert visit.probability == 0.9
    assert activity.activity_start_coordinates == (12.6, -34.3)
    assert activity.activity_end_coordinates == (12.7, -34.4)
    assert activity.distance_meters == 123.5
    first, second = list(path.path_points())
    assert first.minutes_from_start == 5.0
    assert first.source.point_index == 0
    assert second.explicit_time is not None
    assert memory.destination_ids == ("synthetic-destination-1",)


def test_errors_are_isolated_and_keep_context() -> None:
    source = SourceRef(Path("synthetic.json"))
    results = list(parse_value([
        None,
        {"startTime": "bad", "endTime": "2026-01-01T00:00:00Z", "visit": {}},
        {"startTime": "2026-01-01T00:00:00Z", "endTime": "2026-01-01T01:00:00Z", "activity": {}},
    ], source=source))
    assert [type(result) for result in results] == [TimelineError, TimelineError, Record]
    assert results[0].source.record_index == 0
    assert results[1].source.record_index == 1


def test_rejects_naive_timestamp_and_bad_coordinate() -> None:
    source = SourceRef(Path("synthetic.json"))
    results = list(parse_value([
        {"startTime": "2026-01-01T00:00:00", "endTime": "2026-01-01T01:00:00Z", "visit": {}},
        {"startTime": "2026-01-01T00:00:00Z", "endTime": "2026-01-01T01:00:00Z", "visit": {"topCandidate": {"placeLocation": "bad"}}},
    ], source=source))
    assert all(isinstance(result, TimelineError) for result in results)


def test_rejects_malformed_candidate_but_keeps_following_record() -> None:
    source = SourceRef(Path("synthetic.json"))
    results = list(parse_value([
        {"startTime": "2026-01-01T00:00:00Z", "endTime": "2026-01-01T01:00:00Z", "visit": {"topCandidate": "bad"}},
        {"startTime": "2026-01-01T01:00:00Z", "endTime": "2026-01-01T02:00:00Z", "visit": {}},
    ], source=source))
    assert isinstance(results[0], TimelineError)
    assert isinstance(results[1], Record)


def test_android_is_explicitly_unsupported_in_v01() -> None:
    [result] = list(parse_file(FIXTURES / "android_timeline.json"))
    assert isinstance(result, TimelineError)
    assert "not supported" in str(result)
