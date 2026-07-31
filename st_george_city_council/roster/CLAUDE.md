# roster/ — St. George rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each St. George City Council +
Mayor seat over time** as dated intervals, reconciled from multiple sources with
**per-row provenance and confidence**. Answers: *who was on the council on date X?*, *who
is serving now?*, *who represents this address on this date?* — none of which the flat
CSVs can answer.

St. George is a **backlog city** built on the mature shared library
(`../../scripts/roster_lib.py`). It is **AT-LARGE** (no geographic districts — like
Lehi/Logan/Nephi/Vineyard → `district_versions` is one degenerate whole-city row) with a
**NON-VOTING mayor** (presides; votes only to break a tie — like Lehi/Logan/Nephi/Provo,
UNLIKE Vineyard/Orem/Millcreek → the `MAYOR` rows carry no vote bounds). It is the
richest at-large city yet on the crossover/vacancy path: **TWO councilmember→mayor
crossovers**, each spawning a mid-term appointment, **plus** a mayoral resignation that
created a third (mayoral) vacancy.

> **Disambiguation:** St. George, **UTAH** (Washington County) — entirely at-large. NOT
> St. George, Louisiana (which has a district-based council).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates the two CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**21 rows: 18 person-tenures + 3 VACANT intervals**). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for St. George** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer. Applied **last**, wins ties. **0 data rows** (RETIRED 2026-07-11 — the former Randall council vote-bound de-smear is now reproduced by the tenure-window clamp). |

**Never hand-edit the two generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-cohort seat label. St. George = **Mayor + 5 at-large council
  seats**, elected as a single multi-winner **"Vote For N"** field (2019=3, 2021=2, 2023=3,
  2025=2 seats):
  - `AL-A1`, `AL-A2`, `AL-A3` — **Cohort A** (3 seats; elected 2019 / 2023 / 2027; terms
    Jan-2020…, Jan-2024…). `AL-A1` is **anchored** by the Hughes→Anderson vacancy chain;
    `AL-A2` by Larkin's continuity; `AL-A3` by the McArthur→Kemp handoff.
  - `AL-B1`, `AL-B2` — **Cohort B** (2 seats; elected 2021 / 2025; terms Jan-2022…,
    Jan-2026…). `AL-B1` is **anchored** by the Randall→Curtis vacancy chain.
  - `MAYOR` — single seat (elected 2021 / 2025; **no mayoral race in 2019 or 2023**).
  Within-cohort seat **numbers** are a stable labelling of the person-chain; where two
  same-cohort newcomers arrive together the split is a **labelling choice** (flagged in
  `note`) — the person-tenures are exact. Labelling choices here: the 2019 pair
  McArthur(A3)/Larkin(A2), and the 2021 cohort-B pair Larsen(B1)/Tanner(B2) (both seats
  were on the same 2021 ballot; Larsen is assigned to the Randall/Curtis-anchored B1).
- **`district`** = `At-Large` on every row (FK into `district_versions`; no geographic
  districts, no per-seat contests — the top-N vote-getters win the N open seats).
- **`person_key`** = `first_last`. St. George has **no shared surnames** among
  council/mayor members, so surname keys suffice and **no disambiguators** are needed.
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained: a tenure ends when the next tenure on the same `seat_id` begins, or at
  a documented `vacate_date` (which then inserts a VACANT interval).
- **`start_event`** ∈ {elected, reelected, appointed, vacated (VACANT rows)}.
  **`end_event`** ∈ {reelected, did-not-run, lost, resigned, became-mayor, elected (the
  appointed-Mayor→elected-Mayor transition), serving, filled (VACANT rows)}.
  `did-not-run` = McArthur (advanced the 2023 primary but withdrew before the general).
  `lost` = ran and lost (Smethurst 2021 primary; Curtis 2021 general; Randall 2025 mayor).
  `resigned` = Pike (left the mayoralty mid-term). `became-mayor` = the two crossover
  councilmembers (Randall AL-B1 → Mayor 2021; Hughes AL-A1 → Mayor 2026).
