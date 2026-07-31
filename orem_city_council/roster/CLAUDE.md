# roster/ — Orem rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Orem City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance
and confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who
represents this address on this date?* — none of which the flat CSVs can answer.

Orem is the **AT-LARGE + VOTING-MAYOR** city for the roster schema. Like Nephi and Vineyard
it is **entirely at-large** (no geographic districts → `district_versions` is one degenerate
whole-city row). What makes it distinct: **Orem's Mayor is a FULL VOTING member of the
council** (`non_voting_mayor=False`) — the mayor is named in the *"Those voting aye: …"* roll
calls and routinely moves motions — so the **MAYOR rows carry `first_vote`/`last_vote`** and
the mayor is in `db_key` (contrast Nephi/Provo/Lehi/SLC, whose non-voting/tie-break mayors get
empty vote bounds). Orem also has **no in-window mid-term vacancy** → **0 VACANT rows** (an
honest structural fact: every transition is a clean January term boundary; the VACANT/appointed
path is exercised by Vineyard).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates the two CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**18 rows: 18 person-tenures + 0 VACANT intervals**). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for Orem** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit the two generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-class seat label. Orem = **Mayor + 6 at-large council seats**,
  3 up each odd year:
  - `AL-A1`, `AL-A2`, `AL-A3` — **Class A** (elected 2019 / 2023 / 2027; terms Jan-2020…, Jan-2024…).
  - `AL-B1`, `AL-B2`, `AL-B3` — **Class B** (elected 2017 / 2021 / 2025; terms Jan-2018…, Jan-2022…, Jan-2026…).
  - `MAYOR` — single seat (elected 2017 / 2021 / 2025).
  Within-class seat **numbers** are a stable labelling of the person-chain; where two
  same-class members depart/arrive together the A2/A3 (and B2/B3) split is a **labelling
  choice** (flagged in `note`). The continuous anchors are **`AL-A1` = Lambson (2019→2023)**
  and **`AL-B1` = Millett (2021→2025)**.
- **`district`** = `At-Large` on every row (FK into `district_versions`; Orem has no districts).
- **`person_key`** = `first_last`. All Orem surnames are **distinct in-window** — no shared
  surname, so no first-name disambiguation is needed (note the **two Davids**, `david_young`
  the Mayor and `david_spencer` a councilmember, are keyed by their distinct surnames; the
  shared first name `DAVID` is never mapped).
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained: a tenure ends when the next tenure on the same `seat_id` begins.
- **`start_event`** ∈ {elected, reelected}. **`end_event`** ∈ {reelected, lost, did-not-run,
  serving}. `did-not-run` = a full-term member not a candidate the next cycle (end *date*
  precise; only retire-vs-decline unstated). `lost` = ran the next cycle and lost (Spencer 2025,
  Young 2025). **No `resigned`/`vacated`/`appointed`/`filled` events — Orem had no in-window
  mid-term vacancy.**
- **`election_year`** — the cycle that seated the tenure. Multi-term members get **one row per
  term** (Lambson ×2, Millett ×2, Spencer ×2, Macdonald ×2).
- **`first_vote` / `last_vote`** — the person's first/last observed **council-body** member
  vote in `cities.db` (`role`/`vote`, `city='orem'`). Orem has full named Aye/Nay roll calls,
  so these are reliable. **Orem's Mayor VOTES**, so the `MAYOR` rows also carry vote bounds
  (Brunst 2020-01-14…2021-12-14, Young 2022-01-04…2025-12-09, McCandless 2026-01-13…). For a
  multi-term holder each row now carries its **own tenure-clamped** span — first/last vote within
  that term's `[start_date, end_date)` window (e.g. Lambson's two AL-A1 rows read 2020-01-14…
  2023-12-29 and 2024-01-09…2026-05-05, not the whole-career span).
