# roster/ — Ogden rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Ogden City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance
and confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who
represents this address on this date?* — none of which the flat CSVs can answer.

Ogden is a **MIXED district + at-large city with a NON-VOTING (strong-mayor) mayor** — it
combines the Provo template (real districts + at-large + non-voting mayor + a post-2020-census
redistricting + a precinct/address join) with the **Logan/Millcreek council-chair → mayor
CROSSOVER**: **Ben Nadolski was the VOTING District-4 council chair 2020-2023, then Mayor from
2024-01-02.** Built on the shared `scripts/roster_lib.py`; the driver `build_roster.py` carries
only Ogden's data.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script. Regenerates the CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**20 tenures across 8 stable seats**). |
| `district_versions.csv` | Boundary interval table — **REAL 4 districts, with the 2022 redistricting versioned into two plans**, + At-Large + Mayor rows. |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped; shares `plan_id`/dates with `district_versions`). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently **0 data rows**. |
| `_precinct_votes.csv` | **RETIRED 2026-07-11** — roster_lib reads the canonical geo/election files directly (multi-year `precinct_hi_source` + blank/suppressed guard). `precincts_byprecinct_path` now points straight at `election_results/ogden_results_by_precinct.csv`; the hardened `precinct_crosscheck` has a built-in blank/suppressed/non-numeric guard that skips Ogden's 2 voter-privacy-suppressed cells (reported as `skipped 2 blank/non-numeric vote cell(s)`), changing no precinct-sum winner. |

**Never hand-edit the generated CSVs** — regenerate with `python3 roster/build_roster.py`. All
corrections go in `roster_overrides.csv`.

## Council structure & the stagger

**Council–Mayor (strong-mayor) form. 4 District seats (D1–D4) + 3 At-Large seats (A/B/C) = 7
voting council members. The Mayor does NOT vote on council legislation.** Every resident is
represented by 5 elected officials: their District member, all 3 At-Large members, and the Mayor.

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **A** | `MAYOR`, `AL-C`, `D2`, `D4` | 2019 / 2023 | Jan-2020 / Jan-2024 |
| **B** | `AL-A`, `AL-B`, `D1`, `D3` | 2021 / 2025 | Jan-2022 / Jan-2026 |

**A-cycle 2019 winners are IN the election data** (elections floor = 2019) → `high`. **B-cycle
2020–2021 holders were elected in 2017** (predates the 2019 election floor + the 2020 minutes
floor) → **confidence medium**, term-start inferred `2018-01-01`: Choberka (D1), Stephens (D3),
White (AL-A), Blair (AL-B). Everyone else anchors to an in-data election win + a minutes oath.

Oath / term-start dates (verified from `meeting_minutes/minutes/**`, matching `cities.db`
`role.first_seen`): **2020-01-07 · 2022-01-04 · 2024-01-02 · 2026-01-06** (Flor Lopez sworn
2026-01-20 — see D1).

Counts: **20 tenures — 16 high / 4 medium / 0 low. 0 overlapping tenures per seat. 0 VACANT
intervals** (honestly — no mid-term resignation/appointment occurred in-window).

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. (RDA/MBA are the SAME people wearing a board hat — NOT
  modeled here; the vote layer carries those tenures.)
- **`seat_id`** — a **STABLE** id (a redistricting redraws boundaries, it does NOT renumber
  seats): `D1..D4`, `AL-A`/`AL-B`/`AL-C`, `MAYOR`. At-large seats are labelled by the county's
  own "At-Large Seat A/B/C" contest names, so there is no within-cohort ambiguity.
- **`person_key`** = `first_last`, disambiguating shared surnames. Ogden has **two Lopez** —
  `luis_lopez` (At-Large C, ≤2023) and `flor_lopez` (D1, 2025+): **different people, different
  seats, never merge** (resolved by first name in `DISAMBIGUATORS`).
- **`start_date`/`end_date`** — half-open `[start, end)`. `end_date` empty = currently serving.
  Chained: a tenure ends when the next tenure on the same `seat_id` begins.
