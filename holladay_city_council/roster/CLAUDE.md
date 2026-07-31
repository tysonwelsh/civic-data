# roster/ — Holladay rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Holladay City Council + Mayor seat over
time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Built 2026-07-12 on the west_jordan DISTRICT template (`update-council-roster` skill).
Answers: *who was on the council on date X?*, *who is serving now?*, *who represents this address on
this date?*

Holladay is a **5-DISTRICT city with a VOTING MAYOR** (Council-Manager form): **5 single-member
council districts (D1–D5) + a separately-elected Mayor who is a FULL voting member** of the council
(the executive is an appointed City Manager). A complete named roll tops out at **6** ("… Mayor
Dahle-Aye"), never 5 — `non_voting_mayor=False`, so the Mayor is modelled as a real voting seat
(kept in `DB_KEY`, gets clamped vote bounds). 365 mayor vote-rows in the record.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — **15 tenures (12 high / 3 medium / 0 low) across 6 seats; 0 VACANT**. |
| `district_versions.csv` | Boundary interval table — **5 districts × 2 plans + 1 citywide Mayor row (11 rows)** (the 2022 redistricting). |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only**). 30 `plan_2022` `high` rows + 5 `plan_pre2022` gap rows. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows.** |

**Never hand-edit the generated CSVs** — edit `TENURES` or add an override, then
`python3 roster/build_roster.py`.

## Seat model (verified in source)

**5 District seats (D1–D5) + a VOTING Mayor**, non-partisan 4-year staggered terms:
- **Cycle A** — **Mayor + D1 + D3** (2009 / 2013 / 2017 / **2021** / **2025**).
- **Cycle B** — **D2 + D4 + D5** (2007 / 2011 / 2015 / **2019** / **2023**).
`seat_id` is stable across the redistricting. The Mayor VOTES → in `DB_KEY` with clamped vote bounds
(the max roll is 6). Holladay's db uses **surname-only `name_key`s** (the minutes print surname-only
rolls) — `DB_KEY` maps each surname to a `person_key`.

Documented seatings: **2020-01-09**, **2022-01-20**, **2024-01-04**, **2026-01-08**.

**Counts: 15 tenures — 12 high / 3 medium / 0 low; 0 VACANT.** 0 overlapping tenures per seat. All
validators pass. Forward election cross-check maps **every** 2017+ general winner to a tenure — **0
drift** (the two uncontested 2023 seats carry no winner row by design — see below).

## The findings a user must know

1. **D3 COUNCILMEMBER → MAYOR (the headline transition).** **Paul Fotheringham** held **D3** (elected
   2017 & 2021) and was **elected MAYOR in 2025** (def. Daren Watts 57.04%) → his D3 tenure ends
   `became-mayor` at the 2026-01-08 seating and a **MAYOR** tenure begins; **Natalie Bradley** won the
   open D3. One `paul_fotheringham` key spans **D3 (`body=Council`)** and **MAYOR (`body=Mayor`)** —
   the vote-bound clamp confines each tenure's `first_vote`/`last_vote` to its own window (D3 row:
   …→2025-12-18; MAYOR row: 2026-01-08→…). This is the Nephi-Seely pattern on a voting-mayor city.
2. **D5 Gibbons → Gray, with four post-departure `gibbons` rows that are a SOURCE (clerk) error —
   NOT an extraction artifact.** *(Re-diagnosed 2026-07-29 against the primary minutes. The previous
   wording here — "EXTRACTION ARTIFACTS … a mis-parsed roll / OCR of the outgoing member" — was
   **wrong**, and the "7th name over a roll of 6" framing was a per-MEETING distinct-name count, not
   a roll call.)* Daniel Gibbons (D5, elected 2019) was succeeded by **Emily Gray** (elected 2023
   UNCONTESTED — declared elected, seated **2024-01-04**, her first continuous vote). `gov.db` carries
   **four** `gibbons` Council votes AFTER Gray's seating (2024-02-15, -03-21, -04-25, -12-12). All four
   sit on the same boilerplate motion — *"moved to adjourn the Closed Session"* — and the minutes
   **verbatim print Gibbons in that roll**, e.g. 2024-12-12: *"The Council roll call vote was as
   follows: Council Members Durham, Fotheringham, Quinn, Gibbons, Brewer and Mayor Dahle in favor."*
   That is the **2023 slate pasted forward** in the clerk's closed-session template; the clerk *did*
   update Gibbons→Gray on other 2024 dates (2024-09-19, -10-03, -10-24) and throughout 2025. The same
   stale name also appears as a **seconder** on 2024-06-13. **No Holladay motion exceeds a named roll
   of 6** (verified across `all_votes.csv`), so there is nothing mis-parsed. The rows are **RETAINED
   verbatim** (cardinal rule 2 — city-faithful values are never overwritten) and the tenure is **NOT
   extended**: the clamp confines Gibbons' `last_vote` to **2023-11-16**. **Treat these four rows as
   non-service** when analyzing who held D5.