- **`sources`** — semicolon list (`election:YYYY …`, `votes:…`, `minutes:DATE …`). **Every row
  carries a non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result + minutes present-list) · `medium` (pre-floor
  2017-cycle term, term-start 2018-01 inferred from the stagger — win predates the 2019
  election-data floor and the 2020-01-14 minutes floor) · `low` (unknown — **none here**).

Counts: **18 rows — 14 high / 4 medium / 0 low; 0 VACANT intervals.** 0 overlapping tenures
per seat. The 4 `medium` rows are the 4 pre-floor 2017-cycle holders serving at the data floor:
**Sumner** (AL-B1), **Spencer** (AL-B2 term 1), **Macdonald** (AL-B3 term 1) and **Brunst**
(Mayor term 1).

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/orem_results_by_candidate.csv`, municipal **general**
   winners only (`keep_election_row` drops the primary advancer rows). Orem is **at-large
   vote-for-3** — every `is_winner=Y` general row maps to a seat via office=body. UPPER-CASE
   names normalized by surname (`JEFFREY K. LAMBSON`→`jeff_lambson`). The script cross-checks
   that **every** general winner maps to an `elected`/`reelected` tenure (prints to stderr on
   drift — **currently clean**: all 2019/2021/2023/2025 Council + 2021/2025 Mayor winners map).
2. **Vote / attendance bounds** — `cities.db` `role`/`vote` (`city='orem'`, `body='Council'`):
   sets `first_vote`/`last_vote`. Because the **mayor votes**, Brunst/Young/McCandless surface
   here too. The clean January term boundaries in the bounds (first/last_seen at 2020-01-14 /
   2022-01-04 / 2024-01-09 / 2026-01-13, plus Sumner/Brunst last 2021-12-14) are the evidence of
   **no off-cycle appointee** → 0 VACANT rows.
3. **Present-lists / seating dates** — read from `meeting_minutes/minutes/**` (Orem records
   these in the `ELECTED OFFICIALS` present-list header, not a machine motion type). These date
   the January seatings and confirm the mayor is in the Aye lists.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (0 data rows).

Then `end_date` is chained per seat and the table is validated (no overlaps; sources+confidence
present; `non_voting_mayor` invariant; the `minutes_unrecovered.csv` gap-detector — a no-op here,
that file does not exist). A failure aborts the write.

## The VOTING mayor — the point of this city (spot-checked, QUOTED)

Orem's Mayor is a **full voting member of the council** — `non_voting_mayor=False`, and the
MAYOR rows carry vote bounds:

- **2020-01-14 minutes** (Brunst): present-list *"CONDUCTING  Mayor Richard F. Brunst … ELECTED
  OFFICIALS  Jeff Lambson, Debby Lauret, Tom Macdonald, Terry Peterson, David Spencer, and Brent
  Sumner"* (Mayor + 6 = 7), and the roll call **names the mayor as a voter**: *"Those voting aye:
  **Richard F. Brunst**, Jeff Lambson, Debby Lauret, Tom Macdonald, Terry Peterson, David Spencer,
  and Brent Sumner. The motion passed."*
- **2022-01-11 minutes** (Young): *"Those voting aye: **David A. Young**, Terry Peterson, David
  Spencer, Jeff Lambson, and LaNae Millet."* — Mayor Young in the Aye list.
- `cities.db` confirms every mayor with Council-body votes (Brunst, Young, McCandless), so their
  bounds land on the `MAYOR` rows (not on any invented council seat).

## Key transitions (spot-checked, QUOTED)

- **Mayoral chain Brunst → Young → McCandless.** **Brunst** (elected Mayor 2017, pre-floor) did
  not run in 2021; the open seat went to **David Young** (2021 general, 9,647 / 59.06% over Jim
  Evans; *"CONDUCTING  Mayor David A. Young"* 2022-01-11). Young ran for a 2nd term in 2025 and
  **LOST to Karen McCandless** (certified 9,574–9,056, 51.39%); 2026-01-13 present-list heads
  *"CONDUCTING Mayor Karen McCandless"*. **NOTE — the current mayor is KAREN McCandless, not
  "David"** (the task brief's "David McCandless" is a mis-recollection; corrected against the
  election SOVC, `election_results/CLAUDE.md`, Daily Herald/KSL, and the 2026 minutes).
- **A seat transition (Class A, AL-A2).** **Terry Peterson** (2019 top vote-getter, 9,858; seated
  2020-01-14) was **not a candidate in 2023** (last db vote 2023-12-29) → term expired Jan 2024;
  **Jenn Gale** (2023 general, rank2 8,606) seated 2024-01-09 (*"ELECTED OFFICIALS … Jenn Gale"*).
- **Class B re-elections.** Spencer and Macdonald were 2017-cycle incumbents (present at the 2020
  floor) **re-elected in 2021** (in the election data), so each has a pre-floor `medium` term +
  a 2021 `high` term. Spencer then **ran in 2025 and lost** the final seat to Millett (8,789 vs
  9,077, `end_event=lost`); Macdonald **did not run** in 2025 (`did-not-run`).

## Honest gaps (recorded, not filled)

- **Pre-floor 2017-cycle terms (`medium`).** Sumner (AL-B1), Spencer (AL-B2), Macdonald (AL-B3)
  and Brunst (Mayor) were seated at the 2020-01-14 floor; their 2017 election / **2018-01
  term-start is inferred** from the Class-B / mayoral 4-year stagger, **not asserted as fact**,
  and no `election:2017` citation is fabricated (sources cite observed votes + the 2020 present-
  list + non-candidacy in 2021). Their `election_year=2017` is the inferred cycle label.
- **Exact January seating dates.** `start_date` uses the **first documented council meeting** of
  the term (2020-01-14 / 2022-01-04 / 2024-01-09 / 2026-01-13 — matching `cities.db` first_seen);
  the swearing-in oath itself is not separately printed, but the term is election-anchored (high).
- **Within-class seat numbers.** A2/A3 (Peterson/Lauret → Gale/Killpack) and B2/B3 (Spencer/
  Macdonald → Mecham/Muhlestein) are **labelling choices** where same-class members arrived/left
  together — the **person-tenures are exact**; the seat *number* between paired arrivals is not
  source-attested (the continuous anchors AL-A1/AL-B1 are).
- **No vacancy / no appointment / no UNKNOWN.** Every departure aligns with a term boundary → **0
  VACANT rows, 0 appointments, 0 `low` rows** — honest, not a coverage gap.

## `district_versions.csv` — DEGENERATE for Orem (at-large)

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Orem's council + mayor are elected **entirely AT-LARGE — no
wards/districts** — so this table holds exactly **one** row (`district_id=At-Large`, whole city,
open-ended). `geometry_ref` = `geo/city_limits.geojson` (the UGRC Utah Municipal Boundaries
polygon). Orem's limits can change over time by **annexation**; the row points at the **current**
limits, and prior-versioned boundaries are **not on disk and not fabricated**. The sub-district
address→representative join correctly degenerates to whole-city → all sitting members + mayor.

## How to query

```bash
python3 roster/build_roster.py --demo   # (a) current  (as-of dates)  (c) address→rep
python3 roster/build_roster.py --check  # regenerate + validations only
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Mayor + 6:
  McCandless + Lambson, Gale, Killpack, Millett, Mecham, Muhlestein).
- **As of a past date** — `roster_as_of(date, body)`: e.g. **2020-06-01** shows Mayor Brunst +
  the pre-floor Class-B trio + the 2019 Class-A trio.
- **Address + date → representative** — `representatives_for_address(address, date)`: for Orem
  this **correctly reduces to At-Large → all sitting members + mayor** on that date (degenerate,
  like Nephi/Vineyard). The at-large path does not call the geo tool (no network needed).

## Federation

Federation into the root `cities.db` is **not done here** (it would require touching the shared
`scripts/build_cities_db.py`) — see the Nephi/Provo/Vineyard roster CLAUDE.md federation notes.
The federation step picks up any city that HAS a `roster/` dir automatically.