- **`first_vote`/`last_vote`** — the earliest/latest observed Council vote from `cities.db`
  (`city='ogden'`, `body='Council'`) that falls **within each tenure's own `[start, end)` window**
  (the tenure-window clamp, landed 2026-07-11 — blank if the window holds no observed vote).
  **Mayor rows are blank** (`non_voting_mayor=True` — Caldwell/Nadolski cast no council votes as
  Mayor).
- **`confidence`** — `high` (in-data election win or minutes-documented oath/departure/ordinance)
  · `medium` (a pre-floor 2017-cycle B-seat term, term-start inferred) · `low` (none in
  `council_terms`; the `low` rows live in the district/precinct gap records).

## The key transitions (spot-checked against source minutes)

### Nadolski — the council-chair → mayor CROSSOVER (the headline case)
- **D4 councilmember + Chair 2020-2023, a VOTING member.** `minutes:2020-01-07` shows "Chair
  Ben Nadolski" sworn (re-elected D4 2019, unopposed); his council votes run **2020-01-07 →
  2023-12-19** in `cities.db` (382 votes). His D4 row carries those bounds.
- **Won the 2023 MAYOR race** (def. Taylor Knuth 54.36–45.64) and was **sworn as Mayor
  2024-01-02** (`minutes:2024-01-02` "newly elected Mayor Benjamin K. Nadolski"). His D4 term
  expired at the regular cycle boundary the SAME day — a **clean term-end handoff, not a
  mid-term vacancy** (the 2023 election filled D4 with Dave Graf). **D4 ends 2024-01-02; MAYOR
  begins 2024-01-02 — half-open, no overlap.**
- His **MAYOR row has EMPTY vote bounds**: `non_voting_mayor=True` empties them (and the
  tenure-window clamp would independently leave them blank — no council vote falls within the
  mayoral window; exactly the Logan/Anderson + Millcreek/Jackson pattern). Verified:
  `first_vote`/`last_vote` blank on both Mayor rows; his D4 row is clamped to
  2020-01-07..2023-12-19.

### Caldwell → Nadolski — the mayoral chain
- **Michael P. Caldwell**: Mayor 2020-2023 (his third term; the 2019 win *is* in-data → `high`,
  no pre-floor inference). `minutes:2020-01-07` "Oath of Office for newly elected Mayor Michael
  P. Caldwell." **Non-voting** (0 `cities.db` council rows — never in a roll call). **Did not
  run in 2023** (race was Nadolski vs Knuth) → term ended 2024-01-02, replaced by Nadolski.

### A district-seat transition — D4 Nadolski → Graf (2023)
- Dave Graf **elected D4 2023** (def. Steven Van Wagoner 52.68–47.32), sworn 2024-01-02. His
  `first_vote` is 2024-02-06 — the **named-roll-call seam** (a recording lag, not the term start).

### The 2026 B-cycle turnover (three incumbents out)
- **AL-A**: White (incumbent) **LOST** to Alicia Washington 2025 → Washington seated 2026-01-06.
- **AL-B**: Blair (incumbent) **LOST** to Kevin Lundell 2025 → Lundell seated 2026-01-06; Blair
  addressed as "Former Council Member Blair" at `minutes:2026-01-06`.
- **D1**: Choberka **did not run** 2025 → Flor Lopez won. Choberka's last ATTENDED meeting was
  2026-01-06 ("her last meeting … after eight years"); Flor Lopez was **"unavailable to be sworn
  in until the second week of January"** and first votes 2026-01-20. Choberka held the seat as a
  **holdover** until Lopez qualified, so **D1 chains 2026-01-20 with NO vacancy** (no VACANT row).

### Pre-floor B-cycle seat assignment (the 2017-cycle incumbents)
The four 2020-2021 B-cycle incumbents (all present at `minutes:2020-01-07` and NOT among those
sworn that day → continuing 2017 incumbents) map to seats by their 2021 outcome:
Choberka → **D1** (re-elected 2021), White → **AL-A** (re-elected), Blair → **AL-B** (re-elected),
and **Stephens → D3 by ELIMINATION** (the departing incumbent; D3 was won by newcomer Ken Richey
2021). All four are `medium` (only the 2018-01 term-start is inferred; their 2020-2021 membership
is documented).

## `district_versions.csv` — the 2022 redistricting

