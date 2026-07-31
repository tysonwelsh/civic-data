# St. George roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `roster/council_terms.csv`, `roster_overrides.csv`, `district_versions.csv`
against `election_results/`, `meeting_minutes/minutes/**`, root `cities.db`.
**Method:** ground-truth every VACANT chain, both crossovers, the resignation-succession,
the Randall override, the non-voting-mayor claim, and the structural invariants to source.
**Verdict:** structurally sound; **1 CONFIRMED DEFECT** (the Pike→VACANT mayoral bracket).

---

## (A) CONFIRMED DEFECTS

### DEFECT-1 — MEDIUM — Pike's mayoral-vacancy bracket is mis-dated (wrong lower bound; vacate_date lands past the first documented-vacant meeting)

**Rows:** `council_terms.csv` row 18 (`Mayor / MAYOR / Jon Pike`, `end_date=2021-01-15`)
and row 19 (`Mayor / MAYOR / VACANT`, `start_date=2021-01-15`).

**Claim under test (roster):**
- Row 18 `sources`: *"minutes:2021-01-14 (last documented meeting he presides as Mayor)"*.
- Row 19 `note` / roster CLAUDE.md: *"He presided his last documented meeting 2021-01-14
  … inferred within the recovered-minutes bracket 2021-01-14 (presiding) … 2021-01-19
  (documented-vacant)"*, `vacate_date=2021-01-15`.

**What the sources actually say:**

1. Pike is **absent** from the 2021-01-14 work meeting. Its PRESENT list is headed by the
   **Mayor Pro Tem**, not Pike:

   > `2021/2021-01-11/2021-01-14_city-council-work-meeting.md`, PRESENT:
   > *"Mayor Pro Tem Jimmie Hughes / Councilmember Michele Randall – via Zoom / …"*

   Every substantive presiding line in that file is **Hughes**, e.g. line 366:
   *"Mayor Pro Tem Hughes called for a vote, as follows:"*. (Line 33 *"Mayor Pike called
   the meeting to order"* is a **stale PMN template carryover** — the 2020–21 minutes are
   PMN-backfilled and needed inline header normalization; the authoritative PRESENT list and
   all voting lines contradict it. This line appears to be what misled the build.)

2. Pike's **actual** last documented meeting presiding as Mayor is **2020-12-17**:

   > `2020/2020-12-14/2020-12-17_city-council-regular-meeting.md`, PRESENT: *"Mayor Jon Pike …"*

   There are **no council meetings** between 2020-12-17 and 2021-01-14 (verified: the only
   Dec-2020/Jan-2021 minutes are 2020-12-10, 2020-12-17, 2021-01-14, 2021-01-19, 2021-01-21).

