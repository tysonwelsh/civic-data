# roster/ — Logan rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Logan Municipal Council + Mayor
seat over time** as dated intervals, reconciled from multiple sources with **per-row
provenance and confidence**. Answers: *who was on the council on date X?*, *who is serving
now?*, *who represents this address on this date?* — none of which the flat CSVs can answer.

Logan is a **backlog city** built on the mature shared library
(`../../scripts/roster_lib.py`), after Nephi/Provo/Vineyard/SLC/Lehi/Orem. It is
**AT-LARGE** (no geographic districts — at-large since 1975 → `district_versions` is one
degenerate whole-city row) with a **NON-VOTING mayor** (separately elected, presides, veto
power, never votes — like Nephi/Provo/Lehi, UNLIKE Vineyard/Orem's voting mayor → the
`MAYOR` rows carry no vote bounds). It exercises the **VACANT/appointment path TWICE**
(Lehi did it once):

- **AL-B1 (2020):** Jess W. Bradfield (2017-cycle incumbent) **resigned 2020-09-22** →
  **Ernesto López appointed 2020-10-20** to fill the vacancy (then elected 2021 & 2025).
- **AL-A1 (2025-26):** Mark A. Anderson (elected 2019 & 2023) **won the 2025 mayoralty** and
  **resigned his council seat (effective 2025-11-17)** → **Melissa Dahle appointed** (interim,
  oath 2026-01-06) — the "appointed-after-losing" twist (Dahle lost the 2025 council general,
  then was appointed to Anderson's *different* vacated seat; cf. Lehi's Lockhart).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates the two CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**19 rows: 17 person-tenures + 2 VACANT intervals**). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for Logan** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer. Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit the two generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-cohort seat label. Logan = **Mayor + 5 at-large council seats**:
  - `AL-A1`, `AL-A2`, `AL-A3` — **Cohort A** (3 seats; elected 2019 / 2023 / 2027; terms
    Jan-2020…, Jan-2024…). `AL-A1` is **anchored** by the Mark-Anderson→Dahle vacancy chain.
  - `AL-B1`, `AL-B2` — **Cohort B** (2 seats; elected 2017 / 2021 / 2025; terms Jan-2018…,
    Jan-2022…, Jan-2026…). `AL-B1` anchored by the Bradfield→López vacancy chain; `AL-B2` by
    the distinct continuous holder Amy Z. Anderson.
  - `MAYOR` — single seat (elected 2017 / 2021 / 2025).
  Logan is **unusually clean**: every seat is anchored by a continuous distinct holder or a
  **clean 1-for-1 replacement** — **no two same-cohort newcomers ever arrive together**, so
  (unlike Lehi) there is **no within-cohort labelling ambiguity**. The 2019 trio
  (Anderson=A1 / Simmonds=A2 / Jensen=A3) and the 2017 pair (Bradfield=B1 / Amy Anderson=B2)
  are labelled at the data floor; each later transition touches exactly one seat.
- **`district`** = `At-Large` on every row (FK into `district_versions`; Logan has no
  geographic districts, no wards — the top-N vote-getters win the N open seats).
- **`person_key`** = `first_last`. **KNOWN TRAP — the two Andersons are DISTINCT people and
  are never merged:**
  - **`amy_anderson`** = Amy Z. Anderson — AL-B2, 2017-cycle incumbent, re-elected 2021,
    did not run 2025.
  - **`mark_anderson`** = Mark A. Anderson — AL-A1, elected 2019 & 2023, resigned 2025-11-17,
    then **Mayor 2026+**.
  Both appear as bare "…ANDERSON" in the election data, so `canon_key` resolves them via the
  config **`disambiguators`** map (`ANDERSON → {AMY: amy_anderson, MARK: mark_anderson}`)
  **before** the flat surname table — exactly as Nephi did for the two Worwoods / Provo for
  the two Davids. **`ANDERSON` is deliberately absent from `NAME_TO_KEY`** (adding it would
  merge the two). (There is also a non-member Richard Anderson, Finance Director, who never
  appears as a candidate or voter.)
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained per seat, or cut at a documented `vacate_date` (which inserts a VACANT
  interval — VACANT begins the day AFTER the last day served).
