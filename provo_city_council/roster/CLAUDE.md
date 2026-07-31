# roster/ — Provo rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Provo Municipal Council + Mayor
seat over time** as dated intervals, reconciled from multiple sources with **per-row
provenance and confidence**. Answers: *who was on the council on date X?*, *who is serving
now?*, *who represents this address on this date?* — none of which the flat CSVs can answer.

Provo is the **DISTRICT-based validation city** for the Nephi at-large prototype
(`nephi_city_council/roster/`). It exercises the three things Nephi (all at-large) could
not: a **non-degenerate address → one-district → one-rep join**, a **real redistricting
event** versioned in `district_versions`, and a **precinct → district composition map** with
an election cross-check. **Schema and 4-layer model match Nephi exactly** — the two are meant
to converge on a shared builder.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script. Regenerates all three CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (20 tenures across 8 stable seats). |
| `district_versions.csv` | Boundary interval table — **REAL 5 districts, with the 2022 redistricting versioned into two plans**, + Citywide + Mayor rows. |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped; shares `plan_id`/dates with `district_versions`). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit the three generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — a **STABLE** id (a redistricting redraws boundaries, it does NOT renumber
  seats): `D1..D5` (geographic), `CW-I` / `CW-II` (the two at-large "Citywide" seats),
  `MAYOR`. Unlike Nephi's at-large `AL-A/B` cohorts, **each district seat's identity is
  source-attested** (district number = seat) — no within-cohort labelling ambiguity.
- **`district`** — FK into `district_versions`: `District 1`..`District 5` for D-seats,
  `Citywide` for `CW-I`/`CW-II`, `Citywide` for `MAYOR`.
- **`person_key`** = `first_last`, disambiguating shared surnames. Provo has **two Davids**
  who left together in 2021 — `david_harding` (D5) and `david_sewell` (CW-I): **different
  people, different seats, never merge** (mirrors Nephi's two Worwoods).
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained: a tenure ends when the next tenure on the same `seat_id` begins.
- **`start_event`** ∈ {elected, reelected, appointed, redistricted, became-mayor}.
  **`end_event`** ∈ {reelected, lost, did-not-run, resigned, became-mayor, serving,
  vacated/filled (VACANT rows), unknown}. `did-not-run` is used where a full-term member was
  **not a candidate** in the next cycle — the end *date* is precise; only retire-vs-decline
  is unstated. (Nephi used `unknown` for this; `did-not-run` is the more precise Provo label
  where the ballot proves non-candidacy.)
- **`election_year`** — the cycle that seated the tenure.
- **`first_vote` / `last_vote`** — the earliest/latest observed **Council-body** member vote in
  `cities.db` (the `vote→motion→meeting` join, `city='provo'`, `body='Council'`) **clamped to each
  tenure's own `[start_date, end_date)` window** (`roster_lib.clamp_vote_bounds`, landed 2026-07-11)
  — blank if the window holds no observed vote. Because the bounds are clamped per tenure, a multi-term
  holder shows each term's OWN span (e.g. George Handley's D2 `[2018-01-01, 2022-01-04)` row =
  2021-12-14, not a whole-career person-level max) — the authoritative interval is always
  `start_date`/`end_date`. Mayor rows are blank (Kaufusi/Judkins are not council voters).
- **`sources`** — semicolon list (`election:YYYY …`, `minutes:DATE …`, `votes:start..end`,
  `web:…`, `override:…`). **Every row has non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result or minutes-documented oath/departure/ordinance)
  · `medium` (a pre-floor 2017-cycle term, term-start inferred) · `low` (unknown — none here
  in `council_terms`; the `low` rows live in the district/precinct gap records).

### The 8 seats and their stagger

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `CW-I`, `D2`, `D5`, `MAYOR` | 2021 / 2025 | Jan-2022 / Jan-2026 |
| **B** | `CW-II`, `D1`, `D3`, `D4` | 2019 / 2023 | Jan-2020 / Jan-2024 |

The 2020–2021 Cycle-A holders were elected in **2017** (predates the 2019 election floor and
the 2020 minutes floor) → **confidence medium**, term-start inferred `2018-01-01`: Handley
(D2), Harding (D5), Sewell (CW-I), Kaufusi (Mayor). Everyone else anchors to an in-data
election win (`high`).

