# roster/ — West Jordan rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each West Jordan City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who represents
this address on this date?* — none of which the flat CSVs can answer.

West Jordan is a **MIXED Council–Mayor city**: **4 geographic council districts** (D1..D4) + **3
city-wide AT-LARGE seats** (AL1..AL3) + a **separately-elected strong Mayor who does NOT vote** on
council motions (the strong-mayor form was adopted at the **2019** election — West Jordan's first
strong-mayor cycle). A full council roll call tops out at **7** (never 8). It is the fleet's first
MIXED (districts + at-large) roster; the pure-district templates are South Jordan and Taylorsville
(both 5 districts + non-voting mayor + 2022 redistricting + precinct/address join). West Jordan
adds the 3 at-large seats — validated through the **election** cross-check, not the precinct one —
and a documented mid-term D2 vacancy. Built on the shared `../../scripts/roster_lib.py`; the driver
`build_roster.py` carries only West Jordan's data.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation driver (WJ data + config). Regenerates the CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — **21 tenures across 8 stable seats** (incl. **1 VACANT**). |
| `district_versions.csv` | Boundary interval table — **REAL 4 districts × 2 plans** (the 2022 redistricting) + an At-Large citywide row + a Mayor citywide row (10 rows). |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped, **districts only** — at-large is city-wide). 96 `plan_2022` rows (`high`) + **68 `plan_pre2022` reconstructed rows (`medium`)**. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows** (the one VACANT is fully documented — no override needed). |
| `_precinct_to_district.csv` | **RETIRED 2026-07-11** — roster_lib reads the canonical geo/election files directly (multi-year `precinct_hi_source` + blank/suppressed guard). `precinct_hi_source=("2023", "gis")` now marks BOTH current-plan `source_year` values in `geo/precinct_to_district.csv` (2023: 92 rows, gis: 4 rows) `high` with no collapse sidecar; `precinct_map_path` points straight at `geo/precinct_to_district.csv`. |
| `_precinct_votes.csv` | **RETIRED 2026-07-11** — roster_lib reads the canonical geo/election files directly (multi-year `precinct_hi_source` + blank/suppressed guard). `precincts_byprecinct_path` now points straight at `election_results/west_jordan_results_by_precinct.csv`; the shared `precinct_crosscheck` has a built-in blank/suppressed/non-numeric vote guard, so the defensive copy is no longer needed (WJ had zero suppressed cells anyway). |

**Never hand-edit the generated CSVs** — regenerate with `python3 roster/build_roster.py`. All
corrections go in `roster_overrides.csv`.

## Council structure & the stagger

**Council–Mayor (strong-mayor) form. 4 District seats (D1–D4) + 3 AT-LARGE seats (AL1–AL3) = 7
voting council members + a NON-VOTING strong Mayor.** Every resident is represented by **five**
elected officials: their District member, **all three** At-Large members, and the Mayor (who does
not vote on council legislation).

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `MAYOR`, `D1`, `D2`, `D3`, `D4` | 2019 / 2023 | Jan 2020 / 2024 |
| **B** | At-Large (grouped **Vote-for-3** → `AL1`, `AL2`, `AL3`) | 2021 / 2025 | Jan 2022 / 2026 |

Documented seating dates in the loaded window: **2020-01-08** (first documented 2020 council
meeting; oath of office reported — the 2019-cycle members + the two at-large holdovers), **2022-01-12**
(first documented 2022 meeting — 2021 at-large), **2024-01-10** (first documented 2024 meeting; the
"City Council Oath of Office Ceremony" was the prior week — 2023-cycle), **2026-01-13** (first
documented 2026 meeting; oath ceremonies "in the last week" — 2025 at-large), plus **2023-11-29**
(the D2 appointment, Resolution 23-070).

