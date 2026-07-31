# roster/ — Park City rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Park City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance
and confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who
represents this address on this date?* — none of which the flat CSVs can answer.

Park City is the **tenth city** built on the mature shared library
(`../../scripts/roster_lib.py`), after Nephi/Provo/Vineyard/SLC/Lehi/Orem/Logan/Millcreek/
Ogden. It is **AT-LARGE** (Mayor + 5 all-at-large council, no geographic districts — like
Nephi/Vineyard/Lehi/Orem → `district_versions` is one degenerate whole-city row) with a
**NON-VOTING mayor** (presides; votes only to break a tie — like Nephi/Provo/Lehi, UNLIKE
Vineyard's/Orem's voting mayor → the `MAYOR` rows carry no vote bounds).

**What Park City adds: TWO council→mayor CROSSOVERS on the SAME seat (AL-A1), each a
mid-term vacancy filled by appointment.** Nann Worel (council 2019 → mayor 2021) and Ryan
Dickey (appointed to Worel's seat 2022 → elected 2023 → mayor 2025) each vacated the SAME
cohort-A seat ~2 years early to become mayor, producing **two VACANT intervals** and a
seat filled by appointment **twice** (Dickey 2022, Molly Miller 2026). Handled exactly like
Ogden's Nadolski / Logan's Anderson / Millcreek's Jackson: the crossover's COUNCIL rows carry
the council vote bounds, the MAYOR row is emptied by `non_voting_mayor`, and council/mayor
tenures never overlap.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates the two CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**19 rows: 17 person-tenures + 2 VACANT intervals**). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for Park City** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer. Applied **last**, wins ties. **0 data rows (RETIRED 2026-07-11)** — the tenure-window clamp now reproduces the former Worel de-smear structurally (see below); header-only. |

**Never hand-edit the two generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-cohort seat label. Park City = **Mayor + 5 at-large council seats**:
  - `AL-A1`, `AL-A2`, `AL-A3` — **Cohort A** (3 seats; elected 2019 / 2023 / 2027; terms
    Jan-2020…, Jan-2024…). `AL-A1` is **anchored** by the Worel→Dickey→Miller crossover/vacancy
    chain (two councilmembers-turned-mayor, two appointments).
  - `AL-B1`, `AL-B2` — **Cohort B** (2 seats; elected 2021 / 2025; terms Jan-2022…, Jan-2026…).
    `AL-B1` is anchored by the DISTINCT continuous holder **Tana Toly** (2022 → serving, re-elected 2025).
  - `MAYOR` — single seat (elected 2021 / 2025).
  Within-cohort seat **numbers** are a stable labelling of the person-chain; where two
  same-cohort members arrive/depart together the split is a **labelling choice** (flagged in
  `note`) — the person-tenures are exact. Labelling choices: the 2019 pair Gerber(A2)/Doilney(A3)
  and their 2024 successors Parigian(A2)/Ciraco(A3); the pre-floor pair Joyce(B1)/Henney(B2).
- **`district`** = `At-Large` on every row (FK into `district_versions`; Park City has no
  geographic districts, no numbered seats — the top-N vote-getters win the N open seats).
- **`person_key`** = `first_last`. Park City has **no shared surnames** among council/mayor
  members, so surname keys suffice and **no disambiguators** are needed.
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained: a tenure ends when the next tenure on the same `seat_id` begins, or at
  a documented `vacate_date` (which then inserts a VACANT interval). Elected-term starts use
  the first recovered meeting of that January (matches cities.db `first_seen`); documented
  swearing/appointment dates are used where they differ (Dickey appt 2022-01-27; Miller appt
  2026-01-20; Dickey-mayor 2026-01-05, sworn "on Monday" per the 2026-01-08 minutes).
- **`start_event`** ∈ {elected, reelected, appointed, vacated (VACANT rows)}.
  **`end_event`** ∈ {reelected, did-not-run, lost, became-mayor, serving, filled (VACANT rows)}.
  `did-not-run` = a member not a candidate in the next cycle (Gerber, Doilney, Joyce).
  `lost` = ran for re-election and lost (Henney 2021, Rubell 2025) or ran for mayor and lost
  (Beerman 2021). `became-mayor` = a councilmember who won the mayoralty and vacated the seat
  mid-term (Worel, Dickey — the two CROSSOVERS).
