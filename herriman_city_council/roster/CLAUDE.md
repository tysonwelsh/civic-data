# roster/ — Herriman rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Herriman City Council + Mayor seat over
time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Built 2026-07-12 on the west_jordan DISTRICT template (`update-council-roster` skill).
Answers: *who was on the council on date X?*, *who is serving now?*, *who represents this address on
this date?* — none of which the flat CSVs can answer.

Herriman is a **4-DISTRICT city with a VOTING MAYOR** (the Millcreek model): **4 single-member
council districts (D1–D4) + a separately-elected Mayor who is a FULL voting member** of the council.
A complete roll call tops out at **5** — `non_voting_mayor=False`, so the Mayor is modelled as a
real voting seat (kept in `DB_KEY`, gets clamped vote bounds like any councilmember). This is the
*opposite* of Taylorsville/South Jordan (non-voting mayor); it matches Bluffdale only in the
"voting"-ness, not the structure (Bluffdale is at-large).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — **16 tenures (13 high / 3 medium / 0 low) across 5 seats, incl. 1 VACANT**. |
| `district_versions.csv` | Boundary interval table — **4 districts × 2 plans + 1 citywide Mayor row (9 rows)** (the 2022 redistricting). |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only** — the Mayor is city-wide). 44 `plan_2022` `high` rows + 4 `plan_pre2022` gap rows. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows.** |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override, then
`python3 roster/build_roster.py`.

## Seat model (verified in source)

