# roster/ — Lehi rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Lehi City Council + Mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row provenance
and confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who
represents this address on this date?* — none of which the flat CSVs can answer.

Lehi is the **first BACKLOG city** built on the now-mature shared library
(`../../scripts/roster_lib.py`), after the four prototypes (Nephi, Provo, Vineyard, SLC).
It is **AT-LARGE** (no geographic districts — like Nephi/Vineyard → `district_versions` is
one degenerate whole-city row) with a **NON-VOTING mayor** (votes only to break a tie — like
Nephi/Provo, UNLIKE Vineyard's voting mayor → the `MAYOR` rows carry no vote bounds). It
exercises the **VACANT/appointment path once**: councilmember Paige Albrecht resigned
mid-term (Dec-2025) and Emily Lockhart was appointed to fill her seat.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates the two CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**17 rows: 16 person-tenures + 1 VACANT interval**). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for Lehi** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit the two generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-cohort seat label. Lehi = **Mayor + 5 at-large council seats**:
  - `AL-A1`, `AL-A2`, `AL-A3` — **Cohort A** (3 seats; elected 2019 / 2023 / 2027; terms
    Jan-2020…, Jan-2024…). `AL-A1` is **anchored** by the Albrecht→Lockhart vacancy chain.
  - `AL-B1`, `AL-B2` — **Cohort B** (2 seats; elected 2017 / 2021 / 2025; terms Jan-2018…,
    Jan-2022…, Jan-2026…). Anchored by the two DISTINCT continuous holders Condie / Hancock.
  - `MAYOR` — single seat (elected 2017 / 2021 / 2025).
  Within-cohort seat **numbers** are a stable labelling of the person-chain; where two
  same-cohort newcomers arrive together the split is a **labelling choice** (flagged in
  `note`) — the person-tenures are exact. Labelling choices here: the 2019 pair
  Southwick(A2)/Koivisto(A3), their 2024 successors Stallings(A2)/Newall(A3), and the 2026
  cohort-B pair Harrison(B1)/Freeman(B2).
- **`district`** = `At-Large` on every row (FK into `district_versions`; Lehi has no
  geographic districts, no numbered seats — the top-N vote-getters win the N open seats).
- **`person_key`** = `first_last`. Lehi has **no shared surnames** among council/mayor
  members, so surname keys suffice and **no disambiguators** are needed (do NOT key on the
  two shared first names — Paul Hancock vs Paul Binns; key on surname).
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained: a tenure ends when the next tenure on the same `seat_id` begins, or at
  a documented `vacate_date` (which then inserts a VACANT interval).
- **`start_event`** ∈ {elected, reelected, appointed, vacated (VACANT rows)}.
  **`end_event`** ∈ {reelected, did-not-run, lost, resigned, serving, filled (VACANT rows)}.
  `did-not-run` = a full-term member not a candidate in the next cycle (Southwick, Koivisto;
  Condie, who ran for **mayor** instead; Johnson, who did not seek a third mayoral term).
  `lost` = ran for re-election and lost (Hancock, in the 2025 primary). `resigned` = the
  mid-term departure that created the vacancy (Albrecht — see below).
- **`election_year`** — the cycle that seated the tenure (**blank for a pure appointment** —
  Lockhart).
- **`first_vote` / `last_vote`** — the person's first/last observed **Council-body** member
  vote in `cities.db` (`role`, `city='lehi'`). Lehi has full named roll calls, so these are
  rich for councilmembers. **The `MAYOR` rows carry NO vote bounds** — Lehi's mayor is
  non-voting (see below), so `mark_johnson` is deliberately left out of the db-key map and
  `paul_binns` has no db presence.
- **`sources`** — semicolon list (`election:YYYY …`, `appt:DATE (minutes …)`, `votes:…`,
  `minutes:DATE …`). **Every row carries a non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result or minutes-documented swearing-in / appointment
  / vacancy) · `medium` (pre-floor 2017-cycle term, term-start inferred from the stagger) ·
  `low` (unknown — **none here**).