- **`election_year`** — the cycle that seated the tenure (**blank for a pure appointment** —
  Dickey's first row, Miller).
- **`first_vote` / `last_vote`** — the earliest/latest observed **Council-body** member vote
  **CLAMPED to each tenure's own `[start_date, end_date)` half-open window**
  (`roster_lib.clamp_vote_bounds`), from `cities.db` (`role`, `city='park_city'`); **blank** if the
  window holds no observed vote. **The `MAYOR` rows carry NO vote bounds** — Park City's mayor is
  non-voting (see below), so `andy_beerman` (a pure mayor) is left out of the db-key map and the
  crossovers' MAYOR rows are emptied by `non_voting_mayor`. A member who holds one seat across two
  tenures (Toly, Dickey) is **clamped per tenure** — each row shows only that term's votes (e.g.
  Toly: `2022-01-06…2025-12-18`, then `2026-01-08…2026-05-21`), not a shared whole-career span. The
  authoritative interval is `start`/`end`.
- **`sources`** — semicolon list (`election:YYYY …`, `appt:DATE (minutes …)`, `votes:…`,
  `minutes:DATE …`). **Every row carries a non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result or minutes-documented swearing / appointment /
  vacancy) · `medium` (pre-floor 2017-cycle term, term-start inferred from the stagger) ·
  `low` (unknown — **none here**).

