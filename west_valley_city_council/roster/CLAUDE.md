# roster/ — West Valley City rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each West Valley City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who represents
this address on this date?* — none of which the flat CSVs can answer.

West Valley City is a **MIXED Council–Mayor city**: **4 geographic council districts** (D1..D4) + **2
city-wide AT-LARGE seats** (AL1, AL2) + a **separately-elected Mayor who DOES vote** on council
motions. A full council roll call names **7** voters, the Mayor included. It is the fleet's SECOND
MIXED (districts + at-large) roster after **West Jordan** — but WVC differs on the headline
structural fact (**its Mayor votes**, `non_voting_mayor=False`) and on its at-large shape: WVC's two
at-large seats are **two separate single-winner "Vote-for-1" contests on staggered cycles** (not one
grouped Vote-for-N field), so each at-large seat maps cleanly onto its own cycle. Built on the shared
`../../scripts/roster_lib.py`; the driver `build_roster.py` carries only West Valley's data.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation driver (WVC data + config). Regenerates the CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — **22 tenures across 7 stable seats** (incl. **2 VACANT**). |
| `district_versions.csv` | Boundary interval table — **REAL 4 districts × 2 plans** (the 2022 redistricting) + an At-Large citywide row + a Mayor citywide row (10 rows). |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped, **districts only** — at-large is city-wide). 70 `plan_2022` rows + **64 `plan_pre2022` RECONSTRUCTED rows** (`medium`, 2026-07-19). |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows** (both appointments + both VACANTs are fully documented — no override needed). |
| ~~`_precinct_to_district.csv`~~ | **RETIRED 2026-07-11** — roster_lib now reads the canonical `geo/precinct_to_district.csv` directly (multi-year `precinct_hi_source=("2023","2025")` marks both current-plan source_years `high` with no collapse token). No collapse sidecar generated. |
| ~~`_precinct_votes.csv`~~ | **RETIRED 2026-07-11** — roster_lib now reads the canonical `election_results/west_valley_results_by_precinct.csv` directly (in-library blank/suppressed vote guard). No clean-copy sidecar generated. |

**Never hand-edit the generated CSVs** — regenerate with `python3 roster/build_roster.py`. All
corrections go in `roster_overrides.csv`.

## Council structure & the stagger

**Council–Mayor form. 4 District seats (D1–D4) + 2 AT-LARGE seats (AL1–AL2) + a separately-elected
Mayor = 7 VOTING members (Mayor included).** Every resident is represented by **four** elected
officials: their District member, **both** At-Large members, and the Mayor.

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `D1`, `D3`, `AL1` (At-Large seat 1) | 2019 / 2023 | Jan 2020 / 2024 |
| **B** | `MAYOR`, `D2`, `D4`, `AL2` (At-Large seat 2) | 2021 / 2025 | Jan 2022 / 2026 |

Documented seating dates in the loaded window: **2020-01-07** (first documented 2020 council meeting;
the 2019-cycle members + the four 2017-cycle holdovers), **2022-01-04** (first documented 2022
meeting — 2021-cycle seated), **2024-01-02** (first documented 2024 meeting — 2023-cycle), **2026-01-13**
(first documented 2026 meeting — 2025-cycle), plus **2022-01-18** (the D3 appointment, Resolution
22-11) and **2025-01-28** (the D4 appointment, Resolution 25-11).