- **`start_event`** ∈ {elected, reelected, appointed, vacated (VACANT rows)}.
  **`end_event`** ∈ {reelected, did-not-run, resigned, serving, filled (VACANT rows)}.
  `did-not-run` = a full-term member not a candidate in the next cycle (Jensen; Amy Z.
  Anderson; Daines, who did not seek a third mayoral term). `resigned` = a mid-term departure
  that created a vacancy (Bradfield; Mark A. Anderson).
- **`election_year`** — the cycle that seated the tenure (**blank for a pure appointment** —
  López's 2020 appointed row and Dahle's).
- **`first_vote` / `last_vote`** — the person's first/last observed **Council-body** member
  vote in `cities.db` (`role`, `city='logan'`). **The `MAYOR` rows carry NO vote bounds** —
  Logan's mayor is non-voting (see below): `holly_daines` has zero db council rows, and
  `mark_anderson`'s db votes (his 2020-2025 council service) are emptied on his MAYOR row by
  the `non_voting_mayor` flag (and, redundantly, by the per-tenure vote clamp — his mayoral
  window holds no Council votes) so his council span stays on his AL-A1 rows, not the mayoralty.
- **`sources`** — semicolon list. **Every row carries a non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result or minutes-documented oath / appointment /
  vacancy) · `medium` (pre-floor 2017-cycle term, term-start inferred from the stagger) ·
  `low` (unknown — **none here**).