Counts: **19 rows — 16 high / 3 medium / 0 low; 2 VACANT intervals.** 0 overlapping tenures
per seat. The 3 `medium` rows are the pre-floor 2017-cycle holders: **Joyce** (AL-B1),
**Henney** (AL-B2), and **Beerman**'s Mayor term — all seated at the 2020 data floor, their
2017 election / 2018-01 term-start inferred from the 4-year cohort stagger.

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/park_city_results_by_candidate.csv`, municipal **general**
   winners only (`keep_election_row` drops the **primary** advancer rows — Park City lists each
   primary advancer as `is_winner=Y`, so this filter is essential). Vote-for-N block plurality
   (no RCV, no districts): all N general winners each cycle map to a seat via office=body
   (at-large). UPPER-CASE names normalized to `person_key`. The script cross-checks that **every**
   general winner maps to an `elected`/`reelected`/`became-mayor` tenure — **clean, no drift**.
2. **Vote / attendance bounds** — `cities.db` `role` (`city='park_city'`, `body='Council'`):
   sets `first_vote`/`last_vote` and surfaces off-cycle appointees (a voter with no election
   win). Park City's two appointees both show it: **Dickey** first_seen 2022-01-27 (sworn as a
   mid-term appointee) and **Miller** first_seen 2026-01-20 (sworn appointee) — neither maps to
   a general win in those cycles.
3. **Swearing-in / appointment / vacancy events** — read from `meeting_minutes/minutes/**`
   (Park City records these in narrative prose + resolutions). These date the two crossovers'
   mid-term departures and the two appointments precisely.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (**0 rows, RETIRED 2026-07-11** —
   the tenure-window clamp now reproduces the former Worel de-smear structurally; header-only).

Then `end_date` is chained per seat, the **VACANT-interval** rule runs (twice on AL-A1), and the
table is validated (no overlaps; sources+confidence present; `non_voting_mayor` empties every
MAYOR row; the `vacate_confidence` invariant + the un-recovered-minutes gap detector). A failure
aborts the write. Neither VACANT window contains an un-recovered minutes date (the gap detector
sees them as fully documented → high).

## The two CROSSOVERS + two VACANT chains on AL-A1 (spot-checked, fully on-disk)

- **CROSSOVER #1 — Worel → [VACANT] → Dickey (appointed).** Nann Worel was **elected to
  COUNCIL 2019** (rank1, cohort A, term to Jan-2024). She **won the 2021 MAYOR race** (2,048 /
  60.86% over incumbent Beerman) and vacated her council seat ~2 years early to be sworn mayor.
  The **2022-01-06** ROLL CALL heads the present list *"Mayor Nann Worel"* with only **4
  councilmembers** and announces *"17 applications were received for the council seat vacated
  when she was elected mayor"*; the Council interviewed applicants Jan 7 & 11, **appointed Ryan
  Dickey 2022-01-13** (*"Appointment of New City Council Member to Fill the Seat Vacated by
  Nann [Worel]"*), and swore him in **2022-01-27** (*"Ryan … Dickey … appointed by the Council
  at the last meeting to fill the remaining term left vacant when Mayor Worel was elected"*). →
  Worel's AL-A1 council row ends `became-mayor` at **2022-01-06** (mayor start), an explicit
  **VACANT** interval spans 2022-01-06…2022-01-27, then Dickey's **`appointed`** tenure begins.
- **CROSSOVER #2 — Dickey (elected) → [VACANT] → Miller (appointed).** Dickey **won this
  cohort-A seat outright in 2023** (rank1, term to Jan-2028), then **won the 2025 MAYOR race**
  (the 1,706–1,699 **7-vote recount** over Rubin, certified Res 25-2025 + recount Res 27-2025)
  and again vacated the SAME seat ~2 years early. The **2026-01-08** minutes note *"the new
  mayor being sworn in on Monday"* (2026-01-05) and the ROLL CALL shows Dickey chairing as
  mayor with **4 councilmembers**; the Council interviewed applicants 2026-01-13 and at the
  **2026-01-15** meeting *"Mayor Dickey broke the tie by voting for Molly Miller"* (an
  appointment selection), swearing her in **2026-01-20** (*"Swearing In of a Council Member …
  for a Term Expiring [Jan-2028]"*). → Dickey's AL-A1 elected row ends `became-mayor` at
  **2026-01-05**, a second **VACANT** interval spans 2026-01-05…2026-01-20, then Miller's
  **`appointed`** tenure begins.
  - **Both VACANT windows are `high`** (not gap-bounded like Vineyard's Cameron): each
    resignation-to-mayor, vacant council, and successor appointment is in **recovered** minutes,
    and each window is bracketed by two recovered meetings (last council vote → documented vacant).
  - **The Miller twist** (like Lehi's Lockhart): she **lost the 2025 council PRIMARY** (rank7,
    `is_winner=N`, did not reach the general), then was **appointed** to Dickey's different
    (vacated) seat — so she serves to **Jan-2028** despite never winning a seat at the ballot.
    `election_year` blank (pure appointee).

## The crossover vote-bound de-smear — now handled by the tenure-window clamp (override RETIRED 2026-07-11)

`roster_lib.clamp_vote_bounds()` assigns `first_vote`/`last_vote` as the earliest/latest observed
Council vote **within each tenure's own `[start_date, end_date)` window** (blank if none). For
**Worel**, her person-level `cities.db` max `last_seen` is **2024-08-22** — but that date is her
**MAYORAL tie-break** (Res 16-2024, `"Nay (Mayor tie-break)"`), NOT council service. Her real last
council-MEMBER vote is **2021-12-16** (the last vote before she became mayor 2022-01-06). Her AL-A1
council tenure runs `[2020-01-09, 2022-01-06)`, so the clamp **excludes the 2024-08-22 tie-break
automatically** and yields `last_vote=2021-12-16` — the exact Ogden-Nadolski defect class, now fixed
**structurally with NO override** (verified: the clamp alone reproduces 2021-12-16). Her MAYOR row is
separately emptied by `non_voting_mayor`. **`roster_overrides.csv` is therefore RETIRED (0 data rows,
header-only) as of 2026-07-11** — its former sole row (this Worel de-smear) is no longer needed.
Dickey's council bounds (2022-01-27..2025-12-18) were always genuine council votes and need no
correction — his one mayoral tie-break (2026-01-15, appointing Miller) was an appointment selection,
never recorded as a legislative roll-call, so there was nothing to smear.

## Mayor is NON-VOTING (determination + handling)

Park City's mayor **presides and does not vote except to break a tie** (confirmed in the city
CLAUDE.md + `meeting_minutes/CLAUDE.md`). There are **exactly 2 mayoral tie-break VOTES** in the
record, both `"Nay (Mayor tie-break)"`, both 2-3 Fail: **Beerman 2020-06-25** (Ord 2020-31) and
**Worel-as-mayor 2024-08-22** (Res 16-2024) — these are the mayor's ONLY `cities.db` Council-body
votes. (A third mayoral tie-break, **Dickey 2026-01-15**, selected Molly Miller for appointment
— not a legislative roll-call, so it is absent from `all_votes.csv`.) Handling: `non_voting_mayor=
True` **empties every MAYOR row's vote bounds** and `validate()` enforces it, so no tie-break
smears a member span across a mayoralty. `andy_beerman` (a pure mayor whose sole db Council row
is his 2020-06-25 tie-break) is additionally **left out of `DB_KEY`**; the two crossovers
(`nann_worel`, `ryan_dickey`) stay in `DB_KEY` for their real council tenures.

## Honest gaps (recorded, not filled)

- **Exact term-commencement days.** Elected-term starts use the first recovered January meeting
  (matches cities.db `first_seen`); Park City rarely prints an exact oath date. The one
  separately-documented swearing (Dickey-mayor, 2026-01-05 "on Monday") is used verbatim. No
  date is fabricated; each is tied to a recovered meeting or a quoted event.
- **Pre-floor 2017-cycle terms (`medium`).** Joyce (AL-B1), Henney (AL-B2), and Beerman's Mayor
  term were seated at the 2020 floor; their 2017 election / 2018-01 term-start is inferred from
  the Cohort-B / mayoral 4-year stagger, not asserted as fact.
- **Within-cohort seat numbers.** A2/A3 (Gerber/Doilney → Parigian/Ciraco) and the pre-floor
  B1/B2 (Joyce/Henney) are labelling choices where same-cohort members arrived/departed together
  — the **person-tenures are exact**; the seat *number* between paired arrivals is not
  source-attested. AL-A1 (via the crossover chain) and AL-B1 (via Toly's continuity) are anchored.
- **No unidentified appointee.** Both mid-term appointees resolved to named persons from the
  minutes → **no `UNKNOWN`/`low` rows**.

## `district_versions.csv` — DEGENERATE for Park City (at-large)

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Park City's council + mayor are elected **entirely AT-LARGE — no
wards/districts, no numbered seats** — so this table holds exactly **one** row
(`district_id=At-Large`, whole city, open-ended). `geometry_ref` = `geo/city_boundary.geojson`
(the Summit+Wasatch city-limits polygon). The sub-district address→representative join correctly
degenerates to whole-city → all sitting members + mayor (`geo/address_to_district.py` resolves
only inside/outside city limits).

## How to query

```bash
python3 roster/build_roster.py --demo   # (a) current (b) as-of the 2026 VACANT (b') as-of the 2022 VACANT (c) Worel crossover (d) address→rep
python3 roster/build_roster.py --check  # regenerate + validations only
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Mayor + 5:
  Miller, Parigian, Ciraco, Toly, Zegarra + Mayor Dickey).
- **As of a past date** — `roster_as_of(date, body)`: e.g. **2026-01-12** and **2022-01-13** each
  show the AL-A1 **VACANT** interval; **2023-07-01** shows Dickey as a *councilmember* + Worel as
  *mayor* (the crossovers in their council/mayor phases).
- **Address + date → representative** — `representatives_for_address(address, date)`: reduces to
  At-Large → all sitting members + mayor on that date (degenerate, like the other at-large cities).

## What Park City adds as the tenth city

The first fleet city with **two council→mayor crossovers on ONE seat**, each a **mid-term
vacancy filled by appointment** (AL-A1 = Worel→[VACANT]→Dickey-appointed→Dickey-elected→
[VACANT]→Miller-appointed) — two VACANT intervals and an appointment twice on the same seat. It
also exercises the crossover **vote-bound de-smear via the tenure-window clamp** (Worel's mayoral
tie-break excluded from her AL-A1 council bounds — override retired 2026-07-11), an
**appointed-after-losing-the-primary** twist (Miller), a **non-voting mayor
with a documented tie-break under each of two mayors** (Beerman, Worel), and a fully-on-disk
reconciliation with honest provenance/confidence + pre-floor inference. **Federation into the
root `cities.db` is NOT done here** (it would require touching the shared build) — see the
Nephi/Lehi/Ogden roster CLAUDE.md federation notes.