3. By 2021-01-14 the seat is already **documented-vacant** (Hughes serving as Pro Tem); the
   2021-01-19 special meeting only re-confirms it (*"since Mayor Pike's recent resignation …
   the vacant Mayor position"*).

**Why it's a defect:**
- The row-18 `sources` string asserts Pike **presided on 2021-01-14** — he did not (violates
  the cardinal rule against citing a source for something it doesn't say). The honest bracket
  is **[2020-12-17 last-presiding … 2021-01-14 first documented-vacant]**, not
  [2021-01-14 … 2021-01-19].
- `vacate_date=2021-01-15` is placed **one day AFTER** the first meeting (2021-01-14) at which
  the seat is already documented-vacant — i.e. the roster asserts Pike still held the mayoralty
  on a date when a Mayor Pro Tem was already presiding in his place. Internal inconsistency.

**Non-impact (bounding the severity):** no seat overlap is created (Pike end = VACANT start =
2021-01-15; VACANT end 2021-01-21 = Randall appt start); the `medium` confidence flag is
correctly applied for an un-printed exact date; no person is fabricated; the vacancy itself is
real and fully documented. The error is a ~4-week bracket whose lower bound and `vacate_date`
are mis-placed.

**Fix (via `roster_overrides.csv`, per derived-layer discipline — do NOT hand-edit the CSV):**
- Correct row 18 `Jon Pike` MAYOR `end_date` and row 19 `VACANT` `start_date` to a value
  inside the true bracket **[2020-12-17, 2021-01-14]** (e.g. `2021-01-01`, the statutory /
  first-Monday convention, or a bracket midpoint), keeping `confidence=medium`.
- Correct the row-18 `sources` text: replace *"minutes:2021-01-14 (last documented meeting he
  presides as Mayor)"* with *"minutes:2020-12-17 (last documented meeting presiding as Mayor);
  minutes:2021-01-14 (Mayor Pro Tem Hughes presiding — seat documented-vacant)"*.
- Correct the row-19 / CLAUDE.md bracket prose to **2020-12-17 (last presiding) … 2021-01-14
  (documented-vacant)**.

---

## (B) Calibration / honest-gap items (NOT defects — confirmed correct)

- **The Randall override is CORRECT and hides no service.** `cities.db` role row:
  `michele_randall` first_seen 2020-01-06, last_seen **2025-02-20**, n=248 — confirming
  `load_vote_bounds` would smear the 2025-02-20 **Mayor-era** vote onto her AL-B1 council
  tenure. Her genuine last **council-member** vote is **2021-01-19** (she voted in the
  2021-01-19 mayor-selection ballot as *"Councilmember Randall votes for Michele Randall"*,
  then was sworn Mayor 2021-01-21). 2025-02-20 is a real mayoral vote —
  `2025/2025-02-17/2025-02-20_…` line 141: *"Mayor Randall – aye"*. Override
  `last_vote → 2021-01-19` is exactly right. `first_vote` 2020-01-06 untouched, correct.

- **Hughes needs NO override — confirmed.** `cities.db`: Hughes's last council vote is
  **2025-12-18** (Aye); he has **zero** votes after (no 2026 rows — he became Mayor Jan-2026).
  Legitimate as-a-councilmember; no smear.

- **A spurious Randall vote exists in `cities.db` at 2021-02-25 (upstream extraction artifact,
  NOT a roster defect).** DB records a Randall council Aye on 2021-02-25, but the minutes show
  her **presiding as Mayor** and NOT in any aye list (only Hughes/McArthur/Larkin/Curtis vote;
  Smethurst excused) — it is a mis-parse of *"Mayor Randall called for a vote / suggested
  appointing …"*. Consequence: the roster CLAUDE.md's *"a single … tie-break on 2025-02-20
  (her only Mayor-era vote)"* slightly **undercounts the DB** (two Mayor-era rows exist, one
  genuine + one spurious). **No roster-data impact**: MAYOR rows are empty and the override
  already caps her council `last_vote` at 2021-01-19, below both. Flag for upstream `cities.db`
  extraction cleanup only.

- **Non-voting mayor — CONFIRMED from roll calls (three lines, all hold):**
  - `2023/2023-06-12/2023-06-15_…` lines 134–142 (Randall presiding) polls **only the five
    councilmembers** (Hughes/McArthur/Larkin/Larsen/Tanner); Mayor Randall not in the list —
    matches the CLAUDE.md quote verbatim.
  - 2021-02-10 Curtis appointment: *"Mayor Randall called for a roll call vote"* of the **four**
    sitting councilmembers (her old seat vacant), herself not among them.
  - 2026-01-22: newly-sworn Anderson moves Res. 2026-002R; *"Mayor Hughes called for a roll call
    vote"* — Larkin/Larsen/Tanner… aye, Hughes not in the list (Hughes-as-mayor also non-voting).
  - `cities.db`: `jon_pike` = **exactly 1** council vote (2020-04-16 Aye, a tie-break); Randall
    0 council votes 2022–2024 + the single genuine 2025-02-20; every MAYOR row carries empty
    `first_vote`/`last_vote`. ✔

- **Both 2021 crossover/appointment chains — CONFIRMED verbatim, fully on-disk:**
  - Randall Mayor appointment: `2021/2021-01-18/2021-01-19_…` lines 455–457 —
    *"appoint the first ever female Mayor of the City of St. George, Michele Randall, sworn in
    and appointed as the new Mayor on January 21, 2021 at 5:00 p.m."*; sworn 2021-01-21 (PRESENT
    list flips to *"Mayor Michele Randall"* + only 4 councilmembers → AL-B1 vacant). ✔
  - Curtis: `2021/2021-02-08/2021-02-10_…` line 115 — *"appoint Vardell Curtis for the position
    of City Council to fill Mayor Randall's remaining term"*; *"will end January[,] 2022"*;
    first seated 2021-02-11 (PRESENT list adds *"Councilmember Vardell Curtis"*); `cities.db`
    first council vote **2021-02-11**, last **2021-12-16**. ✔ Lost the 2021 general (rank4 of 4;
    election CSV confirms). ✔

