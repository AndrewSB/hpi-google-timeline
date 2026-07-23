from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "private-acceptance"


def load_script():
    loader = importlib.machinery.SourceFileLoader("private_acceptance", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_private_diagnostics_contain_only_counts_and_bounds() -> None:
    module = load_script()
    result = module.diagnostics(Path(__file__).parent / "fixtures" / "ios_timeline.json")
    assert result == {
        "records": 4,
        "visit": 1,
        "activity": 1,
        "timelinePath": 1,
        "timelineMemory": 1,
        "start_dates": 3,
        "errors": 0,
        "earliest_start": "2026-07-01T10:00:00-04:00",
        "latest_start": "2026-07-03T00:00:00+00:00",
        "latest_end": "2026-07-03T01:00:00+00:00",
    }
