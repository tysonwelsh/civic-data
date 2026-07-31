# roster/ — Sandy rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Sandy City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance
and confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who
represents this address on this date?* — none of which the flat CSVs can answer.

Sandy is a **MIXED district + at-large city with a NON-VOTING (strong-mayor) mayor** — the
SAME structure as Ogden (real 4 districts + 3 at-large + non-voting strong-mayor + a
post-2020-census redistricting + a precinct/address join), but with a **richer set of
transitions** (a mayoral crossover that is a MID-TERM VACANCY, two at-large→district
within-council moves, and two returning members). Built on the shared `scripts/roster_lib.py`;
the driver `build_roster.py` carries only Sandy's data.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script. Regenerates the CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct + at-large cross-checks. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**22 tenures across 8 stable seats**, incl. 1 VACANT). |
| `district_versions.csv` | Boundary interval table — **REAL 4 districts, with the 2022 redistricting versioned into two plans**, + At-Large + Mayor rows (10 rows). |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped; 110 plan_2022 rows (`high`) + **76 plan_pre2022 reconstructed rows (`medium`)**). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently **0 data rows**. |
| `_precinct_to_district.csv` | **DERIVED helper — KEPT** (regenerated each run) — a **point-in-polygon** of `geo/precincts.geojson` against `geo/council_districts.geojson`. Sandy has **no county precinct→district table on disk** (unlike Ogden's `geo/precinct_to_district.csv`), so the roster derives the plan_2022 composition itself. **Stays because it is a genuine per-city derivation — a real point-in-polygon geo derivation, with no canonical county precinct→district map to wrap** (NOT a simple wrapper). Needs geopandas; if absent, an existing map is reused. |
| `_precinct_votes.csv` | **RETIRED 2026-07-11 — `roster_lib` now skips blank/suppressed vote cells at read time (no sidecar needed).** The shared `precinct_crosscheck` now reads `election_results/sandy_results_by_precinct.csv` directly, honoring the voter-privacy `suppressed` column + guarding `int(float(votes))` against blank/non-numeric cells. |

**Never hand-edit the generated CSVs** — regenerate with `python3 roster/build_roster.py`. All
corrections go in `roster_overrides.csv`.

## Council structure & the stagger

**Council–Mayor (strong-mayor) form. 4 District seats (D1–D4) + 3 At-Large seats (A/B/C) = 7
voting council members. The Mayor does NOT vote on council legislation** (the council elects its
own Chair). Every resident is represented by 5 elected officials: their District member, all 3
At-Large members, and the Mayor.

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `AL-A`, `AL-B`, `D2`, `D4` | 2019 / 2023 (at-large **Vote-for-2**) | Jan-2020 / Jan-2024 |
| **B** | `MAYOR`, `AL-C`, `D1`, `D3` | 2021 / 2025 (at-large **Vote-for-1**) | Jan-2022 / Jan-2026 |

**A-cycle 2019 winners are IN the election data** (elections floor = 2019) → `high`. **B-cycle
2020–2021 holders were elected in 2017** (predates the 2019 election floor + the 2020 minutes
floor) → **confidence medium**, term-start inferred `2018-01-01`: Christensen (D1), Coleman-Nicholl
(D3), Robinson (AL-C), Bradburn (MAYOR). Everyone else anchors to an in-data election win + a
minutes oath.

**The 3 at-large seats are NOT individually labelled on the ballot** (the at-large contests are
multi-winner). We assign STABLE ids by cohort + continuity: **AL-A** = the seat Sharkey holds
continuously (A-cycle); **AL-B** = the other A-cycle at-large seat (Houseman → DeKeyzer); **AL-C**
= the B-cycle Vote-for-1 at-large seat (Robinson → D'Sousa).

Oath / term-start dates (verified from `meeting_minutes/minutes/**`, matching `cities.db`
`role.first_seen`): **2020-01-07 · 2022-01-03 · 2024-01-09 · 2026-01-06**. Scott Earl's D4
appointment: **2022-01-18** (first recorded vote 2022-01-25 — the named-roll-call recording seam).

Counts: **22 tenures — 18 high / 4 medium / 0 low. 0 overlapping tenures per seat. 1 VACANT
interval** (the D4 gap between Zoltanski's mayoral swearing and Earl's appointment).

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. (Sandy's RDA is not modeled here — it acts inside/around
  council meetings; the vote layer carries the one open RDA vote.)
- **`seat_id`** — a **STABLE** id (a redistricting redraws boundaries, it does NOT renumber
  seats): `D1..D4`, `AL-A`/`AL-B`/`AL-C`, `MAYOR`.
- **`person_key`** = `first_last`. Sandy has **no shared council surnames in-window** (the two
  Brookes are `brooke_christensen` (D1) and `brooke_dsousa` (AL-C) — distinct surnames). Kris
  Nicholl and Kristin Coleman-Nicholl are the **same person** → one key `kristin_coleman_nicholl`
  (the D3 2026 display name is `Kris Nicholl`, matching the ballot + the 2026 masthead).
- **`start_date`/`end_date`** — half-open `[start, end)`. `end_date` empty = currently serving.
  Chained: a tenure ends when the next tenure on the same `seat_id` begins.
- **`first_vote`/`last_vote`** — earliest/latest observed Council-body vote from `cities.db`
  (`role`, `city='sandy'`, `body='Council'`), **clamped to each tenure's own half-open `[start_date,
  end_date)` window** (LANDED 2026-07-11 — `roster_lib.clamp_vote_bounds`, replacing the old
  person-level min/max). **Mayor rows are blank** (`non_voting_mayor=True`). A member with
  **non-contiguous or seat-changing** tenures now shows **per-tenure** bounds, not one shared
  person-level span (see "vote-bound clamp" below); a window with no observed vote shows BLANK. The
  authoritative service interval is always `start_date`/`end_date`.
- **`confidence`** — `high` (in-data election win or minutes-documented oath/appointment/departure/
  redistricting resolution) · `medium` (a pre-floor 2017-cycle B-seat/mayor term, term-start
  inferred) · `low` (none in `council_terms`; the `low` rows live in the district/precinct gap
  records).

## The key transitions (spot-checked against source minutes)

### Zoltanski — the D4-councilmember → Mayor CROSSOVER, a **MID-TERM VACANCY** (the headline case)
- **D4 councilmember 2020–2021, a VOTING member** (`minutes:2020-01-07` masthead "Monica
  Zoltanski, District 4"; elected 2019 def. Brooke D'Sousa 50.67–49.33). Her last recorded (named)
  D4 vote is **2021-12-07** (she last served 2021-12-14 — a unanimous voice vote with no named members).
- **WON the 2021 MAYOR race** (RCV final 8620–8599 over Jim Bennett) and was **sworn Mayor
  2022-01-03** (`minutes:2022-01-04` "Mayor Monica Zoltanski" presiding; "swearing in ceremony
  yesterday"). **This is MID-TERM**: her 2019 D4 term ran to Jan-2024, and D4 is an **A-cycle** seat
  **not on the 2021 ballot**, so it was **NOT filled by a regular election** — it went **VACANT and
  was filled by APPOINTMENT** (Scott Earl). **This is UNLIKE Ogden's Nadolski** (a clean
  cycle-boundary handoff): here the library inserts an explicit **VACANT interval 2022-01-03 →
  2022-01-18**. D4 ends 2022-01-03; MAYOR begins 2022-01-03 — half-open, **no overlap**.
- Her **MAYOR rows have EMPTY vote bounds** (`non_voting_mayor=True`). Without the flag her
  2020–2021 D4 span — **and** three Board-of-Municipal-Canvassers canvass actions she took *as
  Mayor* (2023-12-06, 2025-08-26, 2025-11-18, listed under `body=Council` in the minutes) — would
  smear onto the mayoralty.

### The D4 VACANT interval + Scott Earl's appointment
- `minutes:2022-01-18` — the Council **interviewed 5 applicants** for the District 4 vacancy and
  chose Scott Earl on a **verbal vote 5–1 over Pat Casaday** (Mecham voted for Casaday), then moved
  to appoint him (Resolution 22-03). His `cities.db` first_vote is **2022-01-25** (the recording
  seam). This is a **documented** vacancy (both bounding meetings on disk; no `minutes_unrecovered`
  date in the window), so the VACANT row is **high** (not gap-bounded).
- Earl **ran for D4 in the 2023 regular election and LOST** to Marci Houseman (48.69–51.31) → his
  term ended at the 2024-01-09 cycle boundary (`end_event=lost`).

### The prior Mayor — Kurt Bradburn
- **Mayor 2020–2021** (`minutes:2020-01-07` "Administration: Mayor Kurt Bradburn" presiding — a
  continuing 2017-cycle mayor; term-start 2018-01 inferred → `medium`). **Non-voting** (0 `cities.db`
  council rows). **Did NOT run in 2021** (the field was Zoltanski/Bennett/Nicholl/… with no Bradburn)
  → replaced by Mayor Zoltanski 2022-01-03.

### Two AT-LARGE → DISTRICT within-council moves
- **Zach Robinson**: At-Large (AL-C) 2020–2021, then **won District 3 in 2021** (RCV 3557–2402) and
  moved to D3 for 2022 → his old at-large seat was won by Brooke D'Sousa.
- **Marci Houseman**: At-Large (AL-B) 2020–2023, then **won District 4 in 2023** (51.31–48.69) and
  moved to D4 for 2024 → her old at-large seat was won by Aaron DeKeyzer.

### Two RETURNING members (non-contiguous tenures on the same seat)
- **Brooke Christensen (D1)** and **Kristin "Kris" Coleman-Nicholl (D3)** each held her district
  **2018–2021**, then **gave it up to run for MAYOR in 2021** (both lost — Christensen 4th,
  Coleman-Nicholl 3rd, RCV), then **won her old district back in 2025**. The `minutes:2026-01-06`
  call them **"new and returning Council Members"**. Their D1/D3 tenures are non-contiguous (Mecham /
  Robinson held the seat in between); chaining handles it with no overlap and no VACANT.

## `district_versions.csv` — the 2022 redistricting

Sandy **DID redistrict** after the 2020 Census: **Resolution 22-24C**, *"amending the Sandy City
Council District Boundaries, updating the Sandy City Council Districts map, and selecting
Alternative Map 4-1b"*, **adopted 2022-05-03 on a UNANIMOUS 7-0 roll call** (motion Scott Earl /
second Brooke D'Sousa). Preceded by two 2022-03-01 direction motions (m2 5–2 keep 4 districts; m3
6–1 staff to bring back the current map + 3 alternatives within the population deviation). **In
force for the 2023 & 2025 elections**; the 2021 election used the prior lines. (Note: Sandy adopted
this via a **Resolution**, not an ordinance — captured verbatim.)

Versioning (10 rows):
- **`plan_2022`** (current) for D1–D4 — real geometry (`geo/council_districts.geojson`, the Sandy
  city GIS district polygons; matches the 2026 minutes), `effective_start=2022-05-03`, open-ended,
  **high**.
- **`plan_pre2022`** (prior) for D1–D4 — RECONSTRUCTED 2026-07-11; **GEOMETRY confidence DOWNGRADED
  medium→`low` 2026-07-19**: `geometry_ref=geo/council_districts_pre2022.geojson` (all 76 SAN precincts;
  SAN024 conflict→D3). VALIDATION 2026-07-19: fetched Sandy's authoritative GIS
  (gis.sandy.utah.gov City_Council_Districts) — it is the CURRENT 2022 plan (current members; 100%
  centroid-agree with the current assignment, only 28% with pre-2022); Sandy publishes NO pre-2022 layer,
  and a fragmentation control (current dissolve = clean 1–2-piece districts vs this pre-2022 dissolve =
  **8–13-piece fragments**) proves SEVERE SAN precinct-code renumbering (the millcreek defect) → geometry
  unreliable, `low`. The `district_precincts` precinct-CODE composition stays `medium` (a faithful SOVC
  record). In force for the 2019/2021 elections. See `scripts/roster_boundary_recon.md`.
- **`At-Large`** + **`Citywide`** (Mayor) rows — whole-city extent, unaffected by redistricting.

## `district_precincts.csv` — precinct → district composition

- **`plan_2022`**: **110 precinct rows** derived by **point-in-polygon** (`_precinct_to_district.csv`
  = each `geo/precincts.geojson` precinct's representative point → the `geo/council_districts.geojson`
  district that contains it; all 110 SAN precincts assign cleanly, 0 unassigned). All `high`
  (source_year 2025 = current layer). Distribution: D1 25 · D2 30 · D3 31 · D4 24.
- **`plan_pre2022`**: **76 rows now POPULATED** from the reconstructed
  `geo/precinct_to_district_pre2022.csv` (`precinct_id` filled, `confidence=medium`) — the pre-2022
  (2012-cycle) composition (76/76 SAN precincts; SAN024 conflict resolved to the 2021 D3 assignment;
  `medium` — current-vintage precinct shapes).

### Precinct cross-check (`--check` / demo (f))

Groups the by-precinct votes by district contest and confirms the precinct-sum winner matches the
roster. Sandy's precinct codes are `SAN###` in **both** the election file and `precincts.geojson`
(**no county-vs-city prefix mismatch** — unlike Ogden), so the check runs cleanly. All four
**plan_2022** district contests **reconcile on the winning individual** — and, unlike Ogden, with
**no middle-initial false-DISCREPANCY** (the roster display names match the ballots):

| Cycle | Seat | Plan | Precinct-sum winner | Roster winner | Status |
|---|---|---|---|---|---|
| 2023 | D2 | plan_2022 | Alison Stroud (unopposed) | Alison Stroud | **RECONCILES** |
| 2023 | D4 | plan_2022 | Marci Houseman (51.3%) | Marci Houseman | **RECONCILES** |
| 2025 | D1 | plan_2022 | Brooke Christensen (53.9%) | Brooke Christensen | **RECONCILES** |
| 2025 | D3 | plan_2022 | Kris Nicholl (56.8%) | Kris Nicholl | **RECONCILES** |

The **2019/2021** district contests are reported as **GAP at the runtime election-crosscheck** — old
cycles can't be graded against the *current* map; the plan_pre2022 *composition* is now reconstructed
(`medium`) but this live check grades old cycles against plan_2022. The aggregate precinct-sum winner
still matches the roster there.

**At-large cohort cross-check** (`--check` / demo (g)) — a **driver-level** check, because the
library's per-contest forward cross-check cannot resolve Sandy's multi-winner at-large seats (see
"Where roster_lib didn't fit"). All 6 at-large general winners (2019 Sharkey+Houseman, 2021 D'Sousa,
2023 Sharkey+DeKeyzer, 2025 D'Sousa) map to an at-large tenure elected/reelected that year → **OK**.

## Honest gaps (recorded, not filled)

- **Prior (`plan_pre2022`) district geometry & precinct composition** — **RECONSTRUCTED 2026-07-11**
  to `medium` (was a blank/`low` GAP, and the old note wrongly said "not reconstructable"):
  `district_versions` now carries `geometry_ref=geo/council_districts_pre2022.geojson` and
  `district_precincts` has 76 populated `medium` rows (SAN024 conflict resolved to the 2021 D3
  assignment). APPROXIMATE — the pre-2022 (2012-cycle) assignment dissolved over current-vintage
  precinct shapes. See `scripts/roster_boundary_recon.md`.
- **No per-precinct plan_pre2022 cross-check at the runtime election-grader** — the 2019/2021 district
  contests still can't be graded against the *current* plan_2022 composition (only the aggregate winner
  is confirmed); the plan_pre2022 composition table itself is now reconstructed.
- **Pre-floor 2017-cycle B-seat/mayor terms (`medium`)** — Christensen (D1), Coleman-Nicholl (D3),
  Robinson (AL-C), Bradburn (MAYOR) were seated at the 2020 floor; their 2017 election / 2018
  term-start is inferred from the B-cycle stagger (only the START date is inferred; their 2020–2021
  membership is documented in the mastheads + votes).
- **1 VACANT** (D4, 2022-01-03 → 2022-01-18) — a real, documented mid-term vacancy. **0 UNKNOWN.**

## `cities.db` vote-bound clamp (LANDED 2026-07-11)

`first_vote`/`last_vote` are the earliest/latest observed Council-body vote from `cities.db`, **clamped
to each tenure's own `[start_date, end_date)` window** (`roster_lib.clamp_vote_bounds`, landed
2026-07-11), replacing the old person-level min/max. Before the clamp, several rows carried a
person-level **smear** that did not affect any tenure date (which come from elections + oath/appointment
minutes); the clamp removes each at the source:

1. **Zoltanski D4 `last_vote`** — the old person-level max had smeared it to **2025-11-18** via three
   Board-of-Municipal-Canvassers actions she took *as Mayor* (2023-12-06, 2025-08-26, 2025-11-18, listed
   under `body=Council`). Now clamped to her D4 window → **2021-12-07** (her true D4 service ended
   2021-12-14).
2. **Returning members Christensen (D1) & Coleman-Nicholl (D3)** — the old person-level span
   `2020-01-07..2026-06-02` smeared across the 2022–2025 off-council gap. Now each stint shows its own
   bounds: first stint `2020-01-07..2021-12-07`, the 2026 return `2026-01-06..2026-06-02`.
3. **Seat-changers Robinson (AL-C→D3) & Houseman (AL-B→D4)** — the continuous person-level span was
   shared by both the at-large and district rows. Now each seat shows its own tenure bounds: Robinson's
   D3 row `first_vote=2022-01-04` (not his 2020-01-07 at-large start, which stays on the AL-C row);
   Houseman's D4 row `2024-01-09..2026-06-02` vs her AL-B row `2020-01-07..2023-12-19`.

The `non_voting_mayor` flag still empties every MAYOR row independently. The authoritative service
interval is always `start_date`/`end_date`.

## Where `roster_lib` didn't fit Sandy cleanly (for the hardening backlog)