Counts: **17 rows — 14 high / 3 medium / 0 low; 1 VACANT interval.** 0 overlapping tenures
per seat. The 3 `medium` rows are the pre-floor 2017-cycle holders: **Condie** (AL-B1),
**Hancock** (AL-B2), and **Johnson**'s first Mayor term — all seated at the 2020 data floor,
their 2017 election / 2018-01 term-start inferred from the 4-year cohort stagger.

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/lehi_results_by_candidate.csv`, municipal **general**
   winners only (`keep_election_row` drops the 2023 & 2025 **primary** advancer rows — so
   e.g. the 2023-primary advancers Kunze/Roberts/Glade and the 2025-primary advancers
   Lockhart/Peterson are not mis-counted as seat winners). Both the RCV years (2021/2023) and
   the plurality years (2019/2025) map to a seat via office=body (at-large). UPPER-CASE names
   normalized to `person_key`. The script cross-checks that **every** general winner maps to
   an `elected`/`reelected`/`became-mayor` tenure (prints to stderr on drift — currently clean).
2. **Vote / attendance bounds** — `cities.db` `role` (`city='lehi'`, `body='Council'`): sets
   `first_vote`/`last_vote` and would surface any off-cycle appointee (a voter with no
   election win). Lehi's one appointee (Lockhart) has db `first_seen 2026-01-06`, AFTER her
   2025-12-22 oath — because the 2025-12-22 appointment vote was cast by Albrecht (the
   retained "Voting Member for the Vacancy"), not by Lockhart. No other off-cycle voter.
3. **Swearing-in / appointment / vacancy events** — read from `meeting_minutes/minutes/**`
   and encoded in `TENURES` (Lehi records these in narrative prose + resolutions, not as a
   machine motion type). These date the mid-term arrival and the biennial turnovers precisely.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties (0 rows now).

Then `end_date` is chained per seat, the **VACANT-interval** rule runs, and the table is
validated (no overlaps; sources+confidence present; the `vacate_confidence` invariant + the
un-recovered-minutes gap detector). A failure aborts the write. Lehi has **no
`minutes_unrecovered.csv`**, so the gap detector sees an empty set (nothing to trip on).

## The VACANT / mid-term-appointment chain (spot-checked, fully on-disk)

- **AL-A1 — Albrecht → [VACANT] → Lockhart.** Paige Albrecht (elected 2019 rank1, re-elected
  2023 to a term running to Jan-2028) **ran for MAYOR in 2025 and lost** the general to Binns,
  then **resigned her council seat** mid-term in Dec-2025. She is present and voting through
  **2025-12-02** (her last recorded vote); by the **2025-12-16** regular meeting the council
  operates with **4 members** and the agenda is *"Resolution #2025-95 adopting procedures …
  for filling the current vacancy … due to the resignation of Paige Albrecht."* At the
  **2025-12-22** special session the council interviewed applicants and passed **Resolution
  #2025-103** *"appointing Emily Lockhart to the Lehi City Council"* (moved Condie / 2nd
  Hancock, unanimous), and *"The Oath of Office was administered to Emily Lockhart after the
  adjournment."* → Albrecht ends `resigned` at the vacate date (**2025-12-02**, her last
  recorded vote), an explicit **VACANT** interval spans 2025-12-02…2025-12-22, then Lockhart's
  **`appointed`** tenure begins at her 2025-12-22 oath.
  - **Confidence high (not medium like Vineyard's Cameron):** the resignation, the vacant
    council, and the successor's appointment are ALL in **recovered** minutes — this is NOT a
    gap-bounded case. The one thing the minutes don't print is the **exact effective date of
    the resignation letter** (the 2026-01-13 procedures review notes it *"first go[ing] to the
    mayor and then to the council"* in December); it is bracketed by two recovered meetings
    (present+voting 2025-12-02 → documented-vacant 2025-12-16). If that exact date surfaces,
    drop it into `roster_overrides.csv`.
  - **The Lockhart twist:** she **ran in the 2025 council general and LOST** (rank3 / first
    loser), then was **appointed to Albrecht's DIFFERENT (vacated cohort-A) seat** — so she
    serves to **Jan-2028** despite losing the seat she campaigned for. (`keep_election_row`
    correctly drops her 2025-primary `is_winner` advancer row; she is `is_winner=False` in the
    general, so she never appears as an elected winner — she is a pure appointee, `election_year`
    blank.)

## Other key transitions (spot-checked against source minutes)

- **Continuing 2017-cycle incumbents (Condie, Hancock, Johnson) — QUOTED.** The **2020-01-14**
  minutes' *"Swearing In Ceremony for City Council Members"* reads: *"Councilors Southwick,
  Albrecht, and Koivisto were sworn in"* — **only the three 2019 winners**. Condie, Hancock,
  and Mayor Johnson head the same present-list but were **NOT** sworn that day, confirming they
  were **continuing incumbents** (cohort-B / mayor elected 2017, pre-floor) rather than 2019
  arrivals. All three were then re-elected 2021 and sworn together: **2022-01-04** *"Swearing In
  Ceremony for Mayor Johnson, Councilor Condie and Councilor Hancock."*
- **The 2024 cohort-A turnover — QUOTED.** **2024-01-09** *"Swearing-In Ceremony for Councilors
  Paige Albrecht, Heather Newall, and Michelle Stallings"* — Albrecht re-elected (continuous
  AL-A1), Newall + Stallings new (replacing Southwick + Koivisto, neither a 2023 candidate).
- **The 2026 cohort-B + mayor turnover.** **2026-01-06** present list is *"Paul Binns, Mayor;
  Rachel Freeman; James Harrison; Emily Lockhart; Heather Newall; Michelle Stallings"* — the
  current roster. New that cycle: Binns (Mayor, replacing Johnson, who did not seek a third
  term), Harrison + Freeman (the 2025 council winners, replacing Condie — who ran for mayor and
  lost the primary — and Hancock — who ran for council and lost the primary). Lockhart continues
  (appointed just before); Newall + Stallings continue.

## Mayor is NON-VOTING (determination + handling)

Lehi's mayor **presides and does not vote except to break a tie** (confirmed in
`meeting_minutes/CLAUDE.md`: the extractor keeps the mayor OUT of the voting roster; exactly
**4 tie-breaks** by Mayor Johnson in the whole corpus — 2022-06-14, 2023-04-11, 2024-03-26,
2025-12-16). So Lehi is like **Nephi/Provo** (non-voting mayor), **not** Vineyard (voting
mayor). Handling: `mark_johnson` is **deliberately omitted from `DB_KEY`**, so the 4 tie-break
rows in `cities.db` are NOT folded into the `MAYOR` rows' `first_vote`/`last_vote` (`non_voting_mayor=True`
already blanks every MAYOR row, and the per-tenure vote clamp would in any case confine each
tie-break to its own term's `[start,end)` window rather than span both of Johnson's tenures). The 4
tie-breaks are documented in the MAYOR-row `note` instead. `paul_binns` has no db presence
(0 votes → no tie-breaks yet). Every `MAYOR` row therefore has empty vote bounds — correct.

## Honest gaps (recorded, not filled)

- **Exact Albrecht resignation-letter date** — not printed in the recovered minutes; bracketed
  2025-12-02 (last recorded vote) … 2025-12-16 (first documented-vacant meeting). `vacate_date`
  uses the last-recorded-vote convention (2025-12-02). High on the fact + window; the precise
  day within the bracket is the only unknown. Patch via `roster_overrides.csv` if it surfaces.
- **Pre-floor 2017-cycle terms (`medium`).** Condie (AL-B1), Hancock (AL-B2), and Johnson's
  first Mayor term were seated at the 2020 floor; their 2017 election / 2018-01 term-start is
  inferred from the Cohort-B / mayoral 4-year stagger, not asserted as fact. (The 2020-01-14
  swearing-in list positively confirms they were continuing incumbents, not 2019 arrivals.)
- **Within-cohort seat numbers.** A2/A3 (Southwick/Koivisto → Stallings/Newall) and B1/B2
  (Harrison/Freeman in 2026) are labelling choices where same-cohort members arrived together —
  the **person-tenures are exact**; the seat *number* between paired arrivals is not
  source-attested. AL-A1 and (via the two distinct continuous holders) AL-B1/AL-B2 are anchored.
- **No unidentified appointee.** The one mid-term arrival resolved to a named person from the
  minutes → **no `UNKNOWN`/`low` rows**.

## `district_versions.csv` — DEGENERATE for Lehi (at-large)

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Lehi's council + mayor are elected **entirely AT-LARGE — no
wards/districts, no numbered seats** — so this table holds exactly **one** row
(`district_id=At-Large`, whole city, open-ended). `geometry_ref` = `geo/city_boundary.geojson`
(the existing city-limits polygon). **Note:** Lehi's city LIMITS change over time by
**annexation** (a fast-growth "Silicon Slopes" city); the row points at the **current** limits,
and prior annexation-versioned boundaries are **not on disk and not fabricated**. The
sub-district address→representative join is validated on a real district city (Provo/SLC); here
it correctly degenerates to whole-city → all sitting members + mayor.

## How to query

```bash
python3 roster/build_roster.py --demo   # (a) current  (b) as-of the VACANT window  (b') as-of 2022  (c) address→rep
python3 roster/build_roster.py --check  # regenerate + validations only
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Mayor + 5).
- **As of a past date** — `roster_as_of(date, body)`: e.g. **2025-12-18** shows the AL-A1
  **VACANT** interval; **2022-07-01** shows the 2019 cohort-A + re-elected cohort-B + Johnson.
- **Address + date → representative** — `representatives_for_address(address, date)`: for Lehi
  this **correctly reduces to At-Large → all sitting members + mayor** on that date (degenerate,
  like Nephi/Vineyard). On a date inside the VACANT window it honestly returns the `VACANT`
  placeholder alongside the sitting members.

## What Lehi adds as the first backlog city

A clean re-use of the shared library on a mid-size, well-documented at-large city: a
**fully-on-disk** mid-term resignation→appointment chain (contrast Vineyard's gap-bounded
Cameron case), an **appointed-after-losing** twist (Lockhart lost the 2025 general, then was
appointed to a different vacated seat), a **council-member-runs-for-mayor-and-loses** departure
(Condie), a **ran-for-re-election-and-lost-the-primary** departure (Hancock), positive
minutes-quoted confirmation of pre-floor incumbency (the 2020-01-14 swearing-in list names only
the 2019 winners), and a **non-voting mayor** handled by omission from the db-key map. It
shares the harder-to-see half with the prototypes — multi-source tenure reconciliation with
honest provenance/confidence and pre-floor inference. **Federation into the root `cities.db` is
NOT done here** (it would require touching the shared build) — see the Nephi/Vineyard roster
CLAUDE.md federation notes.