- **`election_year`** — the cycle that seated the tenure (**blank for a pure appointment** —
  Curtis, Anderson, and Randall's *appointed* Mayor row).
- **`first_vote` / `last_vote`** — the earliest/latest observed **Council-body** member vote in
  `cities.db` (`city='st_george'`) that falls **within each tenure's own `[start, end)` window**
  (the tenure-window clamp — blank if the window holds no observed vote). Full named roll calls →
  rich for councilmembers. Because the bounds are clamped per tenure, a councilmember→mayor
  person's council tenure never shows a Mayor-era vote: **Randall's AL-B1 council `last_vote` is
  2021-01-19**, not her 2025-02-20 Mayor-era tie-break. **The `MAYOR` rows carry NO vote bounds** —
  the mayor is non-voting (see below); `jon_pike` is left out of the db-key map and the two
  councilmember→mayor people (Randall, Hughes) get empty MAYOR rows via the `non_voting_mayor` flag.
- **`sources`** — semicolon list. **Every row carries a non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result or minutes-documented swearing-in / appointment
  / resignation / vacancy) · `medium` (pre-floor 2017-cycle term, term-start inferred from
  the stagger; OR the MAYOR VACANT whose exact start is inferred within a documented bracket)
  · `low` (unknown — **none here**).

**Counts: 21 rows — 17 high / 4 medium / 0 low; 3 VACANT intervals.** 0 overlapping tenures
per seat. The 4 `medium` rows: the three **pre-floor 2017-cycle** holders — Randall (AL-B1),
Smethurst (AL-B2), Pike (MAYOR), all seated at the 2020 data floor with 2017 election /
2018-01 term-start inferred from the 4-year stagger — plus the **MAYOR VACANT** (its exact
start date is inferred; see below).

## The mayor is NON-VOTING (determination — with quoted basis)

St. George runs a **council-manager** form; the mayor **presides and does not vote except to
break a tie**. Evidence (three independent lines):

1. **A quoted roll call excludes the mayor.** 2023-06-15 regular meeting (Randall presiding):

   > *"Mayor Randall called for a vote, as follows: Councilmember Hughes – aye;
   > Councilmember McArthur – aye; Councilmember Larkin – aye; Councilmember Larsen – aye;
   > Councilmember Tanner – aye. The vote was unanimous and the motion carried."*

   Only the **five councilmembers** are polled; the mayor is never in the aye/nay list. This
   is the universal pattern ("**Mayor X called for a vote**" then only councilmembers). Same
   at the 2021-02-10 Curtis appointment: *"Mayor Randall called for a roll call vote"* of the
   **four** sitting councilmembers (her old seat then vacant), herself not among them.
2. **Presiding-mayor vote counts are ~zero.** `cities.db` shows **Jon Pike** (presided all of
   2020) with **exactly one** Council-body vote in 2020 (2020-04-16 — a tie-break), and
   **Michele Randall as Mayor** with **zero** council votes 2022-2024 and a **single** 3-2
   tie-break on 2025-02-20 (her only Mayor-era vote).
3. **Randall's large 2020 vote count was as a COUNCILMEMBER**, not mayor: her 243 votes in
   2020 + 3 in early 2021 predate her 2021-01-21 mayoral appointment.

**Handling:** `non_voting_mayor=True`. Every `MAYOR` row carries **empty** `first_vote`/
`last_vote`, and `validate()` enforces it. `jon_pike` (mayor-only) is left **out of `DB_KEY`**.
The two councilmember→mayor people **are** in `DB_KEY` for their **council** tenures; the
tenure-window clamp confines each council tenure's bounds to its own `[start, end)` window, so
Randall's 2025-02-20 Mayor-era tie-break never lands on her AL-B1 council `last_vote` (see the
retired-override note below).

## The three VACANT / mid-term-appointment chains (spot-checked, fully on-disk)

### 1. AL-A1 — Hughes → [VACANT] → Anderson (2026; councilmember→mayor crossover)
Jimmie Hughes (elected Council 2019 rank1, re-elected 2023 to a term running to Jan-2028)
**ran for MAYOR in 2025 and WON** (12,334 / 55.58%, beating incumbent Randall), taking
office in **January 2026** and vacating his AL-A1 council seat two years early. The
**2026-01-08** regular meeting PRESENT list reads *"Mayor Jimmie Hughes"* + **only four**
councilmembers (Larkin/Larsen/Tanner/Kemp) — the seat is empty. At the **2026-01-22** special
meeting the Council interviewed **15 applicants**, appointed and swore in **Austin F.
Anderson** (*"SWEARING IN OF NEW CITY COUNCILMEMBER — swearing in of Austin Anderson"*).
→ Hughes ends `became-mayor` at `vacate_date=2026-01-08`, an explicit **VACANT** interval
spans 2026-01-08…2026-01-22, then Anderson's **`appointed`** tenure begins. **High** — the
crossover, the empty council, and the appointment are all in recovered minutes; the window
contains **no** un-recovered date.

