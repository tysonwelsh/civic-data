# ordinances/ — Bluffdale adopted zoning/land-use ordinances

Additive dataset (`expand-city-sources` Source 3), built 2026-07-12/13. Maps adopted
**Ordinance #YYYY-NN → adoption date → the council motion that passed it**, so a vote in
`../meeting_minutes/all_votes.csv` links to what the ordinance did. **150 ordinances**
(2020+ floor; 69 land-use). Regenerate: `python3 build_index.py` (idempotent).

## Two sources, two confidence semantics (READ THIS)

1. **Minutes backbone (primary).** Every council motion citing an `Ordinance <YYYY-NN>`
   (regex tolerant of `No.`/`Number`/`#`/no-space) yields a number→date→subject→motion row
   DERIVED FROM THE MOTION. These are **`within_source`** — high *by construction*, **NOT an
   independent cross-match** (the minutes are the only witness). Their `source_url` points at
   the minutes doc (the within-source pointer); `path` is blank (no separate PDF on disk).
2. **Municipal Code Online S3 archive (independent corroboration).** The city's public
   signed-ordinance archive
   (`s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/bluffdale/ordinances/documents/`,
   enumerated into `archive_backcatalog.csv`). A motion-cited number that ALSO has an adopted
   PDF there is upgraded to **`high`** (stored in `raw/archive/<num>.pdf` + a `text/<num>.txt`
   sidecar that feeds `cities.db` `fts_ordinance`).

Archived 2020+ ordinances **not** cited in any motion are matched by adoption-date + subject
where possible (**`medium`**) or left **`none`** (unmatched) — FLAGGED extraction leads,
never force-matched.

## Counts (as-of 2026-07-13)

- **150 ordinances**: `high` 68 · `within_source` 75 · `medium` 3 · `none` 4.
- **Land-use: 69** (`land_use=yes`; keyword classifier over motion + sidecar title, with a
  non-land-use guard for budget/fee/appointment/etc.).
- Formats: born-digital `text` + `scanned` (OCR'd, listed in `build_index.py` `SCANNED`);
  `within_source` rows are `format=na` (no PDF).

## The 4 `none` (unmatched) rows — dates source-verified, not motion-linked

All four are real adopted ordinances whose **adoption date was read from the signed PDF**
(Read-tool, 2026-07-13), since no council motion in `all_votes.csv` cites their number:
- **2020-01** (procurement) — 2020-01-29 ("PASSED AND ADOPTED: January 29, 2020").
- **2020-06** (Signs/Outdoor Advertising, LAND USE) — 2020-03-11 ("PASSED AND DATED: March
  11, 2020"); the signed PDF even shows a full 5-0 Aye roll — a real adopted land-use
  ordinance whose minutes motion omitted the number → **extraction lead**.
- **2023-29** (Bluffdale–Draper boundary adjustment, LAND USE) — 2023-12-13 (the council
  meeting whose agenda item 8.2 was "Consideration and Vote on Ordinance 2023-29"; matches
  the signed "December 2023") → **extraction lead**.
- **2025-17** (Healthy Bluffdale Coalition term) — 2025-06-11 ("PASSED AND APPROVED: June 11,
  2025"); only the minutes-approval motion was extracted that day → possible extraction gap.

For `none` rows `matched_motion_date` is blank (the date is source-verified, NOT motion-linked)
so they are never read as corroborated links.

## Schema

`index.csv` — §9 ordinances contract header (`ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path`) + linkage cols
`land_use, result, matched_motion_date, matched_motion_no, match_confidence, linkage_note,
minutes_source`. **Never force a match** — an unmatched ordinance keeps `match_confidence=none`
and blank match fields. Corrections regenerate from source; do not hand-edit `index.csv`.

## Caveats

- **`within_source` ≠ corroborated.** 75 of 150 rows are motion-derived only — treat as
  suggestive, not independently confirmed. Only the 68 `high` rows have a second source.
- **2020+ floor.** A ~pre-2020 back-catalog exists on the S3 archive but is out of scope.
- Ordinance vs Resolution numbers are separate sequences — the join keys on the instrument
  word + number in the motion text.