Ogden **DID redistrict** after the 2020 Census: **Ordinance 2022-9 (Joint Resolution 2022-3)**,
*"revising the four municipal districts and adopting the official municipal district boundary
map"* (amends Ogden Municipal Code §1-7-2), **adopted 2022-03-15 on a CONTESTED 6:1 roll call**
(AYE: Blair, Hyer, Richey, White, Vice Chair Lopez, Chair Nadolski; **NO: Choberka**, who wanted
more community outreach). Follows the county's Dec-2021 precincts; the memo notes the adopted map
"most closely resembles the existing boundaries." **Effective immediately upon posting** → in
force for the 2023 & 2025 elections; the 2021 election used the prior lines.

Versioning (10 rows):
- **`plan_2022`** (current) for D1–D4 — real geometry (`geo/council_districts.geojson`, the
  MUNIWARD-dissolved district polygons), `effective_start=2022-03-15`, open-ended, **high**.
- **`plan_2012`** (prior) for D1–D4 — **explicit acquisition GAP**: `geometry_ref` blank,
  `confidence=low`. The pre-2022 lines (used for 2019/2021) are **NOT in `geo/`** and no pre-2022
  Ogden precinct SOVC is available, so the old geometry is **not reconstructable from data on
  disk** and is **not fabricated**. `effective_start = data floor (2020-01-01)`.
- **`At-Large`** + **`Citywide`** (Mayor) rows — whole-city extent, unaffected by redistricting.

## `district_precincts.csv` — precinct → district composition

- **`plan_2022`**: **41 precinct rows** from `geo/precinct_to_district.csv` (the authoritative
  Ogden City GIS **MUNIWARD** field), all `high` (source_year 2025 = current layer). D1/D3 (2025)
  and D4 (2023) are additionally corroborated by the district-winner cross-check; D2 was unopposed.
- **`plan_2012`**: 4 explicit GAP rows (one per district, `precinct_id` blank, `low`) — prior
  composition not acquired.

### Precinct cross-check (`--check` / demo (e))

Groups the by-precinct votes by district contest and confirms the precinct-sum winner matches the
roster. All four district contests with precinct data **reconcile on the winning individual**:

| Cycle | Seat | Plan | Precinct-sum winner | Roster winner | Status |
|---|---|---|---|---|---|
| 2023 | D2 | plan_2022 | Richard Hyer 1501 (unopposed) | Richard **A.** Hyer | **RECONCILES** |
| 2023 | D4 | plan_2022 | Dave Graf 2465 (52.7%) | Dave Graf | **RECONCILES** |
| 2025 | D1 | plan_2022 | Flor Lopez 1106 (60.2%) | Flor Lopez | **RECONCILES** |
| 2025 | D3 | plan_2022 | Ken **R.** Richey 1795 (52.1%) | Ken Richey | **RECONCILES** |

**All four RECONCILE with 0 DISCREPANCY as of 2026-07-11.** D2 and D3 formerly printed a spurious
"DISCREPANCY" — a **middle-initial display-vs-ballot string artifact** (ballot "RICHARD HYER" vs
roster "Richard A. Hyer"; ballot "KEN R. RICHEY" vs roster "Ken Richey") from the old exact-string
comparator, though the same individual won. The hardened `roster_lib._winner_matches` (canon_key,
landed 2026-07-11) now resolves BOTH names to a `person_key` before comparing, so the middle-initial
difference no longer false-flags — **the roster names were never distorted to satisfy the
comparator.** The cross-check also reports `skipped 2 blank/non-numeric vote cell(s)` (the built-in
guard handling Ogden's voter-privacy-suppressed rows, formerly dropped by the `_precinct_votes.csv`
sidecar).

## Honest gaps (recorded, not filled)

- **Prior (`plan_2012`) district geometry** — not in `geo/`; `low`/blank rows in both
  `district_versions` and `district_precincts`. Not reconstructable from disk.
- **No per-precinct elections for 2019 or 2021** — Weber published summary-only canvasses, so the
  cross-check runs only for 2023 (D2/D4) + 2025 (D1/D3); the 2021 B-cycle districts are ungradeable.