### AT-LARGE seat ids are an ANALYTICAL construct — but a MILD one
WVC's two at-large seats are each a **separate single-winner "Vote for 1" contest on its OWN
staggered cycle** (unlike West Jordan's single grouped Vote-for-3 field), so the mapping is naturally
1:1 and stable:
- **AL1 = the 2019/2023 at-large seat — Don Christensen throughout** (won 2019 + 2023).
- **AL2 = the 2021/2025 at-large seat — Lars Nordfelt throughout** (2017-cycle holdover in 2020, then
  won 2021 + 2025).

The county ballot labels both contests simply `"At-Large"` (no ballot seat number), so the **election
cross-check keys on the district LABEL** (`"At-Large"`), not the analytical seat id — but because each
at-large winner sits in a **different year**, `(year, "At-Large", person)` is already unambiguous and
each winner lands on the right AL id anyway.

**Counts: 22 tenures — 18 high / 4 medium / 0 low; 2 VACANT.** 0 overlapping tenures per seat. All
shared-library validators pass (overlap, sources/confidence, seat_id, the vacate-confidence invariant,
the un-recovered-minutes gap detector). There is **no** `minutes_unrecovered.csv`, so the auto
gap-detector has nothing to flag. (The non-voting-mayor invariant does **not** apply here — WVC's
Mayor votes, so `non_voting_mayor=False` and MAYOR rows legitimately carry vote bounds.)

## `council_terms.csv` schema
`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. **`seat_id`** — STABLE id (a redistricting redraws boundaries,
  it does NOT renumber seats): `D1..D4`, `AL1..AL2`, `MAYOR`.
- **`start_date`/`end_date`** — half-open `[start, end)`; `end_date` empty = currently serving;
  chained per seat. A documented departure before the successor's seating inserts an explicit
  `VACANT` interval (begins the day AFTER the predecessor's last day served).
- **`first_vote`/`last_vote`** — earliest/latest observed **Council-body** vote **CLAMPED to each
  tenure's own `[start_date, end_date)` half-open window** (`roster_lib.clamp_vote_bounds`), from
  `cities.db` (`role`, `city='west_valley'`, `body='Council'`); **blank** if the window contains no
  observed vote. **MAYOR rows carry bounds** (the WVC Mayor votes). Because bounds are tenure-scoped
  (not person-level), **Karen Lang** — who held **District 3 (2020–2022)** and then the **Mayor seat
  (2022–present)** under one `karen_lang` key — shows her D3 row clamped to `2020-01-07 … 2021-12-14`
  while her Mayor rows carry their own mayor-era bounds (`2022-01-04 … 2025-12-09`, then
  `2026-01-13 … 2026-05-26`): the cross-body smear is gone structurally. The authoritative service
  interval is always `start_date`/`end_date`.
- **`confidence`** — `high` = an in-file election win (2019/2021/2023/2025) seated at a documented
  first-of-year meeting and corroborated by the cities.db named-vote record, OR one of the two fully-
  documented mid-term appointments (Whetstone D3 Res. 22-11; Wood D4 Res. 25-11) · `medium` = a
  **2017-cycle HOLDOVER** serving at the 2020 floor whose seating election predates the 2019
  election-data floor (four rows — Bigelow MAYOR, Nordfelt AL2, Buhler D2, Fitisemanu D4) · `low` =
  unknown/not-acquired (none in `council_terms`; the `low` rows live in the district/precinct gap
  records).

## The current roster (as-of the 2026-01-13 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Tom Huynh | 2024-01-02 | 2023 | high |
| D2 | Scott Harmon | 2026-01-13 | 2025 | high |
| D3 | William Whetstone | 2024-01-02 | 2023 | high |
| D4 | Cindy Wood | 2026-01-13 | 2025 | high |
| AL1 | Don Christensen | 2024-01-02 | 2023 (At-Large, Vote-for-1) | high |
| AL2 | Lars Nordfelt | 2026-01-13 | 2025 (At-Large, Vote-for-1) | high |
| MAYOR | Karen Lang | 2026-01-13 | 2025 (**votes**) | high |

Matches the latest documented roll (2026-01-13 present list: Lang, Nordfelt, Christensen, Huynh,
Harmon, Whetstone, Wood) and the 2025/2023 election winners.

## The distinctive surface (spot-checked against source minutes)

### The Mayor VOTES (the headline structural fact — OPPOSITE of West Jordan / South Jordan)
A full WVC council roll call names **seven** voters **including the Mayor** (verified: 0 council
meetings exceed 7 distinct voters, and the modal full roll is exactly 7). `non_voting_mayor=False`,
so MAYOR-body rows **carry** `first_vote`/`last_vote`, and **both** mayors (Ron Bigelow, Karen Lang)
are in `DB_KEY`. **Verbatim confirmation** — 2022-03-15, Ordinance 22-10 (the redistricting itself),
where the roll names all six councilmembers **and the Mayor**:

> A roll call vote was taken:
> Councilman Fitisemanu  Yes / Councilman Whetstone  Yes / Councilman Harmon  Yes / Councilman Huynh
> Yes / Councilman Christensen  Yes / Councilman Nordfelt  Yes / **Mayor Lang  Yes**
> **Unanimous.**

The 7-0 roll names the Mayor as the seventh vote. (This is why the roster's MAYOR rows differ from
West Jordan's / South Jordan's, whose non-voting mayors are emptied and excluded from `DB_KEY`.)

### Karen Lang — ONE PERSON, TWO SEATS (District 3 → Mayor)
Lang won **District 3** in 2019 (seated 2020-01-07), then won the **Mayor** seat in 2021 and took
office 2022-01-04 — **vacating D3 mid-term**. One `karen_lang` key spans both bodies (D3 seat + MAYOR
seat), but `first_vote`/`last_vote` are **clamped to each tenure's own `[start, end)` window**, so her
D3 row shows only D3-era votes (2020-01-07 … 2021-12-14) while her Mayor rows carry their own mayor-era
bounds (2022-01-04 … 2025-12-09, then 2026-01-13 … 2026-05-26) — no cross-body smear. Her D3 departure
created the documented D3 vacancy below. (She is the roster's only two-seat person; the seats D3 and
MAYOR do not overlap in time.)

### The D3 mid-term vacancy: Lang → VACANT → Whetstone (appointed) → Whetstone (elected)
When Lang became Mayor (2022-01-04) her D3 seat fell vacant — *"a midterm vacancy has occurred in
District 3 with the election of Karen Lang as Mayor … the office of Councilmember District 3 unfilled
with a remaining term of two years"* (minutes 2022-01-18). After public interviews of the applicants,
the Council appointed **William Whetstone** to D3 by **Resolution 22-11** — *"APPOINT WILLIAM
WHETSTONE AS COUNCILMEMBER FOR DISTRICT 3 … TO SERVE UNTIL THE JANUARY FOLLOWING THE NEXT GENERAL
ELECTION"* — on a **6-0** roll call (he acts as councilmember by that meeting's adjournment).
Whetstone then **won D3 outright at the 2023 general** and was seated 2024-01-02. This yields an
explicit **VACANT interval D3 [2022-01-04, 2022-01-18)** (`high` — begins when Lang's Mayor term
starts). So D3 chains: Lang → **VACANT** → Whetstone (appointed) → Whetstone (elected).

### The D4 mid-term vacancy: Fitisemanu → VACANT → Wood (appointed) → Wood (elected)
Jake Fitisemanu (D4, re-elected 2021) left mid-term: *"This vacancy was created when Jake Fitisemanu
was elected to State House District 30 in the 2024 General Election. The vacancy, governed by Utah
State Code 20A-1-510, lasts until the end of the year"* (minutes 2025-01-28). His last cities.db D4
vote is **2024-12-10**. At the 2025-01-28 Regular meeting the Council appointed **Cindy Wood** to D4
by **Resolution 25-11** — the City Recorder administered the oath that night. Wood then **won D4 at
the 2025 general** and was seated 2026-01-13. This yields an explicit **VACANT interval D4
[2024-12-11, 2025-01-28)** (`high` — begins the day AFTER Fitisemanu's last day served). So D4
chains: Fitisemanu (holdover) → Fitisemanu (elected) → **VACANT** → Wood (appointed) → Wood (elected).
*(Cindy Wood is also the one person who spans the appointed Planning Commission and the elected
Council — see the repo `meeting_minutes`/`db` CLAUDE.md.)*

### The four 2017-cycle HOLDOVERS at the 2020 floor (the only `medium` rows)
In Jan 2020 the four **B-cycle** seats (Mayor, At-Large seat 2, D2, D4) were held by **Ron Bigelow**
(Mayor), **Lars Nordfelt** (AL2), **Steve Buhler** (D2), and **Jake Fitisemanu** (D4) — all seated by
the **2017** election, which is **below the 2019 election-data floor**. Their SERVICE is fully
vote-documented from 2020-01-07, but the term origin is below the floor, so those four rows are
`medium` (no fabricated seating date/election). Their B-cycle successors in 2021: Bigelow **did not
run** (Lang won the open Mayor seat); Buhler **ran for Mayor and lost** (Harmon won D2); Nordfelt and
Fitisemanu each **won their own seat** (continuous service, next `high` row). They are the roster's
only `medium` rows.

## `district_versions.csv` — REAL 4 districts + the 2022 redistricting

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by, source_url,
confidence, note`. WVC has **no council-district polygon on disk** (the `gisportal.wvc-ut.gov`
FeatureServer was not acquired — see `geo/CLAUDE.md`); the authoritative geometry is the Salt Lake
County precinct layer `geo/precincts.geojson` aggregated by district via `geo/precinct_to_district.csv`.

**West Valley DID redistrict** after the 2020 Census: **Ordinance 22-10**, *"amend Title 2, Chapter 3
of the West Valley City Municipal Code, making adjustments in the West Valley City Council District
Boundaries,"* adopted **2022-03-15** on a **7-0 UNANIMOUS** roll call (motion Harmon "Option 1" /
second Huynh; all six councilmembers + Mayor Lang Yes), built on **2020 Census** data (each district
within 1% of the ideal population). First used for the **2023** (D1/D3) and **2025** (D2/D4) district
elections; 2019 + 2021 used the prior lines. *(West Valley redistricts by **ordinance** — like South
Jordan, unlike SLC's/West Jordan's resolution.)*

