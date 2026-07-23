# Parser extraction decision

Date: 2026-07-23

## Decision

Use the extracted Life Portrait implementation as a dependency-free parser
core. Keep HPI configuration, discovery, result, statistics, and location
types in adapters. Use MIT licensing. Ship iOS-style array support in 0.1,
target Android-style objects for 0.2, and distribute from a signed Git tag
before publishing to PyPI while the API settles.

## Compatibility spike

The candidates were evaluated from their documented formats, APIs, licenses,
and synthetic-fixture behavior:

| Candidate | iOS array | All four kinds | Source-faithful library API | License fit | Decision |
| --- | --- | --- | --- | --- | --- |
| Life Atlas | Partial | No memories | No | MIT | Behavioral reference |
| Google Maps Timeline Viewer | Yes | Yes | Browser conversion API | GPL-3.0 | Research only |
| PixelPast | No | No memories | Derived event model | MIT | Android reference |
| gtlparser | No | No memories | Conversion-oriented | MIT | Do not adopt |

None meets the adoption gate. The extracted parser accepts the iOS array,
retains raw mappings and all four record kinds, records source indices, and
yields isolated errors. Private acceptance is intentionally separate from the
repository and must emit only content-free diagnostics.

## Revisit conditions

Re-evaluate PixelPast and gtlparser when Android support begins. Never copy
GPL Timeline Viewer code into this permissively licensed package. Recheck the
distribution name immediately before publication.

