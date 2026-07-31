# roster/ — Taylorsville rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Taylorsville City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who represents
this address on this date?* — none of which the flat CSVs can answer.

Taylorsville is a **PURE-DISTRICT Council–Mayor (executive-mayor) city**: **5 geographic council
districts** (D1..D5, **NO at-large/citywide council seats**) + a **separately-elected executive
Mayor who does NOT vote** on council legislation (the council elects its own Chair/Vice-Chair from
the five members to conduct meetings). It is a district city like South Jordan
(`south_jordan_city_council/roster/`, the reference template) — pure districts + a non-voting mayor
+ a 2020-census redistricting + a precinct/address join — but with MORE motion: **one in-window
mid-term vacancy** (the 2020 D3 Christopherson→Barbieri chain), **two councilmember→Mayor
crossovers** (Larry Johnson, Kristie Overson), and **two out-of-cycle D3 specials**. Built on the
shared `../../scripts/roster_lib.py`; the driver `build_roster.py` carries only Taylorsville's data.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation driver (Taylorsville data + config). Regenerates the CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — **35 tenures across 6 stable seats** (incl. **2 VACANT**). |
| `district_versions.csv` | Boundary interval table — **REAL 5 districts × 2 plans** (the 2022 redistricting) + a Mayor/citywide row (11 rows). |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped). 44 `plan_2022` rows (`high`) + **38 `plan_pre2022` reconstructed rows (`medium`)**. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **1 data row** (the D2 interim-VACANT note — see below). |
| ~~`_precinct_to_district.csv`~~ | **RETIRED 2026-07-11** — roster_lib now reads the canonical `geo/precinct_to_district.csv` directly (multi-year `precinct_hi_source=("2023","2025")` marks both current-plan source_years `high` with no collapse token). No collapse sidecar generated. |
| ~~`_precinct_votes.csv`~~ | **RETIRED 2026-07-11** — roster_lib now reads the canonical `election_results/taylorsville_results_by_precinct.csv` directly (in-library blank/suppressed vote guard). No clean-copy sidecar generated. |

**Never hand-edit the generated CSVs** — regenerate with `python3 roster/build_roster.py`. All
corrections go in `roster_overrides.csv`.

## Council structure & the stagger

**Council–Mayor (executive-mayor) form. 5 District seats (D1–D5) = 5 voting council members + a
NON-VOTING executive Mayor.** Every resident is represented by **2** elected officials: their
District member and the citywide Mayor (who does not vote on council legislation).

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `MAYOR`, `D4`, `D5` | 2009 / 13 / 17 / 21 / 25 | Jan 2010 / 14 / 18 / 22 / 26 |
| **B** | `D1`, `D2`, `D3` | 2007 / 11 / 15 / 19 / 23 | Jan 2008 / 12 / 16 / 20 / 24 |

Documented seating dates in the loaded window: **2020-01-08** (first documented 2020 council
meeting; cities.db `first_seen` for the 2019-cycle members), **2022-01-05** (Swearing-In of Elected
Officials, A-cycle), **2024-01-03** (Swearing-In ceremony, B-cycle), **2026-01-07** (Administration
of Oath of Office, A-cycle), plus the **2020-09-30** D3 appointment (Ordinance 20-17). Pre-2020-floor
term-starts use `YYYY-01-01` (inferred from the stagger, flagged medium).

**Counts: 35 tenures — 15 high / 19 medium / 1 low; 2 VACANT.** 0 overlapping tenures per seat. All
shared-library validators pass (overlap, sources/confidence, seat_id, the non-voting-mayor invariant,
the vacate-confidence invariant, the un-recovered-minutes gap detector).