Versioning (10 rows):
- **`plan_2022`** (current) for D1–D4 — `effective_start=2022-03-15`, open-ended, **high**. Geometry =
  the precinct aggregation (2023 + 2025 district-contest precincts; no overlap).
- **`plan_pre2022`** (prior) for D1–D4 — RECONSTRUCTED 2026-07-19; **GEOMETRY confidence DOWNGRADED
  medium→`low` 2026-07-19**: `geometry_ref=geo/council_districts_pre2022.geojson` (64/74 old WVC codes;
  10 edge holes; WVC038 conflict→D2). VALIDATION 2026-07-19: West Valley publishes NO combined council-
  district GIS (its AGOL org has only a City Boundary; the SLCo-hosted WVC district services are the
  current plan only) → no authoritative prior to validate against; a fragmentation control (current
  dissolve = clean 1–2-piece districts vs this pre-2022 dissolve = up to **8-piece fragments** on D2)
  proves WVC precinct-code renumbering beyond the known holes (the millcreek defect) → geometry
  unreliable, `low`. The `district_precincts` precinct-CODE composition stays `medium` (a faithful SOVC
  record). In force for the 2019/2021 elections. See `scripts/roster_boundary_recon.md`.
- **`At-Large`** citywide row + **`MAYOR`** citywide row — whole-city extent, unaffected by
  redistricting, open-ended, high. (The 2 at-large seats + the Mayor are city-wide; only the 4
  numbered districts are geographic. The WVC Mayor **votes** on council legislation.)