### AT-LARGE seat ids are an ANALYTICAL construct
The three at-large seats are legally **INTERCHANGEABLE** and are filled **together** in one grouped
**"Vote for 3"** field (the top-3 vote-getters win all three seats) — there is **no ballot seat
number**. `AL1`/`AL2`/`AL3` are assigned to **maximize person-continuity** so the chains read
cleanly:
- **AL1 = Kayleen Whitelock throughout** (she serves continuously 2020 → present).
- **AL2 = Kelvin Green (2019 + 2021) → Annette Harris (2025).**
- **AL3 = Chad Lamb (holdover) → Pamela Bloom (2021) → Jessica Wignall (2025).**

The Green→Harris and Bloom→Wignall pairings are arbitrary — any assignment yields the same clean
cycle-boundary handoffs. The **election cross-check keys on the district LABEL** (`"At-Large"`), not
the analytical seat id, so it is agnostic to which winner lands on which AL id.

**Counts: 21 tenures — 19 high / 2 medium / 0 low; 1 VACANT.** 0 overlapping tenures per seat. All
shared-library validators pass (overlap, sources/confidence, seat_id, the non-voting-mayor
invariant, the vacate-confidence invariant, the un-recovered-minutes gap detector). `minutes_unrecovered.csv`
is empty, so the auto gap-detector has nothing to flag.

