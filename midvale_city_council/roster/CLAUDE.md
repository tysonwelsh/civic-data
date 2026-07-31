# roster/ — Midvale rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Midvale council + mayor seat over
time** as dated intervals with per-row provenance and confidence. Built 2026-07-12 on the
west_jordan district template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?*

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 19 tenures (16 high / 3 medium / 0 low) across 6 seats, incl. **2 VACANT** (the mayoral vacancy + the D5 vacancy). |
| `district_versions.csv` | 5 districts × 2 plans (the 2022 redistricting) + a Mayor citywide row. |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only**). **38 `plan_2022` `high` rows + 5 `plan_pre2022` gap rows** (enabled 2026-07-19, H-A). |
| `roster_overrides.csv` | Hand-correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` or add an override, then
`python3 roster/build_roster.py`.

## Seat model (verified in source)

**Six-member-council form: 5 DISTRICT seats (D1–D5) + a separately-elected Mayor who presides
and votes ONLY to break a tie** (`non_voting_mayor=True` → MAYOR rows carry EMPTY vote bounds;
a full council roll tops out at 5). Staggered 4-year cycles:

| Cohort | Seats | Elected | Seated |
|---|---|---|---|
| **A** | D1, D2, D3 | 2015 / 2019 / 2023 | Jan 2016 / 2020 / 2024 |
| **B** | D4, D5 | 2017 / 2021 / 2025 | Jan 2018 / 2022 / 2026 |
| **Mayor** | MAYOR | 2017 / 2021 / 2025 | Jan 2018 / 2022 / 2026 |

Seating dates (first documented January council meeting = first cities.db vote): **2020-01-07,
2022-01-04, 2024-01-02, 2026-01-06**. Cohort-B terms whose Jan start predates the 2020 minutes
floor (D4 Brown, D5 Gettel, Mayor Hale — all won 2017) are **pre-floor → medium**.

## Current roster (as of the 2026-01-06 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Bonnie Billings | 2024-01-02 | 2023 | high |
| D2 | Paul Glover | 2024-01-02 | 2023 (uncontested) | high |
| D3 | Heidi Robinson | 2024-01-02 | 2023 (RCV pilot) | high |
| D4 | Bryant Brown | 2026-01-06 | 2025 | high |
| D5 | Denece Mikolash | 2026-01-06 | 2025 (appt 2025, then elected) | high |
| MAYOR | Dustin Gettel (non-voting) | 2026-01-06 | 2025 (appt 2024, then elected) | high |

## The distinctive surface (spot-checked against source minutes)

- **The Gettel council→mayor seam + the paired D5 / mayoral vacancies.** Mayor **Marcus
  Stevenson** (won 2021, RCV pilot) **RESIGNED 2024-11-14** (*"on Thursday, November 14, 2024,
  Mayor Marcus Stevenson resigned"*) → explicit **VACANT** mayoral interval (Council Member
  Glover served as Mayor Pro-Tempore — an acting role, not a Mayor tenure) → **Dustin Gettel**
  (D5 councilmember) was **APPOINTED Mayor 2024-12-10** (Resolution 2024-R-57, *"for the
  Remaining Term"*), vacating **D5** → **VACANT** D5 → **Denece Mikolash** appointed to D5
  2025-01-07 (Res. 2025-R-01, oath administered that night). Gettel then **won the 2025 mayoral
  race** (60.89%) and Mikolash **won the 2025 D5 race** — both seated 2026-01-06 for full terms.
  One `dustin_gettel` key spans D5 (2018–2024, real vote bounds) and MAYOR (2024+, EMPTY bounds
  by `non_voting_mayor`); the seats don't overlap.
- **RCV pilots (2021 Mayor, 2023 D3).** The stored `winner_pct`/`margin` are FIRST-CHOICE
  round-1 values; the `winner` is the canvassed RCV-final (Stevenson 2021, Robinson 2023) —
  cited as such, never read as a final margin.
- **The single mayoral tie-break.** Mayor **Robert Hale**'s only recorded council vote is the
  2020-05-05 m14 tie-break (2–2 → "passed 3-2"). `non_voting_mayor` empties his MAYOR bounds;
  he is not in `DB_KEY`.
- **Pre-floor terms (medium)** — Brown-D4-t1, Gettel-D5-t1, Hale-Mayor-t1 (all won 2017, term
  began Jan 2018 below the 2020 minutes floor).
- **The 2020–2021 OCR seam** — the OCR-garbled Gettel/Glover name variants in the source
  minutes were already resolved to canonical `name_key`s in cities.db, so the vote bounds are
  clean (no garbled person rostered).

## The 2022 redistricting

Midvale redrew its 5 districts after the 2020 Census — *"Council adopted a map defining new
district boundaries on April 19, 2022"* (`plan_switch=2022-04-19`); the district NUMBERS were
unchanged. `district_versions` versions the current plan (`plan_2022`, high, real geometry in
`geo/districts.geojson`) against `plan_pre2022` (pre-2020-census boundaries **not acquired →
honest GAP**, blank geometry, low).

## Precinct layer — ENABLED 2026-07-19 (H-A)

`geo/precinct_to_district.csv` has no `source_year` column (its columns are
`precinct,district,district_area_frac,method,split`). Under the H-A hardening the driver reads
the canonical geo map DIRECTLY and passes the explicit
`Redistrict.precinct_source_default="current"` token (fail-loud if unset), so `write_precincts`
no longer `KeyError`s. `district_precincts.csv` now carries **38 `plan_2022` `high` precinct
rows** (centroid-in-district off Midvale's OFFICIAL 5-district FeatureServer) + **5
`plan_pre2022` gap rows**. Because the token is not an election year, per-precinct MISMATCH
detection stays dormant (the documented "token-not-a-year" limitation); the **aggregate winner
cross-check runs live**. No `geo/` or `roster_lib` edits; no sidecar (the map is clean — no
blank-district rows).

### Precinct cross-check (`--check` / demo (e))

**2023 (D1/D2/D3) and 2025 (D4/D5) RECONCILE** against the `plan_2022` precinct assignment
(district numbers were unchanged at the 2022 redraw). All pre-2022 cycles fall under
`plan_pre2022` (old precinct numbering) → honest GAPs, never graded.

## Honest gaps (recorded, not filled)

- **`end_event=unknown`** — Sperry (D1), Hale (Mayor-t1) each left at a cycle boundary with the
  mechanism unrecorded (the end *date* is the successor's seating).
- **plan_pre2022 geometry / precinct composition** — not acquired (5 blank `plan_pre2022` rows
  in `district_precincts.csv`; the current-plan `plan_2022` precinct map is populated).
- **Mayor never routinely votes** — MAYOR `first_vote`/`last_vote` are empty by design.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2024-11-25 (mayoral vacancy)
python3 roster/build_roster.py --check   # validations
```
Federated into the repo-root `cities.db` as `term` / `district_version` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