1. **The forward election cross-check can't resolve multi-winner at-large seats.** Sandy's 3
   at-large seats are **not individually labelled on the ballot** (Vote-for-2 in 2019/2023,
   Vote-for-1 in 2021/2025), so `contest_key(office, district)` cannot map an at-large winner to a
   specific AL seat. The lib's `election_crosscheck` therefore prints **expected informational
   `unmapped contest … Council At-Large`** lines (6 of them) on every build. **Worked around** with a
   **driver-level cohort cross-check** (`_atlarge_crosscheck`, `--check`/demo (g)) that validates the
   at-large winners by cohort→person; the roster data was NOT distorted. A lib enhancement would let
   `contest_key` (or a new hook) map a candidate — not just a contest — to a seat.
2. **No county precinct→district table on disk** (Sandy's `geo/` is district-polygon-authoritative
   and has no `precinct_to_district.csv`, unlike Ogden). **Worked around** with a derived
   **point-in-polygon** sidecar `_precinct_to_district.csv` (geopandas, generated by the driver). A
   lib helper to build this from a precinct + district geojson pair would remove the per-city code.
3. **`precinct_crosscheck` did `int(float(votes))` with no blank guard — LANDED 2026-07-11.**
   Sandy's by-precinct file can carry voter-privacy **suppressed** rows (blank votes), so Sandy used to
   ship a `_precinct_votes.csv` sidecar (suppressed/blank rows dropped). `roster_lib` now honors the
   `suppressed` column and guards blank/non-numeric vote cells **at read time**, so the cross-check reads
   `election_results/sandy_results_by_precinct.csv` directly and the `_precinct_votes.csv` sidecar is
   **RETIRED 2026-07-11**. (The point-in-polygon `_precinct_to_district.csv` sidecar in item 2 legitimately
   remains — it is a genuine per-city geo derivation, not a simple wrapper.)
4. **Single `precinct_hi_source` gates the per-precinct mismatch detector to one year (2025)** — the
   known SLC/Millcreek/Ogden limitation. For Sandy the detector runs on 2025 and surfaces exactly one
   benign seam: **`SAN907`** (a **0-vote placeholder/countywide precinct** listed in the 2025 D3
   contest whose representative point falls in D1). It has **0 votes**, so it affects no winner —
   documented, not a data error.

## How to query

```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of-2022 (c) D4 VACANT window
                                         # (d) address→reps (e) redistricting gap (f) precinct (g) at-large
python3 roster/build_roster.py --check   # validations + precinct + at-large cross-checks
```
- **Address + date → representatives** — `representatives_for_address(address, date)` resolves the
  address via `geo/address_to_district.py` to **District 1–4**, then returns that district's member
  on `date` **plus all 3 At-Large members and the Mayor**. It honors `district_versions`: a
  pre-2022-05-03 date now **resolves against the reconstructed `plan_pre2022` map** (`medium`,
  approximate — see the recon note), never a fabricated district.