## `council_terms.csv` schema
`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. **`seat_id`** — STABLE id (a redistricting redraws boundaries,
  it does NOT renumber seats): `D1..D4`, `AL1..AL3`, `MAYOR`.
- **`start_date`/`end_date`** — half-open `[start, end)`; `end_date` empty = currently serving;
  chained per seat. A documented departure before the successor's seating inserts an explicit
  `VACANT` interval (begins the day AFTER the predecessor's last day served).
- **`first_vote`/`last_vote`** — the earliest/latest observed Council vote from `cities.db`
  (`city='west_jordan'`, `body='Council'`) that falls **within each tenure's own `[start, end)`
  window** (the tenure-window clamp, landed 2026-07-11 — blank if the window holds no observed
  vote). **Mayor rows are blank** (`non_voting_mayor=True`). Because the bounds are clamped per
  tenure, a person with two non-contiguous tenures now shows each tenure's OWN span — e.g. **Chad
  Lamb** (AL3 holdover 2020–2022 **and** D1 2024–present) shows `2020-01-08 / 2021-12-15` on the AL3
  row and `2024-01-10 / 2026-05-12` on the D1 row (no longer one shared person-level span). The
  authoritative service interval is always `start_date`/`end_date`.
- **`confidence`** — `high` = an in-file election win (2019/2021/2023/2025) seated at a documented
  first-of-year meeting/oath and corroborated by the cities.db named-vote record, OR the fully-
  documented 2023 D2 resignation→appointment chain · `medium` = an **at-large HOLDOVER** serving at
  the 2020 floor whose seating election predates the 2019 election floor (only 2 rows — Whitelock AL1
  + Lamb AL3) · `low` = unknown/not-acquired (none in `council_terms`; the `low` rows live in the
  district/precinct gap records).

## The current roster (as-of the 2026-01-13 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Chad Lamb (Council Chair) | 2024-01-10 | 2023 | high |
| D2 | Bob Bedore (Council Chair 2026) | 2024-01-10 | 2023 | high |
| D3 | Zach Jacob | 2024-01-10 | 2023 | high |
| D4 | Kent Shelton | 2024-01-10 | 2023 | high |
| AL1 | Kayleen Whitelock | 2026-01-13 | 2025 (Vote-for-3, rank 1) | high |
| AL2 | Annette Harris | 2026-01-13 | 2025 (Vote-for-3, rank 2) | high |
| AL3 | Jessica Wignall (Vice Chair) | 2026-01-13 | 2025 (Vote-for-3, rank 3) | high |
| MAYOR | Dirk Burton | 2024-01-10 | 2023 (non-voting) | high |

Matches the latest documented roll (2026-01-13 present list: Bedore, Wignall, Harris, Jacob, Lamb,
Shelton, Whitelock) and the 2025/2023 election winners.

## The distinctive surface (spot-checked against source minutes)

### The NON-VOTING strong Mayor (the headline structural fact)
West Jordan adopted the **strong-mayor** form at the **2019** election; **Dirk Burton** is the first
strong Mayor. He presides and appoints the executive staff (e.g. selected the Police Chief at the
2020-01-08 meeting) but does **NOT** vote on council motions. He is **absent from every cities.db
council role** and from **every vote roll** (verified: **0** council meetings exceed 7 distinct
voters). `non_voting_mayor=True` empties every MAYOR-body `first_vote`/`last_vote`, and `dirk_burton`
is deliberately **excluded from `DB_KEY`**. **Verbatim confirmation** — 2025-02-25, Ordinance No.
25-03 (Oquirrh Highlands annexation), where the minutes list Mayor Burton under **STAFF** (not
COUNCIL):

> **COUNCIL:** Chair Chad Lamb, Vice Chair Kayleen Whitelock, Bob Bedore, Pamela Bloom (remote),
> Kelvin Green, Zach Jacob, Kent Shelton
> **STAFF:** … **Mayor Dirk Burton** …
> …
> The vote was recorded as follows: **YES:** Zach Jacob, Chad Lamb, Bob Bedore, Pamela Bloom, Kelvin
> Green, Kent Shelton, Kayleen Whitelock — **The motion passed 7-0.**

The roll names exactly the seven councilmembers; the Mayor is absent from the vote. (The 2022-04-13
Resolution 22-011 redistricting roll call is another example — a 5-0 with the Mayor "explaining the
recommendation" on the *next* item but never in the vote.)

### The IN-WINDOW D2 vacancy: Worthen → VACANT → Bennett → Bedore (2023)
The one fully-documented mid-term vacancy. **Melissa Worthen** (D2, elected 2019) was honored as
*"Outgoing District 2 Council Member"* on **2023-10-25** (her last meeting / last cities.db D2 vote)
and left mid-term (*"deeply missed … her new adventures"*). At a **2023-11-29 SPECIAL** meeting
("FILLING MID-TERM VACANCY FOR DISTRICT TWO") the Council appointed **Robert (Rob) Bennett** by
**Resolution No. 23-070** — *"appointing Robert Bennett to fill the mid-term vacancy in West Jordan
City Council District 2"* — selected over **Bob Bedore** by a documented **coin toss** after a tied
electronic vote; the City Recorder administered the oath that same night. **Bedore had already won
the D2 seat at the 2023 general (Nov)** but could not be seated until January, so Bennett filled the
~6-week interim. This yields an explicit **VACANT interval D2 [2023-10-26, 2023-11-29)** (`high` —
begins the day AFTER Worthen's last day served, per the fleet vacate-date convention). **Bedore was
seated 2024-01-10.** So D2 chains: Worthen → **VACANT** → Bennett (appointed) → Bedore (elected).

### ONE PERSON, TWO SEATS (non-contiguous) — Chad Lamb
**Chad Lamb** held an **at-large** seat (`AL3`) in 2020–2022 — he was **Mayor Pro Tem** and chaired
the first 2020 meeting — then **LOST** the 2021 grouped at-large race (4th of 6) and left Jan 2022.
He returned by winning **D1** in 2023 (seated 2024-01-10). One `chad_lamb` key spans both; the seats
(`AL3`, `D1`) do **not** overlap, and there is a genuine ~2-year off-council gap (2022–2024) between
them. (Likewise **Kelvin Green** spans AL2 continuously — the single at-large 2019 seat then the
grouped at-large 2021 seat.)

### The two AT-LARGE HOLDOVERS at the 2020 floor (the only `medium` rows)
In Jan 2020 the three at-large seats were held by **Green** (won the 2019 single at-large seat),
**Whitelock**, and **Lamb** (Mayor Pro Tem). Whitelock and Lamb were seated by a **pre-2019
(pre-strong-mayor) at-large election below the election floor** — their **service** is fully
vote-documented from 2020-01-08, but the term origin is below the floor, so those two rows are
`medium` (no fabricated seating date/election). They are the roster's only `medium` rows.

### The 2019 single-seat at-large (the strong-mayor transition)
2019 was West Jordan's first strong-mayor election; the county SOVC shows a **single** at-large seat
that year (**Vote for 1**, won by Green), not the grouped **Vote-for-3** field seen from 2021 on.
Green's 2019 at-large term ran **~2 years** (2020→2022) to sync all three at-large seats onto the
consolidated 2021/2025 cycle; he was re-elected to a full term in 2021. (Documented as a source
feature, not a theory — see `election_results/CLAUDE.md`.)

## `district_versions.csv` — REAL 4 districts + the 2022 redistricting

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by, source_url,
confidence, note`. Geometry is not stored inline — `geometry_ref` points at
`geo/council_districts.geojson` (the **city's authoritative 4-district ArcGIS layer**;
`Council_Districts` FeatureServer).

