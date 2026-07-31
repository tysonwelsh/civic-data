# roster/ — South Jordan rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each South Jordan City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who represents
this address on this date?* — none of which the flat CSVs can answer.

South Jordan is a **PURE-DISTRICT Council–Mayor city**: **5 geographic council districts** (D1..D5,
**NO at-large/citywide council seats**) + a **separately-elected Mayor who does NOT vote** on
council legislation (she presides — the single exception is one statutory tie-break). It is a
district city like SLC (`slc_city_council/roster/`) — pure districts + a non-voting mayor + a
2020-census redistricting + a precinct/address join — but SIMPLER (no vacancies, no seat-changers,
no at-large). Built on the shared `../../scripts/roster_lib.py`; the driver `build_roster.py`
carries only South Jordan's data.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation driver (SJ data + config). Regenerates the CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — **30 tenures across 6 stable seats** (0 VACANT). |
| `district_versions.csv` | Boundary interval table — **REAL 5 districts × 2 plans** (the 2022 redistricting) + a Mayor/citywide row (11 rows). |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped). 68 `plan_2022` rows (`high`) + **49 `plan_pre2022` reconstructed rows (`medium`)**. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. Currently **0 data rows**. |
| `_precinct_to_district.csv` | **DERIVED helper — KEPT** (regenerated each run) — `geo/precinct_to_district.csv` (68 SJD precincts → district 1–5, city-GIS-derived, 0 splits) + a constant `source_year` token. The shared `write_precincts()`/`precinct_crosscheck()` require a `source_year` column; SJ's canonical geo file doesn't carry one. **Stays because it is a genuine per-city derivation — SJ's geo file lacks the `source_year` column the shared writer needs** (NOT a simple wrapper). Per-city adapter only — the shared library is untouched. |
| `_precinct_votes.csv` | **RETIRED 2026-07-11 — `roster_lib` now skips blank/suppressed vote cells at read time (no sidecar needed).** The shared `precinct_crosscheck` now reads `election_results/south_jordan_results_by_precinct.csv` directly, honoring the `suppressed` column + guarding `int(float(votes))` against blank/non-numeric cells. |

**Never hand-edit the generated CSVs** — regenerate with `python3 roster/build_roster.py`. All
corrections go in `roster_overrides.csv`.

## Council structure & the stagger

**Council–Mayor form. 5 District seats (D1–D5) = 5 voting council members + a NON-VOTING Mayor.**
Every resident is represented by **2** elected officials: their District member and the citywide
Mayor.

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `MAYOR`, `D3`, `D5` | 2009 / 13 / 17 / 21 / 25 | Jan 2010 / 14 / 18 / 22 / 26 |
| **B** | `D1`, `D2`, `D4` | 2007 / 11 / 15 / 19 / 23 | Jan 2008 / 12 / 16 / 20 / 24 |

Documented seating dates in the loaded window: **2020-01-07** (first documented 2020 council
meeting, pmn_backfill), **2022-01-04** (oath, A-cycle), **2024-01-02** (oath, B-cycle), **2026-01-06**
(first documented 2026 meeting, A-cycle). Pre-2020-floor term-starts use `YYYY-01-01` (inferred from
the stagger, flagged medium).

**Counts: 30 tenures — 12 high / 18 medium / 0 low; 0 VACANT.** 0 overlapping tenures per seat. All
shared-library validators pass (overlap, sources/confidence, seat_id, the non-voting-mayor invariant,
the vacate-confidence invariant, the un-recovered-minutes gap detector).

