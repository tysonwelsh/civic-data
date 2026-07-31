# roster/ — Kearns rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Kearns council + mayor seat over
time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Built 2026-07-13 on the herriman DISTRICT + VOTING-MAYOR template, plus the
white_city / copperton HB35-seam handling (`update-council-roster` skill). Answers: *who was on
the council on date X?*, *who is serving now?*, *who represents this address on this date?* —
none of which the flat CSVs can answer.

Kearns spans a **metro-township → CITY (HB35) seam with a district-count change**, and the
presiding officer **VOTES in BOTH eras** (`non_voting_mayor=False`, the Millcreek pattern) — but
is a *different kind of officer* on each side of the seam.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — **19 tenures (11 high / 8 medium / 0 low; 0 VACANT) across 6 seats** (D1–D5 township + D1–D4 city + MAYOR). |
| `district_versions.csv` | Boundary interval table — **4 city districts × 2 plans + the abolished township D5's own `plan_township` gap row + 1 citywide Mayor row (10 rows)** (the 5→4 township→city restructure; D5 row added 2026-07-19 via the H-H `districts_old` hardening). |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only**). `plan_city2026`: D2 (4 `high`) + D4 (5 `high`) + D1/3 unsplit residual (11 `medium`); `plan_township`: 5 blank-precinct `low` gap rows (incl. the abolished D5, added 2026-07-19). |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows.** |
| `_precinct_to_district.csv` | A **source_year sidecar** over `geo/precinct_to_district.csv` (the canonical geo file lacks the `source_year` column `roster_lib.write_precincts()` requires — see the library-fit note). Clean 2025-SOVC D2/D4 precincts → `source_year=2025` (high); D1/D3 unsplit residuals → `source_year=residual` (medium). A roster-layer derived file, **not** a `geo/` edit. |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override, then
`python3 roster/build_roster.py`.

## The seam model — max roll = 5 in BOTH eras, but different composition

| | Township era (data floor 2017 → 2026 seating) | City era (Jan 2026 →) |
|---|---|---|
| **Council** | 5 members, **Districts 1–5** | 4 members, **Districts 1–4** |
| **Presiding officer** | a **peer-selected Chair** styled "Mayor" (S.B.175), who is **one of the five district members** and **VOTES** (Kelly Bush, holding D5, throughout the recovered record) | a **directly-elected executive Mayor** who **VOTES** (Jesse Valdez) |
| **Max roll call** | **5** (the five district members) | **5** (Mayor + 4 councilmembers) |
| **`non_voting_mayor`** | `False` | `False` |

Verified in source: township — "Mayor Kelly Bush, Chair, presided" and votes as one of five
(2018-07-09+; `cities.db` `kellybush` = 11 named Council votes). City — 2026-05-11 "Vote was 5-0"
with only 4 councilmembers ⇒ the 5th vote is Mayor Valdez (the **city mayor VOTES**; the
opposite of Taylorsville/South Jordan, matching Millcreek/Herriman).

## Seat model (verified in source)

**Six `seat_id`s.** Township districts **D1–D5** on two staggered cohorts; the seam restructures
them into **D1–D4 + a new citywide MAYOR**:
- **Cohort A** — **D1, D3, D5** (2016 founding 3-yr term → 2019 → 2023 → 2027).
- **Cohort B** — **D2, D4** (2016 founding 1-yr term → 2017 → 2021 → 2025). The short 1-year
  founding term for seats 2 & 4 is the metro-township stagger device (they re-elected in 2017).
- **MAYOR** — city-era only (2025 →).

**Districts D1–D4 carry ACROSS the seam continuously.** Township winners **Patrick Schaeffer (D1,
2023)** and **Chrystal Butterfield (D3, 2023)** simply *continue* as city D1/D3 — present and
**NOT re-sworn** at the 2026-01-12 city oath (only Longtin D2, Colby D4, and Mayor Valdez took the
oath). Their 2023 township tenures run unbroken into the city era (one row each; the seam redraws
boundaries, it does not reseat them).

**Township D5 is ABOLISHED at the seam** (5→4 restructure). D5's holder **Kelly Bush** — the
township chair-"Mayor" — ran for the **new directly-elected city Mayor** office in 2025 and **LOST
to Valdez** (57.64%). Her council service ends at the 2026 seating (`end_event=seat-abolished`).
**The city MAYOR seat (Valdez) is a NEW office, modeled SEPARATELY from D5** — Bush ≠ Valdez, no
false continuity across the seam.

**Current (city era): Mayor Jesse Valdez + D1 Schaeffer, D2 Longtin, D3 Butterfield, D4 Colby.**

## The findings a user must know

1. **The Ruby Brown D3 appointment (the one mid-term vacancy — dated only as far as the record
   allows).** Steve Perry won D3 in 2016; he **VACATED mid-term at an undeterminable date inside
   the 2017-01→2018-06 PMN-purge gap**. **Ruby Brown was APPOINTED** to fill it and is already
   seated by the **earliest recovered minutes (2018-07-09)** ("RUBY BROWN" in every 2018–2019
   roll; 3 named votes 2019-09-09…2019-10-14). She then **LOST the 2019 D3 election to Chrystal
   Butterfield** (68.25%) and left at Butterfield's 2020-01-13 seating. Because the whole
   Perry-vacate → Brown-appoint handoff is **inside the purge gap**, it is **not modeled as an
   explicit VACANT interval** (the window cannot be dated — never fabricated): Brown's `start_date`
   is her first documented presence (2018-07-09, `medium`), and **Perry's `end_date` is the
   chaining artifact of that date, NOT his true last day** (flagged in both notes).