- **Pre-floor 2017-cycle B-seat terms (`medium`)** — Choberka/Stephens/White/Blair were seated at
  the 2020 floor; their 2017 election / 2018 term-start is inferred from the B-cycle stagger, and
  Stephens' D3 seat is assigned by elimination.
- **0 VACANT / 0 UNKNOWN** — every in-window member maps to a named election winner or a documented
  continuing incumbent; no mid-term vacancy occurred (both honestly, not by omission).

## Two `cities.db` clerk-typo votes — now excluded by the tenure-window clamp

Ogden's minutes preserve two clerk roll-call typos that print a departed member's name on a later
meeting's VOTING-AYE line. Under the OLD person-level min/max those stray votes smeared onto the
member's `last_vote`; the **tenure-window clamp (landed 2026-07-11)** confines each tenure's bounds
to its own `[start, end)` window, so both stray votes now fall OUTSIDE the relevant window and are
excluded — no override, no hand-edit. The typos remain verbatim in the source minutes (cardinal
rule 2):

1. **Blair & Choberka** — the 2026-05-19 minutes' single VOTING-AYE line prints departed members
   **BLAIR & CHOBERKA**, while that meeting's own present-list shows the correct seated council
   (Hyer, F. Lopez, Lundell, Washington, Graf, Myers, Richey). Both left the council
   **2026-01-06 / 2026-01-20**; the 2026-05-19 vote is outside Blair's AL-B window
   `[2022-01-04, 2026-01-06)` and Choberka's D1 window `[2022-01-04, 2026-01-20)`, so the clamp
   yields **Blair `last_vote` 2025-12-16** and **Choberka `last_vote` 2026-01-06** (their true last
   service).
2. **Stephens** — the Jan-2022 chair-election roll calls print departed member STEPHENS (Richey was
   the sitting D3 member — see `meeting_minutes/CLAUDE.md`), a stray 2022-01-11 vote outside his D3
   window `[2018-01-01, 2022-01-04)`, so the clamp yields **Stephens `last_vote` 2021-12-21**. His
   true last service ended in 2021.

The clamp fixes these structurally in the shared library; the underlying `cities.db` rows (and the
source typos) are untouched.

## Where `roster_lib` didn't fit Ogden cleanly (for the hardening backlog)

1. **`precinct_crosscheck` winner comparison — LANDED 2026-07-11.** Formerly exact-string on the
   ballot name, so a middle-initial difference between the roster `person_name` and the ballot
   (Hyer, Richey) printed a false "DISCREPANCY" though the same person won. `roster_lib._winner_matches`
   now resolves BOTH names to a `person_key` via `canon_key` before comparing, so D2/D3 RECONCILE
   with 0 DISCREPANCY (the roster names were NOT distorted to satisfy a comparator).
2. **`precinct_crosscheck` blank-vote guard — LANDED 2026-07-11 (`_precinct_votes.csv` sidecar
   RETIRED).** Formerly `int(float(votes))` with no guard, so Ogden's voter-privacy **suppressed**
   rows (blank votes) needed the derived `_precinct_votes.csv` sidecar to drop them. The lib now has
   a built-in blank/suppressed/non-numeric guard (`skipped 2 blank/non-numeric vote cell(s)`), so
   `precincts_byprecinct_path` reads the canonical `election_results/ogden_results_by_precinct.csv`
   directly — no sidecar.
3. **County vs city precinct naming** (`29OG##` in the election file vs `OGD##` in
   `geo/precinct_to_district.csv`) means the lib's per-precinct MISMATCH detector (a simple
   `prefix + code` reconcile) can't map election precincts onto the GIS map, so only the
   **aggregate district-winner** reconciliation runs (which is clean). A format-normalization hook
   would enable the stronger per-precinct GIS↔ballot check.

## How to query

```bash
python3 roster/build_roster.py --demo    # (a) current  (b) as-of  (c) address→reps  (d) redistricting  (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Address + date → representatives** — `representatives_for_address(address, date)` resolves the
  address via `geo/address_to_district.py` to **District 1–4**, then returns that district's member
  on `date` **plus all 3 At-Large members and the Mayor**. It honors `district_versions`: a
  pre-2022-03-15 date is an **honest GAP** (plan_2012 geometry not on disk), never a fabricated
  district.