3. **Two UNCONTESTED 2023 seats carry no SOVC row (honest, not a gap).** D2 **Matt Durham** and D5
   **Emily Gray** drew a single candidate each in 2023; **SLCo omits uncontested municipal seats from
   the SOVC** (`election_results/CLAUDE.md`), so there is **no `is_winner` row** for them. Both are
   rostered `high` on the documented **seating + continuous vote record + the 2026 roster** — the
   forward election cross-check simply has no winner row to check for them (correct, 0 drift). The
   REVERSE crosscheck (H-C, 2026-07-19) flags these two elected/reelected tenures for the same
   reason; they are silenced by 2 cited `reverse_crosscheck_exceptions` in the driver (uncontested →
   no SOVC row), so the crosscheck ends clean.

## The VOTING mayor (spot-checked)

2026-01-08 roll: "Council Member Bradley-Yes; … **Mayor** …" — the Mayor is a full voting member;
Holladay `CLAUDE.md` confirms **365 mayor vote-rows** and a max roll of 6. Mayors: **Rob Dahle**
(2018–2026; first won 2013 by +88) → **Paul Fotheringham** (2026+, from D3). Both are in `DB_KEY`.

## Honest gaps / conventions

- **Pre-floor holdovers (`medium`)** — the Cycle-A 2017 cohort (Sabrina Petersen D1, Paul
  Fotheringham D3, Mayor Rob Dahle) were seated **Jan 2018**, before the 2020 floor →
  `start_date=2018-01-01` (cycle-inferred), `medium`, service vote-documented from 2020-01-09.
- **`end_event=did-not-run`** — Petersen (2021), Brewer (2025), Dahle (2025) each served a full term
  and were not candidates in the next cycle; the end *date* is the successor's seating (precise), only
  the mechanism is unstated. Fotheringham's D3 row ends `became-mayor`.
- **Prior-plan (`plan_pre2022`) geometry + precinct composition** — a genuine **GAP** (blank
  `geometry_ref`, `low`; `district_precincts` has 5 blank `plan_pre2022` rows). **Never reconstructed.**

## Redistricting: Ordinance 2022-09 (2022-05-05)

**Ordinance 2022-09** "Amending the Holladay City Municipal Council District Boundaries," adopted
**2022-05-05** on a unanimous roll incl. **Mayor Rob Dahle** (a voting-mayor roll of 6). Driven by
the 2020 Census (discussed 2022-04-21). `district_versions` versions D1–D5 into `plan_2022` (current,
`geo/council_districts.geojson`, `high`) and `plan_pre2022` (prior, gap `low`), plus a citywide Mayor
row. First used for the 2023 district elections.

### Precinct cross-check (`--check` / demo (e))

**2023 (D4) and 2025 (D1, D3) RECONCILE** against the `plan_2022` precinct assignment; pre-2022
cycles → honest GAPs. (The 2023 D2/D5 seats were uncontested → no by-precinct rows to grade.
Per-precinct MISMATCH detection is dormant — the configured `precinct_source_default` token
`current` is not an election year — the documented fleet limitation; the aggregate winner check runs.)

## Library-fit note (for `scripts/roster_HARDENING.md`)

`roster_lib.write_precincts()`/`precinct_crosscheck()` require a **`source_year` column** the
canonical `geo/precinct_to_district.csv` lacks (columns: `precinct,district,district_area_frac,method,
split`). Originally worked around with a roster-layer `_precinct_to_district.csv` sidecar; same issue as
Herriman/Cottonwood Heights.

**RESOLVED 2026-07-19 (H-A hardening):** `roster_lib.write_precincts` now accepts a precinct map with no `source_year` column via the explicit `Redistrict.precinct_source_default` token (fail-loud when unset). The driver reads `geo/precinct_to_district.csv` DIRECTLY and the `_precinct_to_district.csv` sidecar is **retired** (backed up under `_backups/2026-07-19-lm-wave/shared-libs/`). Per-precinct MISMATCH detection remains dormant (the token is not an election year — the documented limitation); the aggregate winner cross-check runs live. Additionally, the **D5
Gibbons post-departure rows** (finding 2) are exactly what the "roll-size sentinel" the skill
describes would surface — promoting that sentinel into `roster_lib.validate()` as a build-time guard
(flag any council-vote DATE whose distinct-voter count exceeds the seat count) would fail-loud on it
for every city. Note the 2026-07-29 lesson, though: the sentinel fires on the **meeting** grain, and
a hit means "investigate the primary document", **not** "the extractor is broken" — here the primary
document itself carried the stale name, so the correct disposition was to retain the rows and
document the source error, not to delete them.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2025-06-01 (c) address→reps (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into the repo-root `cities.db` as `term` / `district_version` / `district_precinct` rows by
`scripts/build_cities_db.py`.