- **2026 Hughes→VACANT→Anderson chain — CONFIRMED:** 2026-01-08 regular PRESENT = *"Mayor
  Jimmie Hughes"* + only four councilmembers (Larkin/Larsen/Tanner/Kemp) → AL-A1 empty;
  2026-01-22 *"INTERVIEW APPLICANTS FOR VACANT CITY COUNCIL SEAT"* (≈15 applicants),
  *"SWEARING IN OF NEW CITY COUNCILMEMBER — swearing in of Austin Anderson"*; `cities.db`
  Anderson first council vote **2026-01-22**. ✔ (Minor label nuance: header reads *"SPECIAL
  REGULAR MEETING"* / filename *"regular"*; roster prose says *"special meeting"* — cosmetic.)

- **Pre-floor `medium` flags — honestly earned.** 2020-01-06 PRESENT list shows Randall &
  Smethurst **already seated and NOT among the sworn-in three** (Hughes/McArthur/Larkin were
  sworn) → they are continuing 2017-cycle incumbents; term-start 2018-01 inferred from the
  4-year stagger. No fabricated citations. Pike MAYOR pre-floor likewise `medium`.

- **All eight elected/appointed members' `first_vote`/`last_vote` reconcile to `cities.db`
  exactly** (Smethurst 2020-01-06→2021-12-16, Larkin →2026-06-04, McArthur →2023-12-14, Curtis
  2021-02-11→2021-12-16, Larsen/Tanner 2022-01-06→2026-06-04, Kemp 2024-01-02→, Anderson
  2026-01-22→). **Every 2019/2021/2023/2025 general winner maps** to a tenure with the right
  rank/votes; the "Vote For N" cohort split (McArthur/Larkin 2019; Larsen/Tanner 2021) is a
  documented **labelling choice** with exact person-tenures. ✔

## (C) Structural invariants — CLEAN

- **No overlapping tenures on any seat.** Every seat chains half-open `[start,end)` with the
  successor's start = predecessor's end (AL-A1/A2/A3, AL-B1, AL-B2, MAYOR all verified).
- **The tightly-packed Jan/Feb-2021 double-vacancy does NOT overlap or contradict.** MAYOR
  VACANT `[2021-01-15, 2021-01-21)` (different seat) precedes AL-B1 VACANT
  `[2021-01-21, 2021-02-11)`. During the first window Randall still holds AL-B1 (last council
  vote 2021-01-19); during the second she holds MAYOR and AL-B1 is empty. **Randall's AL-B1
  `[…,2021-01-21)` and MAYOR `[2021-01-21,…)` share a boundary but do not overlap.** Same for
  Hughes AL-A1 `[…,2026-01-08)` vs MAYOR `[2026-01-08,…)`. ✔
- **Every row carries non-empty `sources` + `confidence`.** Counts reconcile: 21 rows =
  17 high / 4 medium / 0 low; 3 VACANT. The 4 medium = Randall AL-B1, Smethurst AL-B2, Pike
  MAYOR (pre-floor) + the MAYOR VACANT (inferred date). ✔
- **`district_versions.csv`** correctly degenerate (one At-Large row); at-large modeling matches
  the election layer's "Vote For N" structure. ✔
- **`minutes_unrecovered.csv`** holds only 2025-10-09, which does not intersect any VACANT
  window — gap-detector correctly silent. ✔

---

### Bottom line
One real defect (DEFECT-1, MEDIUM): the Pike→VACANT mayoral bracket cites a meeting Pike did
not preside (misled by a stale template line), placing `vacate_date=2021-01-15` past the first
documented-vacant meeting (2021-01-14); true bracket is **[2020-12-17, 2021-01-14]**. Fix in
`roster_overrides.csv` + note text. Everything else — both crossovers, all three VACANT chains,
the Randall override, the non-voting-mayor determination, and every structural invariant — is
correct and quote-verified. The 2021-02-25 spurious Randall vote is an upstream `cities.db`
extraction artifact with no roster-data impact.

---
## RESOLUTION ADDENDUM — 2026-07-11 (post-audit): vote-bound smear FIXED fleet-wide
Any observation in this audit describing a `first_vote`/`last_vote` **person-level smear** (a
councilmember→mayor person's mayor-era vote appearing on a council tenure, or a re-elected
member's whole-career span repeated on each term row) is **RESOLVED**. `scripts/roster_lib.py`
now CLAMPS `first_vote`/`last_vote` to each tenure's own `[start_date, end_date)` window
(`load_vote_dates()` + `clamp_vote_bounds()`), so each tenure carries only its own window's votes
(blank if none). The per-city de-smear overrides (Park City Worel, St George Randall) are retired —
the clamp reproduces their corrected values structurally. See `scripts/roster_HARDENING.md`
(hardening item #2). This addendum records the resolution; the dated findings above are unchanged.