**4 District seats (D1–D4) + a VOTING Mayor**, non-partisan 4-year staggered terms:
- **Cycle A** — **Mayor + D2 + D3** (2013 / 2017 / **2021** / **2025**).
- **Cycle B** — **D1 + D4** (2011 / 2015 / **2019** / **2023**).
`seat_id` is stable (a redistricting redraws boundaries, it does NOT renumber seats). The Mayor is
`body=Mayor`, `seat_id=MAYOR`, and — because Herriman's Mayor VOTES — is in `DB_KEY` and carries
clamped vote bounds (unlike the fleet's non-voting-mayor cities).

Documented seatings in the loaded window: **2020-01-08** (2019-cycle + the pre-floor holdovers),
**2022-01-12** (2021-cycle), **2024-01-10** (2023-cycle), **2026-01-14** (2025-cycle), plus the
**2025-05-15** D4 appointment.

**Counts: 16 tenures — 13 high / 3 medium / 0 low; 1 VACANT.** 0 overlapping tenures per seat. All
shared-library validators pass (overlap, sources/confidence, seat_id, the voting-mayor path, the
vacate-confidence invariant, the gap detector). The forward election cross-check maps **every**
2017+ general winner to a tenure — **0 drift**.

## The findings a user must know

1. **The AT-LARGE → DISTRICT transition is WHOLLY PRE-FLOOR (a flagged finding).** The build task
   hypothesized a 2017/2019 at-large→district switch to model as separate seat chains. The **election
   record shows the switch actually happened 2009→2011**: Herriman elected **2 AT-LARGE** council
   seats in 2007 & 2009, then numbered "Council 1/2/4" DISTRICT contests from **2011** onward
   (`election_results/CLAUDE.md`). That is **~9 years below the 2020 data floor**, so there are **no
   at-large-era tenures in the roster window** and **no at-large seats are modelled** — the entire
   rostered record is stable 4-district + Mayor.
2. **The 2025 D4 mid-term vacancy → special (the one VACANT chain).** Steven Shields (D4, elected
   2019 & 2023) served his **documented last meeting 2025-04-23** (Mayor Palmer "noted it would be
   Councilmember Shields' last meeting"; Shields gave farewell remarks). At a **2025-05-15 SPECIAL**
   meeting the Council interviewed 4 applicants and adopted a resolution "to fill the vacant Herriman
   City Council District 4 seat, with the term beginning **May 15, 2025**, and ending January 5,
   2026," appointing **Terrah Anderson** (congratulated on her appointment 2025-05-28, her first
   vote). Anderson then **won the Nov-2025 D4 2-year SHORT-TERM special** (uncontested) → reseated
   2026-01-14. This yields an explicit **VACANT D4 [2025-04-24, 2025-05-15)** (`high` — both
   endpoints documented; Herriman has no `minutes_unrecovered.csv`). Chain: Shields → **VACANT** →
   Anderson (appointed) → Anderson (elected, same person).

## The VOTING mayor (spot-checked)

2020-01-08 minutes: **"Presiding: Mayor David Watts,"** who casts an **Aye** on one motion and a
**decisive Nay** on another (a roll of 5), and "welcomed Steven Shields as a new City Councilmember,
representing District 4." Mayor **Lorin Palmer** (2022+) votes in every roll. Both are in `DB_KEY`
and carry clamped mayoral vote bounds. **Lorin Palmer sat on the Planning Commission (2020–2021)
before becoming Mayor** — one person, two bodies; his PC votes are `body='PlanningCommission'` and
do **not** leak into his mayoral Council bounds (`load_vote_dates` filters `body='Council'`).
Likewise **Terrah Anderson** was a Planning Commissioner (2023–2025) before her D4 appointment.

## Honest gaps / conventions

- **Pre-floor holdovers (`medium`)** — the Cycle-A 2017 cohort (Clint Smith D2, Sherrie Ohrn D3,
  Mayor David Watts) were seated **Jan 2018**, before the 2020 minutes floor → `start_date=2018-01-01`
  (cycle-inferred), `confidence=medium`, service vote-documented from 2020-01-08. Their exact Jan-2018
  oaths are not in the loaded minutes.
- **`end_event=did-not-run`** for Smith (ran for Mayor 2021 instead), Ohrn (2025), Watts (2021) — each
  served a full term and simply was not a candidate in the next cycle; the end *date* is the successor's
  seating (precise), only the mechanism (retire vs decline) is unstated.
- **Prior-plan (`plan_pre2022`) geometry + precinct composition** — a genuine **GAP**, not on disk
  (blank `geometry_ref`, `confidence=low`; `district_precincts` has 4 blank `plan_pre2022` rows). In
  force through the 2019 elections. **Never reconstructed.**

## Redistricting: Ordinance 2022-08 (2022-03-09)

**Ordinance No 2022-08** "realigning the Council District boundaries," adopted **2022-03-09** on a
**5-0** roll (Henderson mover / Hodges second; Ohrn, Shields, **and Mayor Palmer** all Aye — a
voting-mayor roll of 5). Driven by the 2020 Census (pop. 55,144; ideal district ~13,786; discussed
2022-01-12). `district_versions` versions D1–D4 into `plan_2022` (current, `geo/districts.geojson`,
`high`) and `plan_pre2022` (prior, gap `low`), plus a citywide Mayor row. First used for the 2023
district elections.

### Precinct cross-check (`--check` / demo (e))

Groups the by-precinct council votes by the `district_precincts` (`plan_2022`) assignment and
confirms the precinct-sum winner matches the roster. **2023 (D1, D4) and 2025 (D2, D3, D4-special)
all RECONCILE**; pre-2022 cycles fall under `plan_pre2022` (old numbering) → reported as honest
GAPs. (Per-precinct MISMATCH detection is dormant because the configured `precinct_source_default`
token `current` is not an election year — the documented fleet limitation; the aggregate winner check
runs live.)

## Library-fit note (for `scripts/roster_HARDENING.md`)

`roster_lib.write_precincts()`/`precinct_crosscheck()` require a **`source_year` column** in the
precinct map. Herriman's canonical `geo/precinct_to_district.csv` (like Cottonwood Heights' and
Holladay's) has **no** such column — its columns are `precinct,district,district_area_frac,method,split`.
Originally worked around with a roster-layer `_precinct_to_district.csv` sidecar (added `source_year=current`).

**RESOLVED 2026-07-19 (H-A hardening):** `roster_lib.write_precincts` now accepts a precinct map with no `source_year` column via the explicit `Redistrict.precinct_source_default` token (fail-loud when unset). The driver reads `geo/precinct_to_district.csv` DIRECTLY and the `_precinct_to_district.csv` sidecar is **retired** (backed up under `_backups/2026-07-19-lm-wave/shared-libs/`). Per-precinct MISMATCH detection remains dormant (the token is not an election year — the documented limitation); the aggregate winner cross-check runs live.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2025-05-01 (mid D4 vacancy) (c) address→reps (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into the repo-root `cities.db` as `term` / `district_version` / `district_precinct` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
