# roster/ — Millcreek rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Millcreek City Council + Mayor
seat over time** as dated intervals, reconciled from multiple sources with **per-row
provenance and confidence**. Answers: *who was on the council on date X?*, *who is serving
now?*, *who represents this address on this date?* — none of which the flat CSVs can answer.

Millcreek is a **DISTRICT city built on the Provo template** with one structural difference
that drives every config choice: **THE MAYOR VOTES.** It is a five-member council-mayor form
— **4 district members (D1–D4) + a citywide Mayor who is a FULL VOTING council member** — so
`non_voting_mayor=False`, the MAYOR row carries **real cities.db vote bounds**, and the mayor
is in `db_key`. A complete roll call tops out at **5** (verified in the source minutes):

> "Council Member DeSirant voted yes, Council Member Jackson voted yes, Council Member Uipi
> voted yes, **and Mayor Silvestrini voted yes**. The motion passed unanimously." — minutes
> 2023-12-11

Millcreek is also the **first roster in the fleet to exercise BOTH** a real **council→mayor
move** and a genuine **mid-term VACANT interval** (Provo/SLC/Lehi/Orem/Logan/Vineyard/Nephi
had at most one; Provo/Orem had zero). See "The Nov-2025 succession" below.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates all three CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**20 rows** across 5 stable seats, incl. 1 VACANT). |
| `district_versions.csv` | Boundary interval table — **REAL 4 districts, with the 2022 redistricting (Ordinance 22-23) versioned into two plans**, + the Mayor citywide row. |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped; shares `plan_id`/dates with `district_versions`). |
| `precinct_to_district.csv` | **Roster-local INPUT** — derived from `../geo/precinct_to_district.csv` with an added `source_year` column the shared builder needs (Provo's `geo/` file already has one; Millcreek's does not). `election-xcheck` where a post-2022 contested precinct election cross-validates the composition (D2/D3/D4), else `gis-2022map` (D1). geo/ is left untouched. |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit the three generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. (The council also sits as the **CRA** — Utah 17C — but
  that is the same five people wearing a second hat; **no CRA tenures are modeled**, per the task.)
- **`seat_id`** — a **STABLE** id (a redistricting redraws boundaries, it does NOT renumber
  seats): `D1..D4` (geographic) and `MAYOR`. **There are NO at-large COUNCIL seats** — the
  Mayor is the only citywide seat, and (unlike South Jordan / most cities) is a voting member.
- **`district`** — FK into `district_versions`: `District 1`..`District 4` for D-seats,
  `Citywide` for `MAYOR`.
- **`person_key`** = `first_last`. No shared surnames among winners.
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained per `seat_id`.
- **`start_event`** ∈ {elected, reelected, appointed, became-mayor}. **`end_event`** ∈
  {reelected, did-not-run, became-mayor, resigned, serving, vacated/filled (VACANT rows)}.