## `council_terms.csv` schema
`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. **`seat_id`** — STABLE id (a redistricting redraws boundaries,
  it does NOT renumber seats): `D1..D5` + `MAYOR`.
- **`start_date`/`end_date`** — half-open `[start, end)`; `end_date` empty = currently serving;
  chained per seat (a tenure ends when the next on the same seat begins).
- **`first_vote`/`last_vote`** — earliest/latest observed Council-body vote from `cities.db` (`role`,
  `city='south_jordan'`, `body='Council'`), **clamped to each tenure's own half-open `[start_date,
  end_date)` window** (LANDED 2026-07-11 — `roster_lib.clamp_vote_bounds`, replacing the old
  person-level min/max). **Mayor rows are blank** (`non_voting_mayor=True`). A tenure whose window
  contains **no** observed vote shows **BLANK** first_vote/last_vote — e.g. the pre-floor Harris (2016
  D1), Johnson (2008 D2), Marlor (2016 D2) and Zander (2016 D4) holdover rows, whose holders' recorded
  votes fall in a LATER tenure. Consecutive re-elected terms now show **per-term** bounds (not the
  whole-career span). The authoritative service interval is always `start_date`/`end_date`; the clamp
  means the vote bounds no longer smear a person's later-term votes onto an earlier tenure.
- **`confidence`** — `high` = a documented Jan oath (2022-01-04 / 2024-01-02) or first-2026-meeting
  seating, OR a 2019-recovered-SOVC win seated Jan-2020 and corroborated by the 2020-08+ audited
  minutes + the named-vote record · `medium` = an **election-anchored term predating the 2020 data
  floor** (win = fact, continuous service inferred; incl. every pre-2018 start and the 2017-cycle
  terms whose Jan-2018 start is inferred though the tail is vote-corroborated) · `low` = unknown/
  not-acquired (none in `council_terms`; the `low` rows live in the district/precinct gap records).

## The current roster (as-of the 2026-01-06 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Patrick Harris | 2024-01-02 | 2023 (unopposed) | high |
| D2 | Kathie L. Johnson | 2024-01-02 | 2023 | high |
| D3 | Don Shelton | 2026-01-06 | 2025 (+45) | high |
| D4 | Tamara Zander | 2024-01-02 | 2023 (unopposed) | high |
| D5 | Jason McGuire | 2026-01-06 | 2025 | high |
| MAYOR | Dawn R. Ramsey | 2026-01-06 | 2025 (non-voting) | high |

## The distinctive surface (spot-checked against source minutes)

### The NON-VOTING Mayor + her single statutory tie-break (the headline case)
Mayor **Dawn R. Ramsey** presides and does **NOT** vote on council legislation. `non_voting_mayor=True`
empties every MAYOR-body `first_vote`/`last_vote`, and `dawnrramsey` is deliberately **excluded from
`DB_KEY`**. The ONE exception in the loaded window is a **statutory tie-break on 2025-06-17**
(Ordinance 2025-09, drinking-water-protection-zone uses): the four members present split **2-2**
(Shelton/Johnson **Yes**, Harris/McGuire **No**, Zander **absent**) and — verbatim from the minutes —
*"Mayor Dawn R. Ramsey - Yes"* ... *"The motion passed with a vote of 3-2."* This is her **ONLY**
council-body vote in `cities.db` (`dawnrramsey` Council `first_seen=last_seen=2025-06-17`). The flag
+ the DB_KEY exclusion ensure that lone tie-break **cannot** smear a misleading span across her five
Mayor tenures — every MAYOR row's vote bounds are empty (verified).

### The D2 Marlor → Johnson transition (a CLEAN end-of-term handoff, no vacancy)
Brad Marlor (elected D2 2015, re-elected 2019 as *"Bradley G. Marlor"*) served his **full term through
Dec-2023** — present + honored with a *"Proclamation in recognition of Bradley G. Marlor's Years of
Service"* on **2023-12-05** — and did **not** seek re-election. **Kathie L. Johnson** won D2 2023 and
was sworn on **2024-01-02** (*"Oath of Office of City Council Member, Kathie L. Johnson"*), her tenure
chaining to begin exactly when Marlor's ends (2024-01-02, no overlap). Marlor's `cities.db` last NAMED
vote is **2023-03-07** — a **dissent-only recording seam**, NOT an early departure. **Not a mid-term
resignation → no VACANT row.** (Johnson also held D2 in **2008–2011** before losing to Newton, then
returned in 2023 — SAME PERSON, so her 2023 `start_event` is `elected`, not `reelected`; her two D2
tenures are non-contiguous with Newton/Marlor between.)

### No mid-term vacancies anywhere
Every current district member's `cities.db` role runs continuously to 2026-05-19, and a targeted
minutes sweep for council-member resignations/appointments-to-fill found **none**. All six seats
transition only at cycle boundaries → **0 VACANT rows, honestly**.

## `district_versions.csv` — REAL 5 districts + the 2022 redistricting

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by, source_url,
confidence, note`. Geometry is not stored inline — `geometry_ref` points at
`geo/council_districts.geojson` (South Jordan's own city GIS "Council Districts 2020" layer).

**South Jordan DID redistrict** after the 2020 Census: **Ordinance 2022-13**, *"Amending Section
1.12.030: District Boundaries … set forth in the City Council District Boundary Map based on the 2020
census,"* adopted on a **UNANIMOUS 5-0** roll call (motion Marlor / second Harris) on **2022-06-07**.
Minutes 2022-06-07: the new lines *"are reflective of change and growth in our city over the last 10
years … drawn based on the current census information [the 2020 decennial census]."* First used for
the **2023** (B: D1/D2/D4) and **2025** (A: D3/D5) elections; the 2021 election used the prior lines.
*(South Jordan redistricts by **ordinance** — unlike SLC's/Sandy's resolution.)*

Versioning (11 rows):
- **`plan_2022`** (current) for D1–D5 — real geometry in `geo/council_districts.geojson`,
  `effective_start=2022-06-07`, open-ended, **high**.
- **`plan_pre2022`** (prior) for D1–D5 — RECONSTRUCTED 2026-07-11; **GEOMETRY confidence DOWNGRADED
  medium→`low` 2026-07-19**: `geometry_ref=geo/council_districts_pre2022.geojson` (all 49 SJD precincts,
  0 holes). VALIDATION 2026-07-19: fetched South Jordan's authoritative GIS ('FinalApproved'/'Council
  Districts 2020' — geometrically identical, both the CURRENT 2022 plan: they centroid-agree 100% with the
  current assignment but only 31% with the pre-2022 assignment); the city publishes NO true 2012 layer, and
  a fragmentation control (current dissolve = clean 1-piece districts vs this pre-2022 dissolve = up to
  7-piece fragments) proves the SJD precinct codes were renumbered (the millcreek defect) → geometry
  unreliable, `low`. The `district_precincts` precinct-CODE composition stays `medium` (a faithful SOVC
  record). In force through the 2021 elections. See `scripts/roster_boundary_recon.md`.
