# roster/ — Cottonwood Heights rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Cottonwood Heights City Council + Mayor
seat over time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Built 2026-07-12 on the west_jordan DISTRICT template (`update-council-roster` skill).
Answers: *who was on the council on date X?*, *who is serving now?*, *who represents this address on
this date?*

Cottonwood Heights is a **4-DISTRICT city with a VOTING MAYOR**: **4 single-member council districts
(D1–D4) + a separately-elected Mayor who is a FULL voting member** of the council. A complete roll
call tops out at **5** — `non_voting_mayor=False`, so the Mayor is modelled as a real voting seat
(kept in `DB_KEY`, gets clamped vote bounds). This is the *opposite* of Taylorsville/South Jordan
(non-voting mayor).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — **15 tenures (10 high / 5 medium / 0 low) across 5 seats, incl. 1 VACANT**. |
| `district_versions.csv` | Boundary interval table — **4 districts × 2 plans + 1 citywide Mayor row (9 rows)**. |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only**). 44 `plan_2022` `high` rows + 4 `plan_pre2022` gap rows. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows.** |

**Never hand-edit the generated CSVs** — edit `TENURES` or add an override, then
`python3 roster/build_roster.py`.

## Seat model (verified in source)

**4 District seats (D1–D4) + a VOTING Mayor**, non-partisan 4-year staggered terms:
- **Cycle A** — **Mayor + D3 + D4** (2009 / 2013 / 2017 / **2021** / **2025**).
- **Cycle B** — **D1 + D2** (2011 / 2015 / **2019** / **2023**).
`seat_id` is stable across the redistricting. The Mayor VOTES → in `DB_KEY` with clamped vote bounds.

Documented seatings (oath ceremonies are their own minutes docs): **2020-01-06**, **2022-01-03**,
**2024-01-02**, **2026-01-05**; plus the **2023-05-16** D1 appointment.

**Counts: 15 tenures — 10 high / 5 medium / 0 low; 1 VACANT.** 0 overlapping tenures per seat. All
validators pass. Forward election cross-check maps **every** 2017+ general winner to a tenure — **0
drift**.

## The findings a user must know

1. **The 2023 D1 DEATH IN OFFICE → appointment (the one VACANT chain).** **Douglas (Doug) Petersen**
   (D1, elected 2019) **DIED mid-term**: the 2023-05-15 SPECIAL minutes name candidates "to replace
   the **late** Doug Petersen" (Mayor Weichers on "the loss of Council member Petersen … the District
   1 seat was won by Doug Petersen … a four-year term"). His last cities.db D1 vote is **2023-04-04**;
   the roll header reads "**District 1 (Vacant)**" by 2023-05-02. The Council interviewed **19
   applicants** and appointed **Matt Holton**, "sworn in at 7:00 p.m. during the Regular Business
   Meeting" **2023-05-16** (his first vote). Holton then **won the Nov-2023 D1 general** → reseated
   2024-01-02. Chain: Petersen → **VACANT** → Holton (appointed) → Holton (elected, same person).
   The **VACANT D1 [2023-04-05, 2023-05-16) is `medium`** — the exact death date is unrecorded
   (bounded between the 2023-04-04 last vote and the 2023-05-02 "Vacant" designation), so by the
   weakest-link rule Petersen's departing tenure is `medium` too (the 2019 seating itself is high).
2. **Redistricting effect documented, adopting instrument NOT recovered (a flagged gap).** CH redrew
   districts after the 2020 census — `geo/CLAUDE.md` documents the seam (the current official layer +
   2023/2025 elections define the new map; the 2021 SOVC uses the old one) — but **no adopting
   ordinance is in the recovered minutes**. So `plan_switch` (`2022-06-01`) is an **ESTIMATE** (peer
   SLCo cities Herriman/Holladay adopted Mar–May 2022; first used for the 2023 D1/D2 general), flagged
   in the `district_versions` note. The geometry itself is authoritative (`high`); only the switch
   *date* is estimated, and the prior boundaries are an unacquired `low` GAP.

## The VOTING mayor (spot-checked)

Mayor **Michael (Mike) Peterson** presides at the 2020-01-06 oath and is a full voting member; CH
`CLAUDE.md` confirms **533 mayor vote-rows** and **no >5-voter council motion**. Mayors:
**M. Peterson** (2018–2022) → **Mike Weichers** (2022–2026) → **Gay Lynn Bennion** (2026+). Note the
`PETERSON` (Mayor Michael) vs `PETERSEN` (D1 Douglas) surnames are **distinct tokens** — no
name-collision.

## Honest gaps / conventions

- **Pre-floor holdovers (`medium`)** — the Cycle-A 2017 cohort (Tali Bruce D3, Christine Mikell D4,
  Mayor Michael Peterson) were seated **Jan 2018**, before the 2020 floor → `start_date=2018-01-01`
  (cycle-inferred), `medium`, service vote-documented from 2020-01-07.
- **`end_event`** — Bruce/Mikell/Peterson = `did-not-run` (not candidates in 2021); Bracken = `lost`
  (ran and **lost the 2023 D2 primary**, 3rd of 3); Weichers = `lost` (incumbent, lost 2025 to Bennion).
- **Prior-plan (`plan_pre2022`) geometry + precinct composition** — a genuine **GAP** (blank
  `geometry_ref`, `low`; `district_precincts` has 4 blank `plan_pre2022` rows). Recoverable from the
  2021 by-precinct rows if a historical crosswalk is ever built (`geo/CLAUDE.md`), but **not
  reconstructed here**.

## Redistricting: the 2022 realignment (ordinance not in recovered minutes)

`district_versions` versions D1–D4 into `plan_2022` (current, `geo/districts.geojson`, `high`) and
`plan_pre2022` (prior, gap `low`), plus a citywide Mayor row. `plan_switch` is the **estimated**
2022 effective date (see finding 2).

### Precinct cross-check (`--check` / demo (e))

**2023 (D1, D2) and 2025 (D3, D4) all RECONCILE** against the `plan_2022` precinct assignment;
pre-2022 cycles → honest GAPs. (Per-precinct MISMATCH detection is dormant — `source_year=current`
is a token, not an election year — the documented fleet limitation; the aggregate winner check runs.)

## Library-fit note (for `scripts/roster_HARDENING.md`)

`roster_lib.write_precincts()`/`precinct_crosscheck()` require a **`source_year` column** the
canonical `geo/precinct_to_district.csv` lacks (its columns are
`precinct,district,election_district,method,agrees_with_current_election`). Originally worked around with a
roster-layer `_precinct_to_district.csv` sidecar. Same issue as Herriman/Holladay.

**RESOLVED 2026-07-19 (H-A hardening):** `roster_lib.write_precincts` now accepts a precinct map with no `source_year` column via the explicit `Redistrict.precinct_source_default` token (fail-loud when unset). The driver reads `geo/precinct_to_district.csv` DIRECTLY and the `_precinct_to_district.csv` sidecar is **retired** (backed up under `_backups/2026-07-19-lm-wave/shared-libs/`). Per-precinct MISMATCH detection remains dormant (the token is not an election year — the documented limitation); the aggregate winner cross-check runs live.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2023-05-01 (mid D1 vacancy) (c) address→reps (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into the repo-root `cities.db` as `term` / `district_version` / `district_precinct` rows by
`scripts/build_cities_db.py`.