- **`election_year`** — the cycle that seated the tenure (blank for the two council **appointments**).
- **`first_vote` / `last_vote`** — each row's first/last observed council member-vote in
  `cities.db` (`role`, `city='millcreek'`, `body='Council'`), **clamped to that tenure's own
  `[start_date, end_date)` window**. **The Mayor rows DO carry bounds** (the mayor votes). ⚠
  `first_vote` for the founders reads
  `2019-05-13` (Uipi 2020-02-24) and DeSirant `2022-07-26` — these are the **named-roll-call
  seam**, not term starts: 2017–2021 Millcreek minutes are **tally-only by source** (named
  rolls begin ~2022), so a late first-named-vote is a recording limit (cf. Logan's López).
- **`confidence`** — `high` for **every** `council_terms` row. **Millcreek's ENTIRE history is
  in-window** (incorporated Dec 28 2016; data floor 2016), so there is **NO pre-floor
  inference** — unlike the older cities' 2017-cycle `medium` terms. **20 high / 0 medium /
  0 low.** The only `low` rows live in the district/precinct GAP records (prior 2016 geometry).

### The 5 seats and their stagger

Every seat was on the founding **Nov 8, 2016** ballot; **D2/D4 drew SHORT initial terms** and
were re-filled in 2017, landing them on the B cycle.

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `MAYOR`, `D1`, `D3` | 2016 / 2019 / 2023 / (2027) | Founding 2016-12-28 · Jan-2020 · Jan-2024 |
| **B** | `D2`, `D4` | 2016(short) / 2017 / 2021 / 2025 | Founding 2016-12-28 · Jan-2018 · Jan-2022 · Jan-2026 |

Term-start = the first **regular** council meeting of January (oath administered there; verified
`2018-01-08 · 2020-01-13 · 2022-01-10 · 2024-01-09 · 2026-01-12`). The **founding** council took
office at **INCORPORATION — legally recorded 2016-12-28** (council-elect met 2016-12-05..27;
first regular meeting 2017-01-09). Founding council + mayor documented from the source:

> "Jeff Silvestrini – Mayor / Silvia Catten – Council District 1 / Dwight Marchant – Council
> District 2 / Cheri Jackson – Council District 3 / Bev Uipi – Council District 4" — minutes
> 2017-01-09 (and, as "Council-Elect", 2016-12-05 & 2016-12-27)

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/millcreek_results_by_candidate.csv`, municipal **general**
   winners only. `seat_for_contest` maps District N → `D-N`; Mayor → `MAYOR`. `is_winner`
   is `True`/`False`. The builder cross-checks that **every** general winner maps to a tenure
   (prints to stderr on drift — currently **clean, 0 drift**; all 17 general winners map).
2. **Vote / attendance bounds** — `cities.db` `role` (`city='millcreek'`, `body='Council'`):
   sets `first_vote`/`last_vote`. **Silvestrini AND Jackson are present** in this table (the
   mayor votes) — confirming `non_voting_mayor=False`.
3. **Minutes events** — incorporation/oath dates, the 2025 succession, and the redistricting
   ordinance, read from `meeting_minutes/minutes/**` and encoded in `TENURES`.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (0 rows).

## The Nov-2025 succession — a council→mayor move + a real VACANT interval (spot-checked)

Founding Mayor **Jeff Silvestrini resigned mid-term** in autumn 2025 (health). The council
appointed sitting **D3 member Cheri Jackson** to finish his term (Resolution **25-38**,
special meeting 2025-11-03), and she was **sworn in as Mayor 2025-11-10**:

> "Alex Wendt, the Deputy Recorder administered the Oath of Office to Mayor-Elect Cheri
> Jackson." — minutes 2025-11-10

That handoff is modeled cleanly:
- **MAYOR**: Silvestrini (2023 term) ends `2025-11-10` (`end_event=resigned`) → Jackson begins
  the **same day** (`start_event=appointed`, `election_year=''`) — **no VACANT** (filled same meeting).
- **D3**: Jackson's 2023 term ends `2025-11-10` (`end_event=became-mayor`, `vacate_date=2025-11-10`),
  so an explicit **`VACANT` interval [2025-11-10, 2025-11-24)** is inserted until **Nicole Handy**
  was **appointed** to D3 (Resolution **25-42**, oath administered) on **2025-11-24**:

> "Resolution 25-42 … Filling the Mid-Term Vacancy of Council District 3 with Nicole Handy … The
> City Recorder administered the oath of office to Nicole Handy." — minutes 2025-11-24

`roster_as_of('2025-11-17')` therefore correctly returns **Jackson as MAYOR and D3 = VACANT**.
The VACANT row is `high`: both endpoints are documented on-disk minutes and the window contains
**no** un-recovered minutes date (`minutes_unrecovered.csv` has only 2018-03-20).

Neither appointment is an election → **no 2025 mayoral race** and **no 2025 D3 race** exist in
`election_results` (consistent with the SOVC — the mayor is a 2027-cycle seat). Both appointees'
rows carry blank `election_year` and are excluded from the election cross-check by design.

⚠ **Multi-tenure bounds — now clamped (LANDED 2026-07-11):** `first_vote`/`last_vote` are
clamped to each tenure's own `[start_date, end_date)` window. Jackson served D3 (2016–2025)
**and** Mayor (2025+); her MAYOR row now reads `2025-11-10..2026-05-26` (her mayoral service
only) and her three D3 rows carry their own per-term bounds — no longer one `2019-05-13..
2026-05-26` span across both roles. The former person-level smear (cf. the SLC-audit /
Vineyard-Fullmer backlog item) is resolved structurally by the `roster_lib` vote-bound clamp.

## `district_versions.csv` — REAL districts + the 2022 redistricting

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Geometry is **not** inline — `geometry_ref` points at
`geo/council_districts.geojson` (the 4 district polygons, 2022-2032 vintage).

**Millcreek DID redistrict** after the 2020 census: **Ordinance 22-23**, *"AN ORDINANCE
ADJUSTING CITY COUNCIL DISTRICT BOUNDARIES TO MAINTAIN DISTRICTS OF SUBSTANTIALLY EQUAL
POPULATION"* (map 5 as Exhibit A), **adopted 2022-05-09** (Pass, unanimous; mover Jackson /
second Uipi). Public hearing 2022-04-11; the council "needed to adopt a redistricting map by
May 16, 2022" (2022-02-14).

Versioning (9 rows):
- **`plan_2022`** (current) for D1–D4 — real geometry, `effective_start=2022-05-09`, open-ended,
  **high**.
- **`plan_2016`** (prior) for D1–D4 — the **ORIGINAL 2016 incorporation district map**,
  **AUTHORITATIVE, SOURCED 2026-07-19**, `confidence=high`: `geometry_ref=geo/council_districts_pre2022.geojson`,
  `source_url` = Millcreek's own city GIS (`services9.arcgis.com/XRrSFvEwSsReIxuA`, the SAME org as the
  current 2022-2032 layer), **`CityCouncilDistricts` FeatureServer layer 0 = "City Council District
  Boundaries 2017-2022"** (4 polygons; `DistrictRep` carries the pre-2022 members incl. Dwight Marchant
  D2, who left office Jan 2022 → vintage confirmed). Genuinely distinct from `plan_2022` (per-district
  IoU 0.58–0.92). In force for the 2016/2017/2019/2021 elections. `effective_start` = data floor
  (incorporation). See `scripts/roster_boundary_recon.md`. **This REPLACED the 2026-07-11 precinct-
  dissolve reconstruction**, which was materially wrong (IoU ≈ 0 vs this authoritative layer) because the
  MIL### precinct CODES were renumbered/reshaped between 2019 and the current 2025 UGRC vintage. ⚠ Do NOT
  regenerate `council_districts_pre2022.geojson` with `scripts/build_prior_district_map.py` — it would
  overwrite the authoritative fetch.
- **`MAYOR`** citywide row — whole-city extent, unaffected by redistricting, open-ended, high.

`plan_switch = 2022-05-09` (the ordinance's adoption/effective date). Sitting members continued
representing their pre-redraw constituents until the next election; the switch date controls
which plan an **address→district** query resolves against (below).

## `district_precincts.csv` — versioned precinct → district composition

`city, plan_id, district_id, precinct_id, effective_start, effective_end, source, confidence,
note`. Sourced from `roster/precinct_to_district.csv` (51 precincts).
- **`plan_2022`**: 51 precinct rows. `confidence=high` for **D2 (14) / D3 (13) / D4 (13)** —
  their compositions are cross-validated against a post-2022 contested municipal general
  (2025 D2, 2023 D3, 2025 D4). `medium` for **D1 (11)** — the city GIS layer only, because D1's
  sole post-2022 race (2023) was **cancelled-uncontested** so has no precinct-level election data.
- **`plan_2016`**: **46 rows POPULATED** from `geo/precinct_to_district_pre2022.csv`
  (`precinct_id` filled, `confidence=medium`) — the incorporation-era composition (46 MIL precinct
  CODES, from the 2017+2019 SOVC district contests). This is the record of which OLD precinct code
  voted in which district contest; it is **NOT geographically joinable to the current UGRC precinct
  shapes** (the codes were renumbered/reshaped by 2025 — centroid-in-polygon against the authoritative
  2017-2022 district layer disagrees on 36/44 codes), hence still `medium`. NOTE the **boundary GEOMETRY**
  (`district_versions.plan_2016`) is now the AUTHORITATIVE fetched layer (`high`); this precinct-CODE
  composition is a separate SOVC-derived `medium` artifact.

### Precinct-map cross-check (in `--check` / demo (e))

Groups precinct votes by the `district_precincts` (plan_2022) assignment and confirms the winner
matches the roster:

| Cycle | District | Plan | Result |
|---|---|---|---|
| 2023 | D3 | plan_2022 | **RECONCILES** — Jackson 76.2% |
| 2025 | D2 | plan_2022 | **RECONCILES** — DeSirant 59.3% |
| 2025 | D4 | plan_2022 | **RECONCILES** — Uipi 82.0% |
| 2016/2017/2019/2021 | D2/D3/D4 | plan_2016 | **GAP at the runtime election-crosscheck** — old cycles can't be graded against the *current* map (the plan_2016 *composition* is now reconstructed, `medium`) |

The pre-2022 cycles are honestly ungradeable through the current map. Note **2021 D2 was RCV**
(first-choice leader **Clark** ≠ final-round winner **DeSirant**); it falls under the plan_2016
GAP, so the RCV divergence never surfaces as a false discrepancy.

## How to query

```bash
python3 roster/build_roster.py --demo    # (a) current  (b) as-of mid-vacancy  (c) address→rep  (d) redistricting  (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Catten D1,
  DeSirant D2, Handy D3, Uipi D4, Mayor Jackson).
- **As of a date** — `roster_as_of(date, body)`.
- **Address + date → representative** — `representatives_for_address(address, date)`: resolves
  the address via `geo/address_to_district.py` to **District N**, returns that district's rep on
  `date` **plus the citywide voting Mayor**. It honors `district_versions`, and since **2026-07-19**
  the shared lib is **confidence-gated plan-aware**: a **pre-2022-05-09** date **RESOLVES by
  point-in-polygon against the AUTHORITATIVE `plan_2016` layer**
  (`geo/council_districts_pre2022.geojson`, `confidence=high` — millcreek is currently the ONLY
  city whose prior plan qualifies; low/blank-geometry prior plans elsewhere still return the honest
  gap). A prior-plan hit carries `plan_provenance` (plan id, geometry confidence, geometry_ref, the
  city-GIS `source_url`) for honest citation. Demo: `3330 S 1300 E` → **District 2 → Thom DeSirant
  + Mayor Cheri Jackson** (2026); the same address on **2021-06-01 → plan_2016 District 2 → Dwight
  Marchant + Mayor Silvestrini** (cross-checked against the layer's own `Representative` field and
  `council_terms`). The plan_2016 `district_precincts` precinct-CODE composition plays no part in
  this (not geographically joinable); resolution is pure PiP on the authoritative polygons.

## Honest gaps (recorded, not filled)

- **Prior (`plan_2016`) district geometry** — **NO LONGER A GAP: AUTHORITATIVE, SOURCED 2026-07-19**
  (`high`). `district_versions.plan_2016` now carries `geometry_ref=geo/council_districts_pre2022.geojson`
  (the exact "City Council District Boundaries 2017-2022" polygons from Millcreek's own GIS) + a cited
  `source_url`. This superseded the 2026-07-11 precinct-dissolve reconstruction (which was `medium` and,
  on comparison to the authoritative layer, materially wrong — IoU ≈ 0, because the MIL### precinct codes
  were renumbered/reshaped between 2019 and 2025). See `scripts/roster_boundary_recon.md`.
- **Prior (`plan_2016`) precinct-CODE composition** — still `medium` (`district_precincts`, 46 rows):
  the 2017+2019 SOVC record of which old code voted in which district contest, NOT geographically
  joinable to current precinct shapes. Separate from the now-authoritative boundary geometry above.
- **D1 plan_2022 precinct composition** — `medium` (GIS layer only; D1's 2023 race was
  cancelled-uncontested, so no precinct-election corroboration).
- **Named-roll-call seam (2017–2021)** — the founders' `first_vote` (2019-05-13; Uipi 2020-02-24)
  and DeSirant's (2022-07-26) reflect when named rolls begin, NOT their term starts (which are
  anchored to elections/incorporation). A recording limit, not a gap.
- **No unidentified holder** — every seat-date maps to a named election winner or a
  minutes-documented appointee; the only `VACANT` interval (D3, Nov 2025) is fully documented.

## `roster_lib` fit notes (Millcreek)

The shared library fit cleanly with **two** driver-level accommodations, no `roster_lib` edits:
1. **`non_voting_mayor=False` + mayor in `db_key`** — exercises the voting-mayor path (mayor rows
   carry real bounds; the `non_voting_mayor` validator is correctly inert). Well-supported.
2. **Roster-local `precinct_to_district.csv`** — the builder's precinct writer needs a
   `source_year` column that Provo's `geo/` file has but Millcreek's does not, so the driver reads
   a roster-scoped adapter copy (documented above) rather than modifying `geo/`.

Everything else — the `Redistrict` block, the VACANT-interval insertion, the election
cross-check, `citywide_seats=()` (no at-large council seats), and the address/precinct query
helpers — worked as-is.