## `district_precincts.csv` — versioned precinct → district composition (districts only)

70 **`plan_2022`** rows read directly from `geo/precinct_to_district.csv` (roster_lib multi-year
`precinct_hi_source`; the retired `_precinct_to_district.csv` sidecar is no longer needed) + **64
`plan_pre2022` RECONSTRUCTED rows** (`medium`, from `geo/precinct_to_district_pre2022.csv`; the 10
renumbered/retired codes are honest holes, absent — was 4 blank `low` GAP rows before 2026-07-19).
All 70 plan_2022 rows are `high` — the current post-2020-census map (built from the 2023 D1/D3 + 2025
D2/D4 district contests; no district overlap). **At-large has no precinct→district composition**
(city-wide). *(One WVC precinct, `WVC067`, has a GIS polygon but no district-race votes → an unmapped
sliver, an honest gap; see `geo/CLAUDE.md`.)*

### Precinct-map cross-check (`--check` / demo (e))

Groups the by-precinct votes by the `district_precincts` (plan_2022) assignment and confirms the
precinct-sum winner matches the roster (the **district seats** only — at-large is city-wide and is
validated by the election cross-check instead):

| Cycle | Seats | Plan | Result |
|---|---|---|---|
| 2023 | D1, D3 | plan_2022 | **RECONCILES** (Huynh 54.5%; Whetstone 56.6%) |
| 2025 | D2, D4 | plan_2022 | **RECONCILES** (Harmon 61.5%; Wood 63.5%) |
| 2019 | D1 | plan_pre2022 | **GAP at the runtime check** — old cycles can't be graded against the *current* plan_2022 map; the plan_pre2022 composition is now reconstructed (`medium`), aggregate winner still matches |
| 2021 | D2, D4 | plan_pre2022 | **GAP at the runtime check** — as above (composition reconstructed 2026-07-19; this live check grades old cycles against plan_2022) |