> **Person identity (PC↔Council), verified 2026-07-19:** the appointed councilmember
> **Austin F. Anderson** is the **SAME person** who chaired the **Planning Commission**
> 2021–Jan 2026. Evidence: the 2026-01-22 minutes list "Applicant Austin F Anderson" among
> the 15 applicants and swear him in; and he vanishes from the PC roster from **2026-02**
> (no more `Chair Anderson`) exactly as he joins the Council — a clean body-to-body move,
> not a name collision. The person layer correctly links his PC-Chair record and his
> Council tenure (both `Austin Anderson`). (Note: on the PC there is ALSO a *Brandon*
> Anderson, a Member since Dec 2023 — a genuinely different person; see the PC extractor's
> attendance-based Anderson disambiguation.) (The only unknown is Hughes's exact mayoral oath date,
not printed for the 2026 term — anchored to the first documented meeting he presides as
Mayor.)

### 2. AL-B1 — Randall → [VACANT] → Curtis (2021; the FIRST councilmember→mayor crossover)
Michele Randall (a pre-floor cohort-B councilmember) was **appointed the first female Mayor
of St. George on 2021-01-21** (*"Michele Randall, sworn in and appointed as the new Mayor on
January 21, 2021 at 5:00 p.m."*) after Mayor Pike's resignation, vacating her council seat
(term to Jan-2022). At the **2021-02-10** special meeting the Council appointed **Vardell
Curtis** *"for the position of City Council to fill Mayor Randall's remaining term"* (first
seated/voting 2021-02-11). → Randall ends `became-mayor` at `vacate_date=2021-01-21` (her
last council vote is 2021-01-19), a **VACANT** interval spans 2021-01-21…2021-02-11, then
Curtis's **`appointed`** tenure begins. **High.** Curtis then ran for a full term in 2021 and
**lost the general** (rank4 of 4) → served only to Jan-2022; Larsen won the seat.

### 3. MAYOR — Pike → [VACANT] → Randall (2021; mayoral resignation)
Jon Pike **resigned the mayoralty** in mid-January 2021 (to become Utah Insurance
Commissioner). He presided his last documented meeting **2021-01-14**; by the **2021-01-19**
special meeting Mayor Pro Tem Hughes notes he has served *"since Mayor Pike's recent
resignation"* and the sole agenda item is interviewing applicants for *"the vacant Mayor
position."* → Pike ends `resigned` at `vacate_date=2021-01-15`, a **VACANT** interval spans
2021-01-15…2021-01-21, then Randall's **`appointed`** Mayor tenure begins. **Medium** — the
*fact* of the vacancy is fully documented, but Pike's **exact resignation-effective date is
not printed**; it is inferred within the recovered-minutes bracket 2021-01-14 (presiding) …
2021-01-19 (documented-vacant), so `vacate_confidence=medium` and the VACANT row inherits it.

## The Randall vote-bound clamp (roster_overrides.csv RETIRED 2026-07-11)

`michele_randall` is a councilmember→mayor person. `cities.db` carries a Mayor-era 3-2 tie-break
on **2025-02-20**, which the OLD person-level min/max would have smeared onto her 2018–2021 AL-B1
**council** tenure's `last_vote`. The **tenure-window clamp** (landed 2026-07-11 in
`roster_lib.clamp_vote_bounds`) confines each tenure's `first_vote`/`last_vote` to its own
`[start, end)` window; the 2025-02-20 tie-break falls outside her AL-B1 window
`[2018-01-01, 2021-01-21)`, so the clamp alone yields her **true last council vote 2021-01-19**
(sworn Mayor 2021-01-21) with **no override**. Her `first_vote` (2020-01-06) is likewise correct.
The former de-smear row in `roster_overrides.csv` is therefore **RETIRED** (the file is now
header-only, 0 data rows) — verified: the clamp reproduces `last_vote=2021-01-19` on its own. (This
is the fleet-wide retirement that also dropped Park City's Worel de-smear override.) Hughes, the
other crossover, needs no correction either: his last council vote 2025-12-18 is legitimate — he
was a councilmember right up to becoming Mayor in Jan-2026, and has cast no Mayor-era tie-breaks yet.

## Other transitions (spot-checked against source minutes)

- **2020-01-06 SWEARING IN OF ELECTED OFFICIALS** — *"Jimmie Hughes, Gregg McArthur, and
  Dannielle Larkin were sworn in"* (the 2019 cohort-A winners). The same present-list shows
  Randall & Smethurst **already seated and NOT sworn** → they are continuing 2017-cycle
  (cohort-B) incumbents, confirming the pre-floor `medium` inference.
- **2024-01-02 SWEARING IN** — Councilmembers **Kemp, Hughes, Larkin** (2023 winners).
  McArthur advanced the 2023 primary (rank6) but **withdrew before the general** (the general
  field was Kemp/Hughes/Larkin/Bennett/Smith) → `did-not-run`, seat won by Kemp.
- **2022-01-03 SWEARING IN** — *"Michelle Tanner, Natalie Larsen, and Michele Randall were
  sworn in"* (the 2021 winners: Larsen/Tanner to Council, Randall to her **elected** Mayor
  term after her 2021-01 appointment).