- **`citywide`** row for `MAYOR` — whole-city extent, unaffected by redistricting, open-ended, high.
  (SJ has **no** at-large council seats, so there is no Citywide *council* row.)

## `district_precincts.csv` — versioned precinct → district composition

68 **`plan_2022`** rows from `geo/precinct_to_district.csv` (via the `_precinct_to_district.csv`
sidecar) + **49 `plan_pre2022`** rows now POPULATED from the reconstructed
`geo/precinct_to_district_pre2022.csv` (`precinct_id` filled, `confidence=medium`).
All 68 plan_2022 rows are `high` — they derive from the **single authoritative** city GIS "Council
Districts 2020" layer (0 split precincts; per-district counts D1=14, D2=15, D3=12, D4=16, D5=11). The
49 plan_pre2022 rows are the reconstructed pre-2022 (2012-cycle) composition (49/49 SJD precincts,
`medium` — current-vintage precinct shapes).

### Precinct-map cross-check (`--check` / demo (e))

Groups the by-precinct votes by the `district_precincts` (plan_2022) assignment and confirms the
precinct-sum winner matches the roster:

| Cycle | Seats | Plan | Result |
|---|---|---|---|
| 2023 | D1, D2, D4 | plan_2022 | **RECONCILES** (Harris unopp., Johnson 61.7%, Zander unopp.) |
| 2025 | D3 | plan_2022 | **RECONCILES** (Shelton 50.7%, a +45 squeaker) |
| 2007–2021 | all | plan_pre2022 | **GAP at the runtime election-crosscheck** — old cycles can't be graded against the *current* map; the plan_pre2022 *composition* is now reconstructed (`medium`) but this live check grades old cycles against plan_2022 (aggregate winner still matches the roster) |