**All four districts are now in the automated check** (`crosscheck_districts=("1","2","3","4")`,
LANDED 2026-07-11). D2 and D3 were previously excluded because the ballot spells those winners
**`SCOTT L. HARMON`** (2025 D2) and **`WILL WHETSTONE`** (2023 D3) while the vote record / roster use
**`Scott Harmon`** / **`William Whetstone`** — a name-**format** mismatch, **NOT** a data discrepancy
(same pattern as SLC's D2/D6 and South Jordan's D5). roster_lib's `_winner_matches` now resolves BOTH
the precinct-sum winner and the roster winner through `canon_key` before comparing, so these no longer
need a per-city exclusion + hand-verification: **2023 D3 and 2025 D2 RECONCILE automatically** (the
precinct-sum leaders `WILL WHETSTONE` / `SCOTT L. HARMON` resolve to the seated `William Whetstone` /
`Scott Harmon`; no DISCREPANCY). (The per-precinct GIS-vs-ballot mismatch detector is still dead here
because the precinct map is geometric, not ballot-year-scoped; only the aggregate district-winner
check runs. Known SLC/Millcreek/Ogden limitation.)

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/west_valley_results_by_candidate.csv`, municipal **general**
   winners only (2019+). Each winner maps to a **district LABEL** via `seat_for_contest` (District N →
   `"District N"`; At-Large → `"At-Large"`; Mayor → `"Citywide"`), and `crosscheck_field="district"`
   so each year's single at-large winner maps without a fake seat number. UPPER-CASE names normalized
   in `NAME_TO_KEY`; **no two WVC general winners share a surname**, so no disambiguators. The forward
   cross-check confirms **every general winner maps to a tenure — 0 drift** (all **14** winner rows
   across the four cycles map cleanly).
2. **Vote / attendance bounds** — `cities.db` `role` (`city='west_valley'`, `body='Council'`): sets
   `first_vote`/`last_vote` for the **10** distinct council voters. **The Mayor VOTES**, so both
   mayors (Bigelow, Lang) are in `DB_KEY` and MAYOR rows carry bounds. **Fed the Council body ONLY** —
   WVC's separately-meeting **RDA** and **MBA** boards are the same people in a different capacity, so
   no RDA/MBA seats are created (see below).
3. **Minutes events** — oath/seating dates (2020-01-07, 2022-01-04, 2024-01-02, 2026-01-13), the
   redistricting ordinance (2022-03-15, Ord. 22-10), and the **two mid-term appointments** (Whetstone
   D3 2022-01-18 Res. 22-11; Wood D4 2025-01-28 Res. 25-11), read from `meeting_minutes/minutes/**` and
   encoded in `TENURES`. **Two in-window VACANTs** (D3 + D4, both high).
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (**0 rows** — both appointments +
   both VACANTs are fully documented).

## RDA / MBA are NOT separate roster seats

West Valley holds standalone **Redevelopment Agency (RDA)** and **Municipal Building Authority (MBA)**
meetings as distinct bodies (real + populated — 132 RDA + 63 MBA motions in `db/`), but the **same
councilmembers** sit as their boards (one `person`, extra `role`s — e.g. the 2025-02-25 RDA minutes
open with *"CALLED TO ORDER BY CHAIR CINDY WOOD"*). The roster is **COUNCIL-based**:
`load_vote_bounds` reads only `cities.db body='Council'`, and **no RDA/MBA roster seat is created**.
(WVC's case-number project quirk — items keyed `Z-`/`PUD-`/`GPZ-` — is a project-layer concern and
does not touch the roster's people/seats.)

## Honest gaps (recorded, not filled)

- **Prior (`plan_pre2022`) geometry + precinct composition** — **RECONSTRUCTED 2026-07-19** to
  `medium` (was a blank/`low` GAP wrongly noted "not reconstructable"): `district_versions` now
  carries `geometry_ref=geo/council_districts_pre2022.geojson` and `district_precincts` has 64
  populated `medium` rows (WVC038 conflict → 2021 D2). **APPROXIMATE** — the pre-2022 assignment
  dissolved over current-vintage precinct shapes; **10 renumbered codes remain honest holes**
  (WVC068/070–074/076–079, mostly D2). Firming up the holes would need the SL County 2020-vintage
  VistaBallotAreas layer (probed 2026-07-19; not acquirable as a simple open endpoint — UGRC serves
  only the current vintage). See `scripts/roster_boundary_recon.md`.
- **The four 2017-cycle HOLDOVERS' seating (`medium`)** — Bigelow (MAYOR), Nordfelt (AL2), Buhler
  (D2), Fitisemanu (D4) were serving at the 2020 floor but their seating election predates the 2019
  election-data floor and is not in the data; service documented from 2020-01-07, term origin below
  the floor. No fabricated seating date/election.
- **AT-LARGE seat ids are analytical** — the 2 at-large seats are single-winner Vote-for-1 contests
  ballot-labelled just "At-Large" (no seat number). AL1 = the 2019/2023 seat (Christensen), AL2 = the
  2021/2025 seat (Nordfelt); a stable 1:1 mapping (milder than West Jordan's grouped Vote-for-3).

## Where `roster_lib` fit West Valley cleanly (no library changes)

West Valley needed **no new library changes** — it reuses the district + redistricting + precinct path
with two config choices distinct from West Jordan: **`non_voting_mayor=False`** (the WVC Mayor votes,
so MAYOR rows carry vote bounds and the mayors are in `DB_KEY`) and `crosscheck_field="district"` (so
each year's single at-large winner maps on the LABEL). Spots that hit the **already-logged** fleet
backlog (worked around per-city, lib untouched):

1. **`write_precincts()`/`precinct_crosscheck()` need a `source_year` column — LANDED 2026-07-11.**
   WVC's `geo/precinct_to_district.csv` carries per-row `2023`/`2025` tags, and `int(float(votes))`
   had no blank guard. Formerly worked around with two DERIVED sidecars (a collapse-to-token
   `_precinct_to_district.csv` + a suppressed/blank-dropping `_precinct_votes.csv`). Both **RETIRED**:
   roster_lib now accepts a **multi-year `precinct_hi_source`** (`("2023","2025")` → both current-plan
   years earn `high` with no collapse) and applies an **in-library blank/suppressed vote guard**, so it
   reads `geo/precinct_to_district.csv` + `election_results/west_valley_results_by_precinct.csv`
   directly — exactly as the fleet's other precinct cities are being retired.
1b. **Exact-string winner comparison in the crosscheck — LANDED 2026-07-11.** The 2025 D2
   `SCOTT L. HARMON` / 2023 D3 `WILL WHETSTONE` ballot names vs the roster display names would
   false-flag an exact-string compare; D2 + D3 were formerly excluded and hand-verified. roster_lib's
   `_winner_matches` now resolves both names through `canon_key`, so **all four districts are in the
   automated check** and D2/D3 reconcile automatically (no DISCREPANCY).
2. **Person-level vote-bound smear onto multi-seat / non-contiguous tenures** — **LANDED 2026-07-11.**
   Karen Lang's D3 (2020–2022) and MAYOR (2022–present) rows, and Fitisemanu's / Wood's two D4 tenures,
   formerly inherited the whole person-level span. `roster_lib.clamp_vote_bounds()` now assigns
   `first_vote`/`last_vote` as the earliest/latest observed Council vote **within each tenure's own
   `[start, end)` window** (blank if none), so every row is tenure-scoped and the cross-body /
   cross-term smear is gone structurally (no longer merely documented per row).

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2022-01-10 (D3 vacancy) (c) as-of 2025-01-15 (D4 vacancy) (d) address→reps (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a date** — `roster_as_of(date, body)`.
- **Address + date → representative** — `representatives_for_address(address, date)`: resolves a West
  Valley address via `geo/address_to_district.py` (Census geocode → point-in-polygon on
  `precincts.geojson` → `precinct_to_district.csv`) to **District 1–4**, returns that district's member
  on `date` **plus both at-large members and the (voting) Mayor**. Honors `district_versions`: a
  **pre-2022-03-15 date returns an honest GAP** for the geographic district — the shared query helper
  point-in-polygons only against the CURRENT precinct map, so it does not seat a district for a
  `plan_pre2022` date (never a fabricated district), while the city-wide at-large + Mayor still
  resolve. *(The `plan_pre2022` boundary geometry itself is now RECONSTRUCTED on disk —
  `geo/council_districts_pre2022.geojson`, wired into `district_versions`/`district_precincts` at
  `medium` — but the address→rep helper is unchanged from the 5-city convention and still gaps on
  plan_old dates; a plan-aware point-in-polygon against the reconstructed layer is a possible
  follow-up, not part of this pass.)*