Counts: **20 tenures — 16 high / 4 medium / 0 low.** 0 overlapping tenures per seat.

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/provo_results_by_candidate.csv`, municipal **general**
   winners only. Each winner maps to a seat via `seat_for_contest` (District N → `D-N`;
   `Citywide I/II` → `CW-I/CW-II`; Mayor → `MAYOR`). UPPER-CASE names normalized. The script
   cross-checks that **every** general winner maps to a tenure (prints to stderr on drift).
2. **Vote / attendance bounds** — `cities.db` `role` (`city='provo'`, `body='Council'`): sets
   `first_vote`/`last_vote`. **Mayor Kaufusi is correctly ABSENT from this table** — she does
   not vote on council motions (verified: 0 rows in `all_votes.csv`'s member column). She sits
   as an 8th voter **only on the Board of Canvassers**, which is NOT council membership.
3. **Minutes events** — oath dates (`2020-01-07`, `2022-01-04`, `2024-01-09`, `2026-01-13`),
   the redistricting ordinance, and departure evidence, read from `meeting_minutes/minutes/**`
   and encoded in the `TENURES` table.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties.

Then `end_date` is chained per seat, the **VACANT-interval** rule runs (below), and the table
is validated (no overlaps; sources+confidence present). A failure aborts the write.

### VACANT-interval convention (the improvement over Nephi)

When a seat is vacated mid-term (resignation / became-mayor) **before** the successor is
seated, the predecessor's tenure ends at the *vacate date* and an explicit
`person_name=VACANT` interval is inserted until the successor's start — so **no two people
ever "hold" one seat and no gap is silently swallowed**. **Provo produced 0 VACANT rows**
(every successor is seated the same meeting the predecessor's term ends — no mid-term
resignations or council→mayor moves occurred in-window), but the code path is exercised and
validated, ready for cities that do have vacancies.

## The key transitions (spot-checked against source minutes + web)

- **Harding (D5) vs Sewell (CW-I) — pre-floor seat disambiguation.** Both Davids left
  together Dec-2021 (minutes 2021-12-14: *"Councilor David Harding and Chair David Sewell were
  presented with a gift for their service"*; Harding 6 yrs, Sewell 8 yrs & Council Chair). The
  roll call never prints districts, so the seat split is resolved externally: **Harding = D5**
  (his campaign *"Reelect Doctor Dave for District Five"*, votedrdave.blogspot.com) and
  **Sewell = Citywide I** (his own candidate pages say "Citywide"; the *other* citywide seat,
  CW-II, was Shipley's from 2019). Confirmed by succession: MacKay won CW-I 2021, Whipple won
  D5 2021.
- **Handley = D2 continuously.** Held D2 in 2020–21 (elected 2017) and was **re-elected to D2**
  in 2021 (unopposed) — so D2 was his seat throughout, not a citywide seat. Publicly said in
  2022 he would not run again (minutes 2022-03-29); not a 2025 candidate → Whitlock won D2.
- **Mayoral turnover.** Kaufusi (Mayor 2018–2026, two terms) **lost** the 2025 general to
  **Marsha Judkins** (8,703–8,280, ~422-vote upset). Judkins presides from 2026-01-13.

## `district_versions.csv` — REAL districts + the 2022 redistricting (the primary new test)

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Geometry is **not** stored inline — `geometry_ref` points at
`geo/precincts.geojson` (the Provo City GIS layer, which carries `COUNCIL_DISTRICT` per
precinct).

**Provo DID redistrict** after the 2020 Census: **Ordinance 2022-13 (agenda ref 22-003)**,
*"regarding redistricting adjustments to City Council District Maps"*, **adopted 2022-03-29**
on a **contested 4:3 map-selection vote** (Maps 33/34/113; Fillmore, Shipley, MacKay dissenting
on the losing options). Minutes make it effective **end-of-2022 for the 2023 elections**
(*"an at large council member for the duration of the next year"* until the new lines apply).

Versioning (12 rows):
- **`plan_2022`** (current) for D1–D5 — real geometry in `geo/precincts.geojson`,
  `effective_start=2023-01-01`, open-ended, **high**.
- **`plan_2012`** (prior) for D1–D5 — **explicit acquisition GAP**: `geometry_ref` **blank**,
  `confidence=low`, `note=historical boundaries not yet acquired`. The pre-2022 lines (used
  for 2019/2021) are not in `geo/`; the 2012 cycle used a different numeric precinct scheme
  (§2.01.050 codes 301/302…) that doesn't reconcile with current `25PR##` codes, and no
  precinct SOVC was published for the odd-year-B (D1/3/4) contests — so old geometry is **not
  reconstructable from data on disk** and is **not fabricated**.
- **`citywide`** rows for `Citywide` and `MAYOR` — whole-city extent, unaffected by
  redistricting, open-ended, high.

## `district_precincts.csv` — versioned precinct → district composition (secondary)

`city, plan_id, district_id, precinct_id, effective_start, effective_end, source, confidence,
note`. **Shares `plan_id` + effective dates with `district_versions`** (a redistricting
updates both).
- **`plan_2022`**: 67 precinct rows from `geo/precinct_to_district.csv`. `confidence=high` for
  **D2 & D5** (precinct lists cross-validated against 2025 municipal-general results),
  `medium` for **D1/D3/D4** (city GIS layer only — those odd-year-B districts have no
  precinct-level election data).
- **`plan_2012`**: 5 explicit GAP rows (one per district, `precinct_id` blank,
  `confidence=low`) — prior composition not acquired (same reasons as the geometry gap).

### Precinct-map cross-check (in `--check` / demo (e))

For each cycle+district with precinct-level data, the builder groups the precinct votes by the
`district_precincts` (plan_2022) assignment and confirms the winner matches the roster:

| Cycle | District | Plan | Result |
|---|---|---|---|
| 2025 | D2 | plan_2022 | **RECONCILES** — Whitlock 2035 (52.7%) > Petersen 1830; 0 precinct mismatches |
| 2025 | D5 | plan_2022 | **RECONCILES** — Whipple 964 (66.1%) > Blackburn 494; 0 precinct mismatches |
| 2021 | D2 | plan_2012 | **GAP** — old precinct numbering; composition not acquired |
| 2021 | D5 | plan_2012 | **GAP** — old precinct numbering; composition not acquired |

The precinct-sum winners equal the citywide-total winners exactly (no stray/missing
precincts). 2021 is honestly ungradeable through the current map (it belongs to `plan_2012`).

## How to query

```bash
python3 roster/build_roster.py --demo    # (a) current  (b) as-of  (c) address→rep  (d) redistricting  (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a date** — `roster_as_of(date, body)`: tenures with `start_date <= date < end_date`.
- **Address + date → representative** — `representatives_for_address(address, date)`: the
  **non-degenerate join Nephi could not test**. It resolves the address via
  `geo/address_to_district.py` (Census geocode → point-in-polygon → precinct →
  `precinct_to_district.csv`) to **District N**, then returns that district's rep on `date`
  **plus both Citywide members and the Mayor** (who represent everyone). It honors
  `district_versions`: for a date under `plan_2012` the geographic step is an **honest GAP**
  (returns citywide + mayor only — never a fabricated district), which is exactly what
  demo (d) shows across the 2022 redistricting.

## Honest gaps (recorded, not filled)

- **Prior (`plan_2012`) district geometry** — not in `geo/`; recorded as `low`/blank rows in
  both `district_versions` and `district_precincts`. Not reconstructable from disk.
- **2019 & 2023 precinct-level elections** — county published citywide-only SOVC (PDF) those
  years, so D1/D3/D4 have no precinct election corroboration (their `plan_2022` rows are
  `medium`, city-GIS-sourced) and the 2021-era cross-check can't be graded.
- **Pre-floor 2017-cycle terms (`medium`)** — Handley/Harding/Sewell/Kaufusi were seated at
  the 2020 floor; their 2017 election / 2018 term-start is inferred from the Cycle-A stagger.
- **No unidentified appointee** — every Provo council member in-window maps to a named
  election winner; no mid-term vacancy occurred, so there are **no** `low`/UNKNOWN rows in
  `council_terms` and **0 VACANT** intervals (both honestly, not by omission).

## Federation & generalization (NOT implemented — do not touch the shared `cities.db` build)

To federate later: add a **`term`** table = `council_terms` unioned across cities, a
**`district_version`** table = `district_versions` unioned, and a **`district_precinct`**
table = `district_precincts` unioned; plus views `v_council_current` (end_date IS NULL AND
end_event='serving') and `v_council_asof(:date)` mirroring `roster_as_of`. Join
`term.person_key` to the existing `person`/`vote` tables via the per-city `DB_KEY` map.

**What Provo validated that Nephi could not:** the non-degenerate
address→one-district→one-rep join through real precinct geometry; a **real redistricting**
versioned as two `plan_id`s with a closed `effective_end` (the `start_event=redistricted`
semantics), including the honest old-geometry gap; a **precinct→district composition map** with
an election reconciliation; and **source-attested seat identity** (district = seat), removing
Nephi's within-cohort labelling ambiguity. **Both cities** share the harder-to-see half —
multi-source tenure reconciliation with honest provenance/confidence, shared-surname
disambiguation (two Davids ≈ two Worwoods), pre-floor inference, and the VACANT-interval rule.
With Provo's DISTRICT surface and Nephi's AT-LARGE surface both green, the schema is ready to
generalize to the remaining 14 cities. **Still unvalidated:** a city that actually produces a
mid-term VACANT interval or a council→mayor move (Provo had neither); a redistricting where
**both** boundary versions are on disk (Provo's old geometry is a gap); and term-limit regimes.