2. **The township chair is a peer-selected HAT, not a seat.** "Council Member Peterson nominated
   Council Member Bush as Kearns Metro Township Mayor" (2024-01-08). Bush held the chair across the
   whole recovered record, so every "Mayor Kelly Bush, Chair" roll is Bush in her **D5** seat —
   modeled on `seat_id=D5` (`body=Council`), never as a separate township executive. (The
   2022-02-14 ordinance extended the mayor/vice-chair term from 1 year to the full elected term.)
3. **The city mayor VOTES** (roll of 5) — `non_voting_mayor=False`; Valdez is `seat_id=MAYOR`,
   `body=Mayor`. No named vote is yet attributable to him in `cities.db` (city-era minutes are
   narrative-tally) → blank vote bounds; a **source limit, not a gap**.

## Honest gaps / conventions

- **Pre-2019 FOUNDING terms (`medium`, 8 rows).** The 2016 and 2017 township elections are in the
  data (the roster is **election-anchored**), but their **Jan-2017 / Jan-2018 seatings fall in the
  2017-01→2018-06 PMN-purge gap** (earliest recovered minutes 2018-07-09): the win is fact, the
  continuous service across the purge is inferred → `medium` (weakest-link). Ruby Brown's
  appointment is likewise `medium` (exact appoint date in the gap).
- **`end_event=did-not-run`** for Peterson (D2) and Snow (D4) — each served the full 2021 term to
  the seam and was not a city-D2/D4 candidate in 2025 (Snow instead ran for city Mayor and lost);
  the end *date* (the 2026-01-12 city seating) is precise, the mechanism is unstated.
- **`end_event=seat-abolished`** for Bush (D5) — the seat ceased to exist at the 5→4 restructure.
- **Township 5-district GEOMETRY is a GAP** (`plan_township`, blank `geometry_ref`, `low`). Since
  2026-07-19 the abolished **D5 carries its own `plan_township` gap row** (H-H `districts_old`
  hardening) instead of being folded into D1–D4's gap prose — the township 5-district map was
  never acquired. In force through the 2023 township elections. **Never reconstructed.**
  Township-era address→rep queries therefore return an honest gap (see demo (c)).
- **D1/D3 are an UNSPLIT RESIDUAL even in the city plan.** The 2025 ballot omitted Districts 1 & 3
  (only D2/D4 were up), so the SLCo SOVC precinct→contest map cannot separate D1 from D3
  (`geo/districts.geojson` carries one "District 1/3" residual feature). `district_precincts`
  marks those 11 precincts `medium` ("District 1/3"); only **D2 and D4 are authoritative** (`high`).
  This is a `geo/` limitation flagged, not a roster defect.

## The 5→4 restructure (`district_versions`)

The HB35 city conversion (legally effective **2024-05-01**) restructured the 5 township districts
into **4 city districts + a directly-elected Mayor**; the 4-district plan took effect for
representation at the **2026-01-12** city seating (`plan_switch`). `district_versions` versions
D1–D4 into `plan_city2026` (current, `geo/districts.geojson`, `high` — with the D1/D3-residual
caveat in the note) and `plan_township` (prior, gap `low`), plus a citywide Mayor row. ⚠ The Mayor
row's `effective_start` is the data floor by library convention, but the **directly-elected
citywide mayor office only began in 2026** (township era had no elected mayor — the presiding
"Mayor" was the peer-selected Chair Bush in D5); the note records this.

### Precinct cross-check (`--check` / demo (e))

Groups the 2025 by-precinct council votes by the `district_precincts` (`plan_city2026`) assignment
and confirms the precinct-sum winner matches the roster: **2025 D2 (Longtin) and D4 (Colby) both
RECONCILE**. All township-era cycles fall under `plan_township` (old precinct numbering not
acquired) → reported as honest GAPs.

## Library-fit note (for `scripts/roster_HARDENING.md`)

Same as herriman / Cottonwood Heights / Holladay: `roster_lib.write_precincts()` /
`precinct_crosscheck()` require a **`source_year` column** in the precinct map, which Kearns's
canonical `geo/precinct_to_district.csv` (columns `precinct,district,method,note`) lacks. Worked
around with a **roster-layer sidecar** `_precinct_to_district.csv` (adds `source_year`);
`roster_lib` and `geo/` were **not** edited. Kearns's second, deeper library-fit limitation —
`roster_lib.Redistrict` assumed the SAME district list across both plans, so the 5→4 seam could
not emit a `plan_old` row for the abolished District 5 — was **RESOLVED 2026-07-19 (H-H
hardening)**: `Redistrict.districts_old` now carries the prior plan's own list and the driver
sets it, giving D5 its honest `plan_township` gap rows in `district_versions` +
`district_precincts`. Likewise the terminal abolished-seat end_date clobber (`chain_end_dates`
blanking Bush's explicit 2026-01-12) was **RESOLVED (H-F)** — terminating end_events
(`seat-abolished`) now keep their explicit end_date, and the `roster_overrides.csv` pin that
worked around it is retired (0 data rows again).

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2019-06-01 (township) (c) address→reps (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into the repo-root `cities.db` as `term` / `district_version` / `district_precinct` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py` (run by the orchestrator,
not from here).