**D5 is deliberately excluded** from the automated string-match (`crosscheck_districts=("1","2","3","4")`)
because the 2025 ballot spells the winner **`JASON TIMOTHY MCGUIRE`** while the vote record / roster use
**`Jason McGuire`** — a name-format mismatch, **NOT** a data discrepancy (same pattern as SLC's D2/D6).
**Hand-verified to reconcile:** 2025 D5 precinct-sum leader `JASON TIMOTHY MCGUIRE` (1,335) is the seated
`Jason McGuire`. (The per-precinct GIS-vs-ballot mismatch detector is dead here because the precinct map
is geometric, not ballot-year-scoped — `precinct_hi_source` is a token, not a year; only the aggregate
district-winner check runs. This is the known SLC/Millcreek/Ogden precinct-crosscheck limitation.)

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/south_jordan_results_by_candidate.csv`, municipal **general**
   winners only (2007+). Each winner maps to a seat via `seat_for_contest` (District N → `D-N`; Mayor →
   `MAYOR`). UPPER-CASE names normalized in `NAME_TO_KEY`; **no shared council surnames** in SJ, so no
   disambiguators. The forward cross-check confirms every general winner maps to a tenure — **0 drift**
   (all 30 winners map cleanly; no expected-anomaly lines, unlike SLC's broken-SOVC/RCV cases).
2. **Vote / attendance bounds** — `cities.db` `role` (`city='south_jordan'`, `body='Council'`): sets
   `first_vote`/`last_vote`. **Mayor Ramsey is excluded from `DB_KEY`** and her MAYOR rows are emptied
   by `non_voting_mayor` — her one tie-break does not appear as a vote span.
3. **Minutes events** — oath dates (2022-01-04, 2024-01-02), the redistricting ordinance (2022-06-07),
   and the Marlor years-of-service proclamation (2023-12-05), read from `meeting_minutes/minutes/**` and
   encoded in `TENURES`. **No mid-term vacancies exist** → 0 VACANT.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (currently 0 rows).

## Honest gaps (recorded, not filled)

- **Prior (`plan_pre2022`) geometry + precinct composition** — **RECONSTRUCTED 2026-07-11** to
  `medium` (was a blank/`low` GAP): `district_versions` now carries
  `geometry_ref=geo/council_districts_pre2022.geojson` and `district_precincts` has 49 populated
  `medium` rows. APPROXIMATE — the pre-2022 (2012-cycle) assignment dissolved over current-vintage
  precinct shapes. See `scripts/roster_boundary_recon.md`.
- **Election-anchored pre-2020 terms (`medium`)** — win = fact, continuous service = inferred (below the
  2020 data floor); no fake vote bounds invented.
- **Audited-minutes floor 2020-08-18** — the Jan–Jul 2020 council meetings live only in `pmn_backfill/`
  (tally-only, `provenance=pmn_minutes` in `cities.db`), so the 2019-cycle Jan-2020 seatings are anchored
  to the recovered 2019 SOVC + the first documented 2020 meeting (2020-01-07); earliest audited present-
  list is 2020-08-18. Flagged `high` (election recovered + continuously documented), noted per row.
- **Pre-floor mayoral succession Money→Osborne (~2010–2013)** — the 2009 mayor was W. Kent Money, but the
  2013 general shows Alvord defeating **incumbent Scott L. Osborne**; an intervening pre-floor mayoral
  change is externally attested but its dates are entirely below the 2020 floor and unreconstructable from
  loaded sources → flagged in Money's note, **NOT** modeled as a fabricated Osborne tenure.

## Where `roster_lib` fit South Jordan cleanly (and the already-logged batch items it touched)

South Jordan needed **no new city-specific library changes** — it is a clean reuse of the SLC-style
pure-district + non-voting-mayor + redistricting + precinct path. Two spots exercised **already-logged**
fleet backlog items; one remains worked-around per-city, the other has since LANDED in the shared library:

1. **The precinct-crosscheck cluster — the blank/suppressed-vote guard LANDED 2026-07-11; the
   `source_year` adapter legitimately remains.** `precinct_crosscheck` used to do `int(float(votes))`
   with no blank guard, so SJ shipped a `_precinct_votes.csv` sidecar (suppressed/blank rows dropped).
   `roster_lib` now honors the `suppressed` column and guards blank/non-numeric vote cells **at read
   time**, so the cross-check reads `election_results/south_jordan_results_by_precinct.csv` directly and
   the `_precinct_votes.csv` sidecar is **RETIRED 2026-07-11**. The *other* half of the cluster stays
   worked-around: `write_precincts()`/`precinct_crosscheck()` still need a `source_year` column that SJ's
   canonical `geo/precinct_to_district.csv` doesn't carry, so the `_precinct_to_district.csv` sidecar
   (geo map + a constant `source_year` token) legitimately **remains** — it is a genuine per-city
   derivation, not a simple wrapper.
2. **Person-level vote-bound smear onto pre-floor / non-contiguous tenures — LANDED 2026-07-11.** The old
   person-level min/max made a pre-floor term inherit the holder's later documented-era bounds.
   `roster_lib.clamp_vote_bounds()` now clamps `first_vote`/`last_vote` to each tenure's own `[start_date,
   end_date)` window: the pre-floor Harris (2016 D1), Johnson (2008 D2), Marlor (2016 D2) and Zander (2016
   D4) rows now show **BLANK** bounds (no observed vote in-window — their votes fall in a later tenure),
   and consecutive re-elected terms show per-term bounds (e.g. Harris's 2020–2024 D1 row is now
   `2021-09-21..2023-05-16`, not the whole-career span). The tenure DATES were always correct; the clamp
   removes the informational smear at the source (no derived-layer hand-edit).

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2025-06-17 (tie-break day) (c) address→reps (d) redistricting (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a date** — `roster_as_of(date, body)`.
- **Address + date → representative** — `representatives_for_address(address, date)`: resolves a South
  Jordan address via `geo/address_to_district.py` (Census geocode → point-in-polygon on
  `council_districts.geojson`) to **District 1–5**, returns that district's member on `date` **plus the
  citywide (non-voting) Mayor**. Honors `district_versions`: a **pre-2022-06-07 date now resolves
  against the reconstructed `plan_pre2022` map** (`medium`, approximate — see the recon note), which is
  exactly what demo (d) shows across the redistricting.