- **2026-01-08** — first meeting of the new term: Mayor Hughes + Larkin/Larsen/Tanner/Kemp
  (AL-A1 vacant until Anderson on 2026-01-22).

## Honest gaps (recorded, not filled)

- **Pike's exact resignation-effective date** — not printed; bracketed 2021-01-14 (last
  presiding) … 2021-01-19 (documented-vacant). `vacate_date=2021-01-15` inferred →
  `medium` on the MAYOR VACANT. Patch via `roster_overrides.csv` if it surfaces.
- **The 2026-term oath dates** (Mayor Hughes; reelected Larsen/Tanner) — the recovered 2026
  minutes carry no swearing-in line; the new-term rows are anchored to the first documented
  meeting where the new configuration appears (2026-01-08). The statutory term start is the
  first Monday of January (2026-01-05).
- **Pre-floor 2017-cycle terms (`medium`)** — Randall (AL-B1), Smethurst (AL-B2), Pike
  (MAYOR): seated at the 2020 floor, 2017 election / 2018-01 term-start inferred from the
  4-year stagger (the 2020-01-06 swearing-in list positively confirms Randall/Smethurst were
  continuing incumbents, not 2019 arrivals).
- **Within-cohort seat numbers** — McArthur(A3)/Larkin(A2) and Larsen(B1)/Tanner(B2) where
  same-cohort members arrived together are **labelling choices**; the person-tenures are
  exact. AL-A1 (Hughes→Anderson) and AL-B1 (Randall→Curtis) are anchored by their vacancy
  chains; AL-A2 by Larkin's continuity; AL-A3 by the McArthur→Kemp handoff.
- **No unidentified appointee.** Both council appointees (Curtis, Anderson) resolved to named
  persons from the minutes → **no `UNKNOWN`/`low` rows**.
- **`minutes_unrecovered.csv`** holds one date (2025-10-09, a city mis-upload) — it does NOT
  overlap any VACANT window, so the library's gap-detector does not fire.

## `district_versions.csv` — DEGENERATE for St. George (at-large)

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. St. George's council + mayor are elected **entirely
AT-LARGE — no wards/districts, no per-seat contests** — so this table holds exactly **one**
row (`district_id=At-Large`, whole city, open-ended). `geometry_ref` =
`geo/city_limits.geojson` (the existing city-limits polygon). **Note:** St. George's city
LIMITS change over time by **annexation** (a fast-growth Washington County city); the row
points at the **current** limits, and prior annexation-versioned boundaries are **not on disk
and not fabricated**. The sub-district address→representative join correctly degenerates to
whole-city → all sitting members + mayor.

## How to query

```bash
python3 roster/build_roster.py --demo   # (a) current  (b) as-of the 2026 AL-A1 VACANT  (b') as-of 2021 (Randall appt-Mayor + AL-B1 VACANT)  (c) address→rep
python3 roster/build_roster.py --check  # regenerate + validations only
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Mayor
  Hughes + Anderson/Larkin/Kemp/Larsen/Tanner).
- **As of a past date** — `roster_as_of(date, body)`: **2026-01-15** shows the AL-A1 **VACANT**
  interval; **2021-02-01** shows the AL-B1 **VACANT** interval + Randall as appointed Mayor.
- **Address + date → representative** — `representatives_for_address(address, date)`:
  correctly reduces to At-Large → all sitting members + mayor on that date (degenerate). On a
  date inside a VACANT window it returns the `VACANT` placeholder alongside the sitting
  members.

## What St. George adds

The most crossover-dense at-large city so far: **two councilmember→mayor crossovers** that
each triggered a mid-term council appointment (Randall→Curtis 2021; Hughes→Anderson 2026),
**plus** a mayoral resignation that created a third, mayoral, vacancy (Pike→Randall 2021) —
all **fully on-disk** and quote-verified. It exercises the **non-voting-mayor flag** for a
council-manager city, the **appointed-then-elected** Mayor path (Randall), and the
**tenure-window vote-bound clamp** — which retired the former Randall council `last_vote`
de-smear override on 2026-07-11 (the clamp now reproduces `last_vote=2021-01-19` structurally).
**Federation into the root `cities.db` is NOT done here** (it would require touching the shared build) — see the
Lehi/Nephi roster CLAUDE.md federation notes.