**West Jordan DID redistrict** after the 2020 Census: **Resolution No. 22-011**, *"adopting new City
Council Districts for the City of West Jordan,"* adopted **2022-04-13** (Business Item 8a) on a
**5-0** roll call (motion Worthen / second Green; Bloom stepped out + McConnehey absent): Council
Chair Whitelock, Vice Chair Green, Jacob, Pack, Worthen all Yes. *(An earlier **Ordinance 21-44**,
2021-11-16, amended the redistricting **CODE** Title 1 Ch.15; Res. 22-011 adopts the actual **MAP**.)*
First used for the **2023** district elections; 2019 used the prior lines. *(West Jordan redistricts
by **resolution** — like SLC/Taylorsville, unlike South Jordan's ordinance.)*

Versioning (10 rows):
- **`plan_2022`** (current) for D1–D4 — real geometry in `geo/council_districts.geojson`,
  `effective_start=2022-04-13`, open-ended, **high**. (The city layer agrees with the 2023
  election-derived precinct map on 86% of shared precincts vs 69% for 2019 → current vintage.)
- **`plan_pre2022`** (prior) for D1–D4 — RECONSTRUCTED 2026-07-11; **GEOMETRY confidence DOWNGRADED
  medium→`low` 2026-07-19**: `geometry_ref=geo/council_districts_pre2022.geojson` (all 68 WJD precincts
  present, 0 holes). VALIDATION 2026-07-19 probed West Jordan's ArcGIS org — it publishes NO pre-2022
  layer (all layers are the current 2022+ plan), and a fragmentation control (current-assignment dissolve =
  clean 1–2-piece districts vs this pre-2022 dissolve = 3–5-piece fragments) proves the WJD precinct codes
  were partially renumbered between the 2019 SOVC vintage and current UGRC shapes (the millcreek defect,
  milder here) → geometry unreliable, `low`. The `district_precincts` precinct-CODE composition stays
  `medium` (a faithful SOVC record). In force through the 2019 elections. See `scripts/roster_boundary_recon.md`.
- **`At-Large`** citywide row + **`MAYOR`** citywide row — whole-city extent, unaffected by
  redistricting, open-ended, high. (The 3 at-large seats + the Mayor are city-wide; only the 4
  numbered districts are geographic.)

## `district_precincts.csv` — versioned precinct → district composition (districts only)

96 **`plan_2022`** rows read directly from `geo/precinct_to_district.csv` (the two precinct sidecars
were RETIRED 2026-07-11) + **68 `plan_pre2022`** rows now POPULATED from the reconstructed
`geo/precinct_to_district_pre2022.csv` (`precinct_id` filled, `confidence=medium`).
All 96 plan_2022 rows are `high` — the current post-2020-census map (per-district counts D1=25,
D2=21, D3=27, D4=23; 0 splits). The 68 plan_pre2022 rows are the reconstructed pre-2022 (2012-cycle)
composition (68/68 WJD precincts, `medium` — current-vintage precinct shapes). **At-large has no
precinct→district composition** (city-wide).

### Precinct-map cross-check (`--check` / demo (e))

Groups the by-precinct votes by the `district_precincts` (plan_2022) assignment and confirms the
precinct-sum winner matches the roster (the **4 district seats** only — at-large is city-wide and is
validated by the election cross-check instead):

| Cycle | Seats | Plan | Result |
|---|---|---|---|
| 2023 | D1, D2, D3, D4 | plan_2022 | **RECONCILES** (Lamb 64.5%, Bedore 54.2%, Jacob 65.8%, Shelton 57.2%) |
| 2019 | D1, D2, D3, D4 | plan_pre2022 | **GAP at the runtime election-crosscheck** — a 2019 contest can't be graded against the *current* map; the plan_pre2022 *composition* is now reconstructed (`medium`) but this live check grades old cycles against plan_2022 (aggregate winner still matches the roster) |

No district needed exclusion — the winner compare is via `roster_lib._winner_matches` (canon_key,
landed 2026-07-11), so a SOVC-vs-roster name-format difference never false-flags. (As of the
2026-07-11 sidecar retirement, `precinct_hi_source=("2023", "gis")` is a tuple of real `source_year`
values, and WJ's ballot precinct codes are `WJD###` — matching the `geo/precinct_to_district.csv`
codes exactly — so the per-precinct GIS-vs-ballot MISMATCH detector now runs LIVE for the 2023
cycle and finds **0 mismatches** (in addition to the aggregate district-winner check). The old
"token, not a year → detector dead" limitation no longer applies to West Jordan.)

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/west_jordan_results_by_candidate.csv`, municipal **general**
   winners only (2019+). Each winner maps to a **district LABEL** via `seat_for_contest` (District N
   → `"District N"`; At-Large → `"At-Large"`; Mayor → `"Citywide"`), and `crosscheck_field="district"`
   so the grouped Vote-for-3 at-large winners all map without a fake seat number. UPPER-CASE names
   normalized in `NAME_TO_KEY`; **no two WJ general winners share a surname**, so no disambiguators
   (GREEN resolves to Kelvin — the only at-large/winner Green; the 2023 D1 loser Rulon Green never
   passes through `canon_key`). The forward cross-check confirms **every general winner maps to a
   tenure — 0 drift** (all 17 winner rows — 6+3+5+3 across 2019/2021/2023/2025 — map cleanly).
2. **Vote / attendance bounds** — `cities.db` `role` (`city='west_jordan'`, `body='Council'`): sets
   `first_vote`/`last_vote` for the 13 distinct council voters. **Mayor Burton is absent from
   cities.db** and MAYOR rows are emptied by `non_voting_mayor`.
3. **Minutes events** — oath/seating dates (2020-01-08, 2022-01-12, 2024-01-10, 2026-01-13), the
   redistricting resolution (2022-04-13, Res. 22-011), and the **2023 D2 resignation→appointment**
   (Worthen last served 2023-10-25; Resolution 23-070 appoints Bennett 2023-11-29), read from
   `meeting_minutes/minutes/**` and encoded in `TENURES`. **One in-window VACANT** (D2, high).
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (**0 rows** — the VACANT is fully
   documented).

## Honest gaps (recorded, not filled)

- **Prior (`plan_pre2022`) geometry + precinct composition** — **RECONSTRUCTED 2026-07-11** to
  `medium` (was a blank/`low` GAP): `district_versions` now carries
  `geometry_ref=geo/council_districts_pre2022.geojson` and `district_precincts` has 68 populated
  `medium` rows. APPROXIMATE — the pre-2022 (2012-cycle) assignment dissolved over current-vintage
  precinct shapes, so faithful where only district lines moved, approximate where precincts were
  reshaped; not the fetched-authoritative current plan. See `scripts/roster_boundary_recon.md`.
- **The two at-large HOLDOVERS' seating (`medium`)** — Whitelock (AL1) + Lamb (AL3) were serving at
  the 2020 floor but their seating at-large election predates the 2019 election floor (pre-strong-
  mayor era) and is not in the data; service documented from 2020-01-08, term origin below the floor.
  No fabricated seating date/election.
- **AT-LARGE seat ids are analytical** — the 3 at-large seats are legally interchangeable (grouped
  Vote-for-3, no ballot seat number). AL1/AL2/AL3 maximize person-continuity; the Green→Harris and
  Bloom→Wignall pairings are arbitrary. This is a modeling choice, disclosed here and in the driver.

## Where `roster_lib` fit West Jordan cleanly (and the already-logged batch items it touches)

West Jordan needed **no new library changes** — it is the fleet's first **MIXED** (districts +
at-large) roster, and it reuses the district + non-voting-mayor + redistricting + precinct path with
two config choices: `crosscheck_field="district"` (so the grouped at-large winners map on the LABEL,
not a per-seat id) and `citywide_rows`/`citywide_seats` carrying **both** the At-Large seats and the
Mayor. Spots that hit the **already-logged** fleet backlog (worked around per-city, lib untouched):

1. **`write_precincts()`/`precinct_crosscheck()` need a `source_year` column + a blank-vote guard —
   LANDED 2026-07-11 (both sidecars RETIRED).** WJ's `geo/precinct_to_district.csv` carries per-row
   `2023`/`gis` tags and the raw by-precinct file could carry blank/suppressed cells. Formerly worked
   around with the two DERIVED sidecars (`_precinct_to_district.csv` collapsed to one
   `plan2022current` token; `_precinct_votes.csv` dropped suppressed/blank rows). The hardened
   `roster_lib` now (a) accepts a **multi-year `precinct_hi_source` tuple** (`("2023", "gis")` — both
   current-plan values stay `high`, so the 96 rows keep their `{high:96}` distribution with no
   collapse) and (b) has a **built-in blank/suppressed/non-numeric vote guard** in
   `precinct_crosscheck`. So `precinct_map_path` / `precincts_byprecinct_path` point straight at the
   canonical `geo/` + `election_results/` files — fixed in the shared library, not worked around
   per-city (same retirement applied to Ogden/Sandy/SJ/Taylorsville).
2. **Vote-bound clamp onto non-contiguous tenures — LANDED 2026-07-11.** Chad Lamb's AL3 (2020–2022)
   and D1 (2024–present) rows formerly both inherited his whole person-level span (2020-01-08 …
   2026-05-12). The **vote-bound clamp** (`roster_lib.clamp_vote_bounds`) now confines each tenure's
   `first_vote`/`last_vote` to its own `[start, end)` window, so the AL3 row shows
   2020-01-08..2021-12-15 and the D1 row shows 2024-01-10..2026-05-12. Fixed in the shared library,
   not worked around per-city.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2023-11-15 (mid D2 vacancy) (c) address→reps (d) redistricting (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a date** — `roster_as_of(date, body)`.
- **Address + date → representative** — `representatives_for_address(address, date)`: resolves a West
  Jordan address via `geo/address_to_district.py` (Census geocode → point-in-polygon on
  `council_districts.geojson`) to **District 1–4**, returns that district's member on `date` **plus
  all three at-large members and the (non-voting) Mayor**. Honors `district_versions`: a
  **pre-2022-04-13 date now resolves against the reconstructed `plan_pre2022` map** (`medium`,
  approximate — see the recon note), while the city-wide at-large + Mayor still resolve.