Counts: **19 rows — 16 high / 3 medium / 0 low; 2 VACANT intervals.** 0 overlapping tenures
per seat. The 3 `medium` rows are the pre-floor 2017-cycle holders whose 2018-01 term-start
is inferred: **Bradfield** (AL-B1), **Amy Z. Anderson** (AL-B2), and **Daines**'s first Mayor
term — all seated at the 2020 data floor and positively confirmed as *continuing* incumbents
by the 2020-01-07 oath list (which swore only the three 2019 winners).

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/logan_results_by_candidate.csv`, municipal **general**
   winners only (`keep_election_row` drops every **primary** advancer row — so e.g. the 2019
   primary's Heare/Garrity/Verdoes and the 2025 primary's Dahle/Seamons are not mis-counted as
   seat winners). Logan is plurality / vote-for-N at-large (no RCV). UPPER-CASE names
   normalized to `person_key`. The script cross-checks that **all 12** general winners map to
   an `elected`/`reelected` tenure (prints to stderr on drift — currently clean).
   - **roster_lib is_winner CONTRACT SHIM (a place the library didn't fit Logan cleanly):**
     `roster_lib.load_election_winners` accepts `is_winner ∈ {true,1,yes}`, but Logan's
     **canonical** election CSV encodes winners as **`Y`/`N`** (other cities use `True/False`).
     Rather than edit the shared library OR the canonical file, the driver regenerates a
     normalized copy (`Y`→`true`) into the OS temp dir at run time and points `elections_path`
     at it. Pure format shim for the Layer-1 cross-check; the tenure rows are hand-curated.
2. **Vote / attendance bounds** — `cities.db` `role` (`city='logan'`, `body='Council'`): sets
   `first_vote`/`last_vote` and would surface any off-cycle appointee. **Caveat (Logan-specific):
   Logan's 2020-2021 council votes are heavily tally-only** ("Carried unanimously (no names)"),
   so an appointee's *observed* first named vote can lag their true start — **López** was
   appointed 2020-10-20 and moves motions from Jan-2021, but his first NAMED roll-call vote in
   `cities.db` is `2021-12-07`. That lag is a source-recording limit, **not** a gap; his tenure
   start is anchored by the 2020-10-20 appointment minutes, not by the vote bound.
3. **Swearing-in / appointment / vacancy events** — read from `meeting_minutes/minutes/**`
   (Logan records oaths + resignations in narrative prose) and encoded in `TENURES`. The
   biennial oath dates and the two mid-term events are all documented on disk.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (0 rows now).

Then `end_date` is chained per seat, the **VACANT-interval** rule runs, and the table is
validated (no overlaps; sources+confidence present; the `vacate_confidence` invariant + the
un-recovered-minutes gap detector). Logan has **no `meeting_minutes/minutes_unrecovered.csv`**,
so the gap detector sees an empty set (both VACANT windows are fully bounded by recovered
meetings → both stay `high`).

## The two VACANT / mid-term-appointment chains (spot-checked, fully on-disk)

- **AL-B1 — Bradfield → [VACANT] → López (2020).** Jess W. Bradfield (2017-cycle cohort-B
  incumbent) is present through the 2020-09-14 meeting, then resigned. The **2020-10-20**
  minutes state verbatim: *"The Oath of Office was administered by Judge Lee Edwards to newly
  appointed Councilmember Ernesto López who will fill the vacancy left by Jess Bradfield who
  resigned on September 22, 2020. Councilmember López will serve until January 1, 2022."* →
  Bradfield ends `resigned` at `vacate_date=2020-09-23` (day after the documented 2020-09-22
  resignation), an explicit **VACANT** interval spans 2020-09-23…2020-10-20, then López's
  **`appointed`** tenure begins at his 2020-10-20 oath. **Confidence high** on the vacancy
  (resignation date, vacancy, and appointment all in recovered minutes — not gap-bounded);
  Bradfield's *row* is `medium` only because his 2018-01 term-*start* is pre-floor inferred.
- **AL-A1 — Mark A. Anderson → [VACANT] → Dahle (2025-26).** Mark A. Anderson (elected 2019
  rank1, re-elected 2023 to a term to Jan-2028) **won the 2025 mayoralty** and **resigned his
  council seat** effective 2025-11-17. He is present + voting through **2025-11-04** and is
  **absent** from the **2025-11-18** present list (only 4 members); the **2025-12-01/12-16**
  minutes document *"the resignation of Mark Anderson … there is a vacancy on the Council.
  State Code requires an appointment within 30 days,"* and the seat rolls **"VACANT"** in the
  2025-12-16 roll calls. At **2025-12-16** the council interviewed 9 applicants and *"voted by
  ballot … Melissa Dahle received three votes and Scott Mershon received one vote … Melissa
  Dahle will be appointed as the interim city councilmember."* Her oath was administered
  **2026-01-06** (*"Oath of Office … to Councilmembers Elect Ernesto López, Katie Lee-Koven and
  Melissa Dahle"*). → Anderson ends `resigned` at `vacate_date=2025-11-18`, a **VACANT**
  interval spans 2025-11-18…2026-01-06, then Dahle's **`appointed`** tenure begins at her
  2026-01-06 oath (the seat rolled VACANT between her 12-16 selection and her 01-06 swearing-in
  — her first db vote is 2026-01-06). **Confidence high** (fully on-disk).
  - **The Dahle twist:** she **ran in the 2025 council general and LOST** (rank3 of 4, first
    loser, 3559 vs the 84-vote cutoff), then was **appointed to Anderson's *different* (vacated
    cohort-A) seat** — so she serves the remainder of that 2024-2028 term despite losing the
    seat she campaigned for. `election_year` blank (pure appointee; `keep_election_row` drops
    her 2025-primary advancer row, and she is `is_winner=N` in the general).

## Other key transitions (spot-checked against source minutes)

- **Continuing 2017-cycle incumbents (Amy Z. Anderson, Bradfield, Mayor Daines) — QUOTED.**
  The **2020-01-07** minutes swore *"Councilmember Elect Jeannie F. Simmonds, Councilmember
  Elect Tom Jensen and Councilmember Elect Mark A. Anderson"* — **only the three 2019 winners**.
  Amy Z. Anderson (as *"Vice Chair Amy Z. Anderson"*), Jess W. Bradfield, and Mayor Daines head
  the same present-list but were **NOT** sworn that day, confirming they were **continuing
  incumbents** (cohort-B / mayor elected 2017, pre-floor), not 2019 arrivals.
- **2022-01-04 oath** — *"Oath of Office to Mayor Elect Holly H. Daines, Councilmember Elect
  Amy Z. Anderson and Councilmember Elect Ernesto Lopez"* (the 2021 winners; the 2 cohort-B
  seats + Mayor). López converts from appointee to elected here.
- **2024-01-02 oath** — *"Oath of Office to Councilmember Elect Jeannie F. Simmonds,
  Councilmember Elect Mark A. Anderson, and Councilmember Elect Mike Johnson"* (the 2023
  winners; Anderson + Simmonds re-elected, Johnson new, replacing Jensen who was not a 2023
  candidate). Simmonds's is the razor-thin 3rd seat under the **2023 recount episode** (Simmonds
  2419 vs Needham 2400, 19-vote margin; the recount did not change the result — see
  `election_results/CLAUDE.md`).
- **2026-01-06 oath** — *"Oath of Office to Mayor Elect Mark A. Anderson and Councilmembers
  Elect Ernesto López, Katie Lee-Koven and Melissa Dahle."* The current roster.

## Mayor is NON-VOTING (determination + handling)

Logan's mayor is **separately elected, presides, holds veto power, and does NOT vote**
(`election_results/CLAUDE.md`: *"Separately-elected Mayor does NOT vote (veto)"*;
`geo/CLAUDE.md`; `meeting_minutes/CLAUDE.md`). **Verified in the data:** the mayor never
appears in a roll call — `all_votes.csv` has exactly **9 distinct named voters, none of them a
mayor** (Daines is only ever *"Administration present: Mayor Holly H. Daines"*). So Logan is
like **Nephi/Provo/Lehi**, not Vineyard/Orem. Handling: the config sets **`non_voting_mayor=True`**,
so every `MAYOR` row gets **empty vote bounds** and `validate()` enforces it. `holly_daines`
has **zero** `cities.db` council rows (never votes). **Mark A. Anderson is the subtle case:**
he IS in `DB_KEY` for his 2020-2025 *council* votes (AL-A1), but his 2026+ *MAYOR* row is
emptied by the flag — his council votes stop at **2025-11-04** and he casts none as mayor, so
it carries no vote bounds (the per-tenure vote clamp would empty it too — the mayoral window
holds no Council votes). His AL-A1 council tenure
(ends 2025-11-18 VACANT) and his MAYOR tenure (begins 2026-01-06) **do not overlap**.

## Honest gaps (recorded, not filled)

- **Pre-floor 2017-cycle terms (`medium`).** Bradfield (AL-B1), Amy Z. Anderson (AL-B2), and
  Daines's first Mayor term were seated at the 2020 floor; their 2017 election / 2018-01
  term-start is inferred from the staggered 4-year cycle, not asserted. (The 2020-01-07 oath
  list positively confirms all three were continuing incumbents, not 2019 arrivals.)
- **López's observed vote lag.** His first *named* roll-call vote (2021-12-07) lags his 2020-10-20
  appointed start because Logan's 2020-2021 votes are heavily tally-only — a source-recording
  limit, not a gap. Tenure anchored by the appointment minutes.
- **No unidentified appointee.** Both mid-term arrivals (López, Dahle) resolved to named people
  from the minutes → **no `UNKNOWN`/`low` rows**. Both VACANT windows are bounded by recovered
  meetings → both `high`.

## `district_versions.csv` — DEGENERATE for Logan (at-large)

Logan's council + mayor are elected **entirely AT-LARGE — no wards/districts** (since 1975) —
so this table holds exactly **one** row (`district_id=At-Large`, whole city, open-ended).
`geometry_ref` = `geo/city_boundary.geojson`. The sub-district address→representative join
(validated on Provo/SLC) here correctly degenerates to an in/out-of-city-limits check → all
sitting members + mayor.

## How to query

```bash
python3 roster/build_roster.py --demo   # (a) current  (b) 2025-26 VACANT window  (b') 2020 VACANT window  (b'') 2022  (c) address→rep
python3 roster/build_roster.py --check  # regenerate + validations only
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Mayor + 5:
  Dahle, Simmonds, Johnson, López, Lee-Koven + Mayor Mark A. Anderson).
- **As of a past date** — `roster_as_of(date, body)`: **2025-12-05** shows the AL-A1 **VACANT**
  interval; **2020-10-01** shows the AL-B1 **VACANT** interval; **2022-07-01** shows a full
  normal roster.
- **Address + date → representative** — `representatives_for_address(address, date)`: for Logan
  this **correctly reduces to At-Large → all sitting members + mayor** on that date. Inside a
  VACANT window it honestly returns the `VACANT` placeholder alongside the sitting members.

## What Logan adds to the fleet

The first roster city with **TWO** mid-term resignation→appointment chains (both fully on-disk),
each a different flavor: an incumbent who **resigned outright** (Bradfield 2020) and one who
**resigned to take a higher office he'd just won** (Mark A. Anderson → Mayor 2025-26); a
**second "appointed-after-losing" case** (Dahle, after Lehi's Lockhart); a **person who spans
two bodies with the non-voting-mayor flag doing real work** (Mark A. Anderson's council votes
kept off his MAYOR row); the **two-Anderson disambiguation** (the config `disambiguators` map);
and a **library-contract shim** (Logan's `Y/N` `is_winner` normalized at run time without
touching the shared library or the canonical file). **Federation into the root `cities.db` is
NOT done here** (it would require touching the shared build) — see the other cities' federation
notes.