## `council_terms.csv` schema
`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. **`seat_id`** — STABLE id (a redistricting redraws boundaries,
  it does NOT renumber seats): `D1..D5` + `MAYOR`.
- **`start_date`/`end_date`** — half-open `[start, end)`; `end_date` empty = currently serving;
  chained per seat (a tenure ends when the next on the same seat begins). A documented departure
  before the successor's seating inserts an explicit `VACANT` interval (begins the day AFTER the
  predecessor's last day served).
- **`first_vote`/`last_vote`** — first/last observed **Council-body** vote from `cities.db`
  (`role`, `city='taylorsville'`, `body='Council'`), **clamped to each tenure's own
  `[start_date, end_date)` half-open window**. **Mayor rows are blank** (`non_voting_mayor=True`).
  A pre-floor term whose holder's only recorded votes belong to a LATER term is therefore
  **BLANK** — e.g. Burgess's 2012 D1 row carries no vote bounds (his earliest named db votes,
  2020-01-08+, fall in a later term). The authoritative service interval is always
  `start_date`/`end_date`, never the vote bounds. (Larry Johnson and Kristie Overson cast NO council vote in the loaded window
  — both were pre-floor councilmembers and the Mayor is non-voting — so their council rows are blank.)
- **`confidence`** — `high` = a documented Jan swearing-in (2022-01-05 / 2024-01-03 / 2026-01-07) or
  a documented in-window appointment/departure (the 2020 D3 chain), corroborated by the named-vote
  record · `medium` = an election-anchored term predating the 2020 data floor (win = fact, continuous
  service inferred; incl. every pre-2018 start and the 2017-cycle terms whose Jan-2018 start is
  inferred though the tail is vote-corroborated) · `low` = unknown/not-acquired (the D2 2018-2020
  interim VACANT + the prior-plan district/precinct gap records).

## The current roster (as-of the 2026-01-07 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Ernest Glen Burgess | 2024-01-03 | 2023 | high |
| D2 | Curt Cochran | 2024-01-03 | 2023 (unopposed) | high |
| D3 | Anna Barbieri | 2024-01-03 | 2023 (unopposed) | high |
| D4 | Meredith Harker (Council Chair) | 2026-01-07 | 2025 | high |
| D5 | Bob Knudsen (Chair-elect) | 2026-01-07 | 2025 | high |
| MAYOR | Kristie Steadman Overson | 2026-01-07 | 2025 (non-voting) | high |

## The distinctive surface (spot-checked against source minutes)

### The NON-VOTING executive Mayor (the headline structural fact)
Taylorsville uses Utah's **council–mayor (executive-mayor)** form: the Mayor is the executive and
does **NOT** vote on council motions; the council elects its own **Chair** (one of the five district
members) to conduct meetings, so a full council roll call tops out at **5**. `non_voting_mayor=True`
empties every MAYOR-body `first_vote`/`last_vote`, and Mayor Overson is **absent from the cities.db
person table** — the only distinct named voters in `all_votes.csv` are the seven district members.
**Verbatim confirmation** — the 2020-06-17 `Ordinance No. 20-14` deny motion, a contested **4-1**:

> **Attendance** — Mayor Kristie Overson · **Councilmembers Present** — Council Chair Meredith
> Harker, Vice Chair Brad Christopherson, Council Member Dan Armstrong (electronically), Council
> Member Ernest Burgess, Council Member Curt Cochran
> …
> MOTION: Councilmember Cochran moved to deny Ordinance No. 20-14. … Councilmember Armstrong **Yes**
> / Councilmember Burgess **Yes** / Chair Harker **No** / Vice Chair Christopherson **Yes** /
> Councilmember Cochran **Yes** — **The motion passed 4-1**

The Mayor led the Pledge but is **absent from the vote** — the roll names exactly the five
councilmembers. (The 2022-05-04 Resolution 22-11 redistricting roll call is another 4-1 showing the
same 5-member roll with Barbieri as Chair.)

### The IN-WINDOW D3 vacancy: Christopherson → VACANT → Barbieri (2020)
The one fully-documented mid-term vacancy. **Brad Christopherson** (D3, re-elected 2019) **DEPARTED
mid-term** after the **2020-08-19** meeting — his last day served / last cities.db vote (that meeting
was his farewell; the Mayor "expressed her very best wishes"). The minutes describe a **move OUTSIDE
Taylorsville** (a residency-loss vacancy; the word "resign" does not appear) — `end_event='resigned'`
is the coarse normalized "left the seat mid-term" bucket, with the faithful reason kept in the row note. The 2020-09-02 minutes note *"The District
No. 3 council seat was temporarily vacant."* The council took applications (deadline 2020-09-09),
interviewed on **2020-09-30**, and appointed **Anna Barbieri** by **Ordinance No. 20-17** that same
night — *"Councilmember Armstrong moved to approve Ordinance 20-17, appointing Anna Barbieri to
represent District No. 3 … Barbieri had become a member of the city council immediately upon approval
of Ordinance 20-17."* She was formally sworn on **2020-10-07** (*"Swearing-In Ceremony for District
No. 3 Councilmember Anna Barbieri"*; her first named cities.db vote is 2020-10-07). This yields an
explicit **VACANT interval D3 [2020-08-20, 2020-09-30)** (`high` — fully documented; begins the day
AFTER Christopherson's last day served, per the fleet vacate-date convention). Barbieri then won the
**2021 D3 SPECIAL** (unexpired-term balance, uncontested) and the **2023 D3** full term.

### The D2 2018–2020 interim VACANT (an honest below-floor gap — the override layer)
**Kristie Overson** held D2 (elected 2011 & 2015) and **vacated it ~2 years early** upon becoming
Mayor (sworn ~Jan 2018 — see the crossover below). Her 2016 D2 term ends **2018-01-01**; the **2019
general (Cochran) is the REGULAR B-cycle D2 election** whose new term begins **2020-01-08**. The
2018-2020 interim seat-holder (Utah practice is a council appointment) is entirely **below the 2020
data floor and is undocumented in the loaded sources**, so this window is an explicit **`low`-
confidence VACANT** whose note is corrected via **`roster_overrides.csv`** (the library's default
"seat empty" note would misdescribe an undocumented-appointee gap). **The seat is not claimed empty
and no appointee name is fabricated** — the low confidence signals "holder unknown here."

### Two councilmember → Mayor CROSSOVERS (handled, no overlap)
Both handled per the fleet convention — council bounds on council rows, MAYOR rows emptied by the
flag, no person-level overlap:
- **Larry Johnson**: D5 (elected 2009) → **Mayor** (elected 2013). A **CLEAN term-boundary handoff**
  — his D5 term ended Jan 2014 exactly as his Mayor term began (Armstrong won D5 2013 and was seated
  Jan 2014, so **no vacancy**). D5 `[2010-01-01, 2014-01-01)` and MAYOR `[2014-01-01, 2018-01-01)`
  do not overlap. (He later ran for D5 2021 and lost to Knudsen — SAME PERSON, one `larry_johnson` key.)
- **Kristie Overson**: D2 (elected 2011 & 2015) → **Mayor** (elected 2017, def. incumbent Mayor Larry
  Johnson). She vacated D2 EARLY (Jan 2018); D2 `[2016-01-01, 2018-01-01)` and MAYOR `[2018-01-01, …)`
  do not overlap. One `kristie_overson` key spans both bodies.

### Two out-of-cycle D3 SPECIALS (below floor)
D3 is a B-cycle seat (2007/11/15/19/23), so a D3 contest in an A-cycle year fills an unexpired term:
- **2013 D3** — the 2011 D3 winner **Rechtenbach** ran for Mayor 2013 (lost) and vacated D3;
  **Christopherson** won the balance (uncontested), then the full term 2015.
- **2021 D3** — the in-window Christopherson→Barbieri chain above; **Barbieri** won the balance.

Neither is a permanent cycle shift (flagged in the election `note` column and in each tenure note).

## `district_versions.csv` — REAL 5 districts + the 2022 redistricting

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by, source_url,
confidence, note`. Geometry is not stored inline — `geometry_ref` points at
`geo/council_districts.geojson` (**PRECINCT-DERIVED** — Taylorsville publishes no official district
GIS layer; the 5 polygons are dissolved from the 44 TAY precincts via the district-contest precinct
rows).

