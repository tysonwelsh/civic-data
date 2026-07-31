# ordinances/ — availability & gap log

As-of 2026-07-13. Additive; no existing dataset modified.

## What exists
- **Municipal Code Online public S3 archive** — the city's signed adopted-ordinance PDFs at
  `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/bluffdale/ordinances/documents/`
  (enumerated verbatim into `archive_backcatalog.csv`; the source of the `high` corroboration
  + stored `raw/archive/*.pdf` + `text/*.txt` sidecars). Not bot-blocked; GET-only.
- **Council minutes** (`../meeting_minutes/`) — the backbone for number→date→subject→motion.

## Coverage
- **150 ordinances catalogued, 2020 floor → 2026.** 68 independently corroborated (`high`),
  75 motion-derived only (`within_source`), 3 `medium`, 4 `none`.

## Gaps / honest limits
- **Pre-2020 back-catalog** exists on the S3 archive but is out of the repo's 2020 floor —
  not harvested (documented scope limit, not a miss).
- **4 `none` unmatched ordinances** — real adopted ordinances (dates source-verified from the
  signed PDFs) with no motion in `all_votes.csv` citing their number. Two (2020-06 signs/
  outdoor-advertising, 2023-29 Draper boundary adjustment) are **land-use adoptions whose
  minutes motion omitted the ordinance number → flagged as EXTRACTION LEADS** for the vote
  pipeline, not fabricated links.
- **`within_source` is not corroboration** — 75 rows rest on the minutes alone; flagged so.
- American Legal / other codified-code hosts were not needed — the Municipal Code Online S3
  archive + the minutes backbone fully cover the 2020+ window.
