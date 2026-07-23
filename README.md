# hpi-google-timeline

Dependency-light, source-faithful parsing of current Google Timeline phone
exports, plus optional [HPI](https://github.com/karlicoss/HPI) record and
location modules.

Version 0.1 supports the iOS-style top-level array containing `visit`,
`activity`, `timelinePath`, and `timelineMemory` records. Android
`semanticSegments` exports are detected and reported as unsupported so they
cannot be silently misparsed; support is targeted for 0.2.

## Standalone parser

```python
from pathlib import Path
from google_timeline_parser import TimelineError, parse_file

for result in parse_file(Path("location-history.json")):
    if isinstance(result, TimelineError):
        print(result)
    else:
        print(result.kind, result.start, result.raw)
```

The core package uses only the Python standard library. Records and path
points retain their original mappings and deterministic source indices.
Parsing errors are yielded alongside valid records.

## HPI modules

Install the optional dependency and configure HPI:

```python
# ~/.config/my/my/config.py
class google_timeline:
    export_path = "/path/to/location-history.json"
```

Then use `my.google_timeline.parser.records()` for source records or
`my.location.google_timeline.locations()` for ordinary HPI location
observations. Provider confidence is not spatial accuracy, so projected
locations always use `accuracy=None`.

## Privacy

Google Timeline exports are highly sensitive. Never commit exports, raw
records, coordinates, place IDs, or filenames containing personal data. This
repository contains synthetic fixtures only. Acceptance against a private
export must print content-free counts and timestamp bounds only.

Run the guarded acceptance command without copying an export into the repo:

```console
bin/private-acceptance /private/path/location-history.json
```

See [docs/decision-record.md](docs/decision-record.md) for the extraction and
compatibility decision.