**Taylorsville DID redistrict** after the 2020 Census: **Resolution No. 22-11**, *"A Resolution of
the City of Taylorsville adopting Final Redistricting Maps Pursuant to … Utah Code 10-3-205.5,"*
adopted **2022-05-04** on a **4-1** roll call (motion Harker / second Burgess; **Cochran No**) —
60,448 residents, ~12,100 per district, "0% deviation," lines drawn **not** to dissect voting
precincts. First used for the **2023** (B: D1/D2/D3) and **2025** (A: D4/D5) elections; the 2021
election used the prior lines. *(Taylorsville redistricts by **resolution** — like SLC/Sandy, unlike
South Jordan's ordinance.)*

Versioning (11 rows):
- **`plan_2022`** (current) for D1–D5 — precinct-derived geometry in `geo/council_districts.geojson`,
  `effective_start=2022-05-04`, open-ended, **high**.
- **`plan_pre2022`** (prior) for D1–D5 — RECONSTRUCTED 2026-07-11; **GEOMETRY confidence DOWNGRADED
  medium→`low` 2026-07-19**: `geometry_ref=geo/council_districts_pre2022.geojson` (38 of 39 TAY precincts;
  TAY045 edge hole). VALIDATION 2026-07-19: Taylorsville publishes NO council-district GIS at all (only a
  retail/demographic map; legal lines are textual in municipal code 13.04.100) → nothing to validate
  against; a fragmentation control (current-assignment dissolve = clean 1-piece districts vs this pre-2022
  dissolve = up to 4-piece fragments on D1/D3/D5) still exposes SLCo precinct renumbering, the same defect
  proven in sibling cities → geometry unreliable, `low`. The `district_precincts` precinct-CODE composition
  stays `medium` (a faithful SOVC record). In force through the 2021 elections. See
  `scripts/roster_boundary_recon.md`.
- **`citywide`** row for `MAYOR` — whole-city extent, unaffected by redistricting, open-ended, high.
  (Taylorsville has **no** at-large council seats, so there is no Citywide *council* row.)

## `district_precincts.csv` — versioned precinct → district composition

44 **`plan_2022`** rows read directly from `geo/precinct_to_district.csv` (roster_lib multi-year
`precinct_hi_source`; the retired `_precinct_to_district.csv` sidecar is no longer needed) + **38
`plan_pre2022`** rows now POPULATED from the reconstructed `geo/precinct_to_district_pre2022.csv`
(`precinct_id` filled, `confidence=medium`).
All 44 plan_2022 rows are `high` — the current post-2020-census map (per-district counts D1=7, D2=6,
D3=10, D4=7, D5=14; 0 splits, 0 conflicts). The 38 plan_pre2022 rows are the reconstructed pre-2022
(2012-cycle) composition (38/39 TAY precincts — TAY045 is a missing-geometry edge hole; `medium` —
current-vintage precinct shapes).

### Precinct-map cross-check (`--check` / demo (e))

Groups the by-precinct votes by the `district_precincts` (plan_2022) assignment and confirms the
precinct-sum winner matches the roster:

| Cycle | Seats | Plan | Result |
|---|---|---|---|
| 2023 | D1, D2, D3 | plan_2022 | **RECONCILES** (Burgess 64.7% def. Sanok, Cochran unopp., Barbieri unopp.) |
| 2025 | D4, D5 | plan_2022 | **RECONCILES** (Harker 56.0% def. Muñoz, Knudsen 56.7% def. Schulte) |
| 2007–2021 | all | plan_pre2022 | **GAP at the runtime election-crosscheck** — old cycles can't be graded against the *current* map; the plan_pre2022 *composition* is now reconstructed (`medium`) but this live check grades old cycles against plan_2022 (aggregate winner still matches the roster) |

**All five districts are now in the automated check** (`crosscheck_districts=("1","2","3","4","5")`,
LANDED 2026-07-11). D1 was previously excluded because the 2023 ballot spells the winner
**`ERNEST GLEN BURGESS`** while the roster uses the display name **`Ernest Glen Burgess`** — a
name-**format** mismatch the old exact-string comparator would false-flag. roster_lib's
`_winner_matches` now resolves BOTH the precinct-sum winner and the roster winner through `canon_key`
before comparing, so the middle-name difference no longer needs a per-city exclusion + hand-verification:
2023 D1 **RECONCILES** automatically (`ERNEST GLEN BURGESS`, 1,070, 64.7% def. Sanok = the seated
`Ernest Glen Burgess`). (The per-precinct GIS-vs-ballot mismatch detector is still dead here because
the precinct map is geometric, not ballot-year-scoped; only the aggregate district-winner check runs.
Known SLC/Millcreek/Ogden precinct-crosscheck limitation.)

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/taylorsville_results_by_candidate.csv`, municipal **general**
   winners only (2007+). Each winner maps to a seat via `seat_for_contest` (District N → `D-N`; Mayor
   → `MAYOR`). UPPER-CASE names normalized in `NAME_TO_KEY`; **no shared council surnames**, so no
   disambiguators. `elected_events` includes **`became-mayor`** so the two crossover Mayor wins
   (2013 Johnson, 2017 Overson) map. The forward cross-check confirms every general winner maps to a
   tenure — **0 drift**.
2. **Vote / attendance bounds** — `cities.db` `role` (`city='taylorsville'`, `body='Council'`): sets
   `first_vote`/`last_vote` for the seven district voters. **Mayor Overson is absent from cities.db**
   and MAYOR rows are emptied by `non_voting_mayor`.
3. **Minutes events** — swearing-in dates (2022-01-05, 2024-01-03, 2026-01-07), the redistricting
   resolution (2022-05-04), and the **2020 D3 resignation→appointment** (Christopherson last served
   2020-08-19; Ordinance 20-17 appoints Barbieri 2020-09-30), read from `meeting_minutes/minutes/**`
   and encoded in `TENURES`. **One in-window VACANT** (D3, high) + **one below-floor VACANT** (D2, low).
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (**1 row**: the D2 interim-VACANT note).

## Honest gaps (recorded, not filled)

- **Prior (`plan_pre2022`) geometry + precinct composition** — **RECONSTRUCTED 2026-07-11** to
  `medium` (was a blank/`low` GAP): `district_versions` now carries
  `geometry_ref=geo/council_districts_pre2022.geojson` and `district_precincts` has 38 populated
  `medium` rows (TAY045 is a missing-geometry edge hole → 38/39). APPROXIMATE — the pre-2022
  (2012-cycle) assignment dissolved over current-vintage precinct shapes. See
  `scripts/roster_boundary_recon.md`.
- **D2 2018–2020 interim holder** — Overson vacated D2 to become Mayor; the below-floor appointee is
  undocumented → a `low` VACANT with an honest override note, never a fabricated name.
- **Election-anchored pre-2020 terms (`medium`)** — win = fact, continuous service = inferred (below
  the 2020 data floor); no fake vote bounds invented.
- **Pre-2009 officeholders** — the county election record starts 2007 (council) / 2009 (mayor); no
  tenure is modeled before the earliest election that seats it.

## Where `roster_lib` fit Taylorsville cleanly (and the already-logged batch items it touches)

Taylorsville needed **no new library changes** — it is a clean reuse of the South-Jordan-style
pure-district + non-voting-mayor + redistricting + precinct path, exercising more of the library's
machinery (a real in-window VACANT chain, two crossovers, the override layer). Spots that hit the
**already-logged** fleet backlog (items 1-2 still worked around per-city, lib untouched; item 3,
the vote-bound clamp, has since LANDED in `roster_lib` — see below):

1. **`write_precincts()`/`precinct_crosscheck()` need a `source_year` column — LANDED 2026-07-11.**
   Taylorsville's `geo/precinct_to_district.csv` carries per-row years (2023/2025) for the ONE current
   map, and `int(float(votes))` had no blank guard. Formerly worked around with two DERIVED sidecars
   (a collapse-to-token `_precinct_to_district.csv` + a suppressed/blank-dropping `_precinct_votes.csv`).
   Both **RETIRED**: roster_lib now accepts a **multi-year `precinct_hi_source`** (`("2023","2025")` →
   both current-plan years earn `high` with no collapse) and applies an **in-library blank/suppressed
   vote guard**, so it reads `geo/precinct_to_district.csv` + `election_results/taylorsville_results_by_precinct.csv`
   directly (the "precinct-crosscheck cluster" + SLC "one hi source-year" backlog items).
2. **Exact-string winner comparison in the crosscheck — LANDED 2026-07-11.** The 2023 D1 SOVC name
   `ERNEST GLEN BURGESS` vs the roster display name would false-flag an exact-string compare; D1 was
   formerly excluded from the automated string-match and hand-verified. roster_lib's `_winner_matches`
   now resolves both names through `canon_key` (surname-token fallback), so **all five districts are in
   the automated check** and 2023 D1 reconciles automatically (the logged "compare via canon_key/surname,
   not exact string" batch item — Ogden's "RICHARD HYER" case).
3. **Person-level vote-bound smear onto pre-floor tenures — LANDED 2026-07-11.** The logged
   **vote-bound clamp** batch item shipped in `roster_lib` (`load_vote_dates()` +
   `clamp_vote_bounds()`): `first_vote`/`last_vote` are now clamped to each tenure's own
   `[start_date, end_date)` window, so a pre-floor term with no vote in its window reads BLANK
   (Burgess's 2012 D1 row is now blank, not `first_vote=2020-01-08`). No longer a per-city
   workaround — the library handles this class structurally.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2020-09-15 (mid D3 vacancy) (c) address→reps (d) redistricting (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a date** — `roster_as_of(date, body)`.
- **Address + date → representative** — `representatives_for_address(address, date)`: resolves a
  Taylorsville address via `geo/address_to_district.py` (Census geocode → point-in-polygon on
  `council_districts.geojson`) to **District 1–5**, returns that district's member on `date` **plus
  the citywide (non-voting) executive Mayor**. Honors `district_versions`: a **pre-2022-05-04 date now
  resolves against the reconstructed `plan_pre2022` map** (`medium`, approximate — see the recon
  note), which is exactly what demo (d) shows across the redistricting.
