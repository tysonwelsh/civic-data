# roster/ — Riverton rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Riverton council + mayor seat over
time** as dated intervals with per-row provenance and confidence. Built 2026-07-12 on the
west_jordan district template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?*

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 17 tenures (14 high / 3 medium / 0 low) across 6 seats, incl. **1 VACANT** (the D1 Stewart→Pierucci gap). |
| `district_versions.csv` | 5 districts × 2 plans (the 2022 Ord. 22-07 redistricting) + a Mayor citywide row — **both plans carry REAL geometry** (current `geo/districts.geojson`, prior `geo/districts_pre2022.geojson`). |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only**). **35 `plan_2022` `high` rows + 5 `plan_pre2022` gap rows** (enabled 2026-07-19, H-A). |
| `roster_overrides.csv` | Hand-correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` or add an override, then
`python3 roster/build_roster.py`.

## Seat model (verified in source)

**Six-member-council form: 5 DISTRICT seats (D1–D5) + a separately-elected Mayor who chairs
the council and votes ONLY to break a tie** (`non_voting_mayor=True` → MAYOR rows carry EMPTY
vote bounds; a full council roll tops out at 5). Staggered 4-year cycles:

| Cohort | Seats | Elected | Seated |
|---|---|---|---|
| **B** | D1, D2, D5 | 2019 / 2023 | Jan 2020 / 2024 |
| **A** | D3, D4, Mayor | 2017 / 2021 / 2025 | Jan 2018 / 2022 / 2026 |

The recovered minutes corpus begins **2020-02-17** (no January-2020 minutes on disk), so the
2019-cohort seatings use the **statutory Jan-2020 term-start** (2020-01-06), noted. 2022 / 2024
/ 2026 seatings are the first documented meeting each January (2022-01-04, 2024-01-02,
2026-01-20).

## ⚠ The D3 ↔ D4 renumber (Ordinance No. 22-07, adopted 2022-02-15) — the headline hazard

At the 2022 redraw, **District 3 and District 4 were RENUMBERED (swapped)**. This roster uses
**CURRENT (post-2022) numbering** for `seat_id`, and each pre-2022 row records the *ballot
label* it was elected under:

- **Current `D3` = Tish Buroker's seat** (successor **Alexander Johnson**, 2025). Buroker was
  **elected under the label "District 4"** in 2017 & 2021.
- **Current `D4` = Tawnee McCay's seat** (successor **Shannon Smith**, 2025). McCay was
  **elected under the label "District 3"** in 2017 & 2021.

Corroboration: the retained pre-2022 GIS (`geo/districts_pre2022.geojson`) labels D3=McCay,
D4=Buroker (matching the ballots), while the current GIS (`geo/districts.geojson`) labels
D3=Johnson, D4=Smith. **Join person↔district across 2022 on PERSON identity, not the bare
number** (D1/D2/D5 unaffected). Because `seat_for_contest` keys on the current label, the
`--check` election cross-check prints **4 EXPECTED "winner not in roster" warnings** —
McCay-2017/2021 (ballot "District 3") and Buroker-2017/2021 (ballot "District 4") — the
documented renumber, **not a defect**. The MIRROR of these (the H-C reverse crosscheck, added
2026-07-19) is silenced by 4 cited `reverse_crosscheck_exceptions` in the driver (same renumber
class); the crosscheck ends clean.

## Current roster (as of the 2026-01-20 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Andy Pierucci | 2024-01-02 | 2023 (appt 2023, then elected) | high |
| D2 | Troy McDougal | 2024-01-02 | 2023 | high |
| D3 | Alexander Johnson | 2026-01-20 | 2025 | high |
| D4 | Shannon Smith | 2026-01-20 | 2025 | high |
| D5 | Spencer Haymond | 2024-01-02 | 2023 | high |
| MAYOR | Tish Buroker (non-voting) | 2026-01-20 | 2025 | high |

## The distinctive surface (spot-checked against source minutes)

- **The D1 mid-term vacancy: Stewart → VACANT → Pierucci.** **Sheldon Stewart** (D1, elected
  2019) **resigned** in late 2022 (*"Councilmember Stewart's resignation would be…"*, 2022-12-13;
  last vote 2022-12-13) → explicit **VACANT** interval → **Andy Pierucci** *"appointed to serve
  as the District 1 Councilmember through the end of 2023"* (2023-01-03) → Pierucci then **won
  the 2023 general** for the full term (seated 2024-01-02). Two Pierucci tenures (appointed,
  then elected), both `high`.
- **Two council→mayor / seat continuities across the renumber.** **Tish Buroker** held her seat
  2018–2025 (ballot "District 4", current D3), then won the **2025 mayoralty** (became-mayor at
  the 2026-01-20 seating). One `tish_buroker` key spans both; her MAYOR row carries EMPTY vote
  bounds (`non_voting_mayor`), her council rows keep clamped bounds.
- **The single mayoral tie-break.** Mayor **Trent Staggs** cast exactly one recorded council
  vote — **2025-12-16, Resolution No. 25-62** (a 2–2 split → Staggs Aye). `non_voting_mayor`
  empties his MAYOR vote bounds; he is not in `DB_KEY`, so the tie-break does not smear a span.
- **Pre-floor terms (medium)** — Buroker-t1, McCay-t1, Staggs-t1 (all won 2017, term began Jan
  2018, predating the 2020 minutes floor). Their win is in the recovered election file but the
  term origin is below the floor → medium.

## district_versions — 5 districts + the 2022 renumber (both plans real geometry)

- **`plan_2022`** (current) — `geo/districts.geojson`, `effective_start=2022-02-15`, high.
- **`plan_pre2022`** (prior) — the retained 2019 GIS layer `geo/districts_pre2022.geojson`
  (authoritative, **not** reconstructed) → high, with the D3↔D4 label swap noted on every row.
- **Mayor** citywide row — whole-city extent, unaffected by the redraw.

## Precinct layer — ENABLED 2026-07-19 (H-A)

`geo/precinct_to_district.csv` has no `source_year` column (its columns are
`precinct,district,district_election,method,area_frac,agree_election,split`). Under the H-A
hardening the driver reads the canonical geo map DIRECTLY and passes the explicit
`Redistrict.precinct_source_default="current"` token (fail-loud if unset), so
`write_precincts` no longer `KeyError`s. `district_precincts.csv` now carries **35 `plan_2022`
`high` precinct rows** (centroid-in-district off the OFFICIAL current district layer) + **5
`plan_pre2022` gap rows**. Because the token is not an election year, per-precinct MISMATCH
detection stays dormant (the documented "token-not-a-year" limitation); the **aggregate winner
cross-check runs live**. No `geo/` or `roster_lib` edits; no sidecar (the map is clean — no
blank-district rows).

### Precinct cross-check (`--check` / demo (e))

**2023 (D1/D2/D5) and 2025 (D3/D4) RECONCILE** against the `plan_2022` precinct assignment
(the 2025 results use CURRENT numbering, so the D3↔D4 renumber does NOT corrupt them —
2025 D3 = Johnson, D4 = Smith reconcile cleanly). All pre-2022 cycles fall under `plan_pre2022`
(old precinct numbering + the D3↔D4 ballot swap) → honest GAPs, never graded.

## Honest gaps (recorded, not filled)

- **No January-2020 minutes** — the 2019-cohort seatings use the statutory term-start (noted).
- **`end_event=unknown`** — McCay (D4-t2), Wells (D5), Staggs (Mayor-t2) each served a full
  term and were not candidates in the next cycle; the end *date* is the successor's seating,
  only the retire-vs-decline mechanism is unrecorded.
- **`plan_pre2022` precinct composition** — a genuine GAP (5 blank `plan_pre2022` rows in
  `district_precincts.csv`); the current-plan (`plan_2022`) precinct map is populated.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2022-12-20 (D1 vacant)
python3 roster/build_roster.py --check   # validations (+ the 4 expected renumber warnings)
```
Federated into the repo-root `cities.db` as `term` / `district_version` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
