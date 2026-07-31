# ordinances/ — SLC adopted zoning/land-use ordinances (2020–2026)

Additive dataset. Number→date→subject→motion index of **Salt Lake City adopted
ordinances** (`Ordinance NN of YYYY`), linked to the adopting **Council** motion in
`../meeting_minutes/all_votes.csv`. Read `AVAILABILITY.md` for coverage, counts, and the
independent-source situation before quoting anything.

## Files

```
index.csv     464 adopted ordinances, one row each (2020–2026; 2026 = 1–40 complete)
raw/          7 independent corroboration docs + _fetch_log.jsonl (provenance)
AVAILABILITY.md   coverage, confidence tiers, gaps, the 2021+ vote floor, audit signal
```

There is **no `text/` corpus** — this dataset is an index, not an ordinance full-text
store. Titles/subjects come from the already-audited minutes vote layer (2021+) or 2020
OCR minutes snippets; the signed ordinance PDFs live in the City Recorder's JS-gated
Laserfiche archive (`webdme.slcgov.com/OrdinancesResolutions/`, not GET-harvestable).

## index.csv columns

Standard required: `date,title,source_url,retrieved_date,format,extraction_method`.
Plus: `ordinance_no` (`NN of YYYY`), `adoption_date`, `path` (→ `raw/` doc where
corroborated), `land_use` (yes/no), `result` (verbatim vote tally string),
`matched_motion_date`, `matched_motion_no`, `match_confidence`, `body`
(always `Council`), `n_vote_events`, `independent_source`, `minutes_path`, `note`.

## How to use it

- **Cardinal rule:** `match_confidence` gates trust. `high` (9) = number in an independent
  doc AND a motion. `medium` (49) = land-use ord whose date+subject matches the SLC
  Planning adopted-zoning list. **`within_source` (352, dominant)** = minutes-motion text
  only, NOT independently corroborated — report as minutes-attested. `none` (54) = no
  matched vote row (empty match fields).
- **Link to the vote:** join `(matched_motion_date, matched_motion_no)` back to
  `../meeting_minutes/all_votes.csv` for the full roll call. All ordinance motions are
  `body=Council` (RDA/CRA/LBA pass resolutions, never `Ordinance NN of YYYY`).
- **Land-use questions:** filter `land_use=yes` (151). Corroborate against
  `raw/slc_planning_adopted_zoning_amendments.html` for the Planning Division's own list.
- **2021+ vote floor:** the 48 · 2020 ordinances are `format=scanned`, `confidence=none`
  (no votes existed to link). Don't read that as a defect.
- **Audit hook:** the only 2021+ adopted numbers without a per-number vote row are
  **26–31 of 2021** (FY22 budget appropriations, consent-folded under the omnibus budget
  motion) — see `note`. No land-use adoption is missing from the vote layer.

## Regenerating

Derived from `../meeting_minutes/all_votes.csv` + the minutes markdown/OCR, corroborated
against `raw/`. Never hand-edit `index.csv`; the confidence tiers and the independent
number/date sets are encoded in the build (kept with the expand-city-sources working
files). `raw/` originals are retained verbatim — never rewrite them.

## Provenance / honesty

- American Legal is 403-blocked; the recorder's Laserfiche archive exists but is JS/cookie
  -gated; PMN body-1788 search is JS/opaque. Corroboration is therefore a retrieved sample,
  not a full harvest — the dominant tier is intentionally `within_source`. See `AVAILABILITY.md`.
- Blank match fields mean "no vote row found," never a guess. Numbers were never invented:
  every `ordinance_no` is attested in the SLC minutes.
