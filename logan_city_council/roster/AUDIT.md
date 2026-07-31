# Logan council-roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `roster/council_terms.csv` (19 rows), `district_versions.csv`, `roster_overrides.csv`,
`build_roster.py`, `CLAUDE.md` — verified against `election_results/logan_results_by_candidate.csv`,
`meeting_minutes/minutes/**`, root `cities.db` (`city='logan'`), and repo cardinal rules.
**Method:** READ-ONLY. No rebuild, no CSV/lib edits. Every claim below is quoted from source.

## Verdict: CLEAN — 0 confirmed defects.

All six verification targets pass at source. The two mid-term appointment chains, the
council→mayor crossover, the two-Anderson disambiguation, the non-voting-mayor flag, the
three pre-floor `medium` rows, and every structural invariant reconcile exactly against
the minutes, the certified election canvass, and the `cities.db` vote bounds. Findings are
limited to two cosmetic citation-precision items (Section B) and hardening suggestions
(Section C). No manufactured findings.

---

## (A) CONFIRMED DEFECTS

**None.**

---

## Verification detail (what was checked, with quoted evidence)

### 1. The two VACANT / appointment chains — both fully corroborated on-disk

**AL-B1 2020 — Bradfield → [VACANT] → López.**
- Oath quote verbatim, `2020-10-20_city-council-meeting.md` lines 33–35: *"The Oath of
  Office was administered by Judge Lee Edwards to newly appointed Councilmember Ernesto
  López who will fill the vacancy left by Jess Bradfield who resigned on September 22,
  2020. Councilmember López will serve until January 1, 2022."* — matches the row exactly.
- VACANT window bounded by **recovered** meetings: Bradfield present at his last meeting,
  `2020-09-15_city-council-meeting.md` lines 20–22 (*"…Chair Amy Z. Anderson,
  Councilmember Jess W. Bradfield, Councilmember Mark A. Anderson, and Councilmember
  Jeannie F. Simmonds"*); and the intervening `2020-10-06_city-council-meeting.md` lines
  20–22 present list is only 4 (*"…Chair Amy Z. Anderson, Vice Chair Tom Jensen,
  Councilmember Mark A. Anderson, and Councilmember Jeannie F. Simmonds"*) — **Bradfield
  gone, López not yet seated.** Seat genuinely vacant on 2020-10-06, inside the roster's
  VACANT interval 2020-09-23…2020-10-20. ✓
- `vacate_date=2020-09-23` = day after the documented 2020-09-22 resignation. ✓
- López **elected 2021** (row AL-B1 4313 rank1) and **2025** (3985 rank1) — both confirmed
  in `logan_results_by_candidate.csv`. ✓

**AL-A1 2025-26 — Mark A. Anderson → [VACANT] → Dahle.**
- Resignation, `2025-11-18_city-council-meeting.md` lines 21–22: *"Councilmember Mark A.
  Anderson announced his resignation from the Council on November 17, 2025 so he can
  prepare to take office as Mayor in January 2026."* Present list (lines 17–19) is only 4
  (Simmonds, Johnson, López, Amy Z. Anderson) — **Anderson absent.** ✓
- Vacancy language, `2025-12-02_city-council-meeting.md` lines 238–239: *"With the
  resignation of Mark. Anderson as councilmember, there is a vacancy on the Council. State
  Code requires an appointment within 30 days of the tenured resignation."* ✓
- Ballot, `2025-12-16_city-council-meeting.md` lines 731 & 763–765: *"Nine candidates were
  interviewed: Melissa Dahle, Gail Yost, Scott Mershon…"* → *"Melissa Dahle received three
  votes and Scott Mershon received one vote. With a majority vote, Melissa Dahle will be
  appointed as the interim city councilmember."* The seat rolls **"VACANT"** in that day's
  roll calls (lines 41, 64, 77, 346, 427, 503, 612, 691). ✓
- Oath, `2026-01-06_city-council-meeting.md` lines 26–28: *"…Oath of Office to Mayor Elect
  Mark A. Anderson and Councilmembers Elect Ernesto López, Katie Lee-Koven and Melissa
  Dahle."* ✓
- **The "appointed-after-losing" twist confirmed:** Dahle is `is_winner=N` in the 2025
  council general (rank3, 3559 — first loser by the −84 cutoff) yet is appointed to
  Anderson's **different** vacated cohort-A seat (2024–2028 term). `election_year` is blank
  (pure appointee) — verified in the CSV. Right person, right (AL-A1) seat. ✓

### 2. Mark A. Anderson council→mayor crossover
- `cities.db` `role`: `mark_anderson` (person 20000015) Council `first_seen 2020-02-18`,
  `last_seen 2025-11-04`, n=427 — his AL-A1 rows carry `first_vote=2020-02-18`,
  `last_vote=2025-11-04`. ✓
- His **MAYOR row (2026-01-06→serving) carries EMPTY vote bounds** (`non_voting_mayor` flag),
  confirmed in the CSV and in `build_roster.py` lines 56–58. His db votes do **not** smear
  onto the mayoralty. ✓
- Tenures do NOT overlap: AL-A1 council ends 2025-11-18 (VACANT); MAYOR begins 2026-01-06. ✓

### 3. Two Andersons — distinct, never merged
- `cities.db` `person` for logan contains **exactly two** Andersons: `Amy Z. Anderson`
  (20000001) and `Mark A. Anderson` (20000015) — distinct rows, distinct name_keys. ✓
- Roster keys `amy_anderson` (AL-B2, 2017-cycle, re-elected 2021, did-not-run 2025) and
  `mark_anderson` (AL-A1, 2019/2023 → Mayor 2026) are distinct on every row. ✓
- `build_roster.py` lines 67–72 confirm the design: surname `ANDERSON` resolves via the
  `disambiguators` map `{AMY: amy_anderson, MARK: mark_anderson}` **before** the flat
  surname table, and `ANDERSON` is deliberately absent from `NAME_TO_KEY` (adding it would
  merge them). ✓
- **Non-member Richard Anderson correctly excluded:** he appears only as *"Administration
  present: … Finance Director Richard Anderson"* (`2020-01-07_city-council-meeting.md`
  line 18) and is **absent from the `cities.db` person table** and the roster. ✓

### 4. Non-voting mayor
- `cities.db`: `holly_daines` has **zero** Council `role` rows (never votes). Both her MAYOR
  rows carry empty vote bounds. ✓
- No mayor ever appears in a roll call — Daines is only ever *"Administration present: Mayor
  Holly H. Daines."* ✓
- Structural check: **no `Mayor`-body row has any vote bound.** ✓

### 5. Pre-floor `medium` rows
- Exactly 3 `medium` rows — Bradfield (AL-B1), Amy Z. Anderson (AL-B2 first row), Daines
  (MAYOR first row) — each honestly flagged as "only the START date inferred from the
  cohort stagger." ✓
- Corroborated by `2020-01-07_city-council-meeting.md` lines 26–28: the oath swore **only
  the three 2019 winners** — *"Councilmember Elect Jeannie F. Simmonds, Councilmember Elect
  Tom Jensen and … Mark A. Anderson"* — while Bradfield, Amy Z. Anderson, and Mayor Daines
  head the same present-list (lines 15–18) **un-sworn**, confirming continuing incumbents. ✓

### 6. Structural invariants + election crosscheck (all via read-only CSV analysis)
- **19 rows = 16 high / 3 medium / 0 low; 2 VACANT.** ✓
- **No overlapping tenures; perfect half-open chaining per seat** (every `end_date` ==
  next row's `start_date`; no gaps, no overlaps). ✓
- **Serving set = Mayor + 5:** Dahle, Simmonds, Johnson, López, Lee-Koven + Mayor Mark A.
  Anderson. ✓
- Every row has non-empty `sources` + `confidence`. ✓
- **All 12 general winners map to a tenure** (2019 trio Anderson/Simmonds/Jensen; 2021 pair
  López/Amy Anderson + Mayor Daines; 2023 trio Anderson/Johnson/Simmonds; 2025 pair
  López/Lee-Koven + Mayor Anderson). Every vote count in the CSV matches the tenure sources
  (e.g. 2019 Anderson 3837 / Simmonds 3221 / Jensen 2546; 2021 López 4313 / Amy 4237;
  2023 certified Anderson 3449 / Johnson 2892 / Simmonds 2419 vs Needham 2400 = 19-vote
  seat; 2025 López 3985 / Lee-Koven 3643 / Dahle 3559). ✓
- **Primary-only advancers correctly dropped** (2019 Heare/Garrity/Verdoes; 2023
  Needham/Bennett; 2025 Dahle-as-candidate/Seamons) — none appears as a seated tenure
  except where later winning a general. ✓
- **`election_year` blank ONLY on the two appointee rows** (Dahle, López's appointed row). ✓
- **No `minutes_unrecovered.csv`** exists → gap detector sees an empty set; both VACANT
  windows are bounded by recovered meetings (2020-10-06; 2025-12-02 & 2025-12-16) → both
  correctly stay `high`. ✓
- **López vote lag** (appointed 2020-10-20, first *named* db vote 2021-12-07) is an honest
  source-recording limit (Logan 2020-21 heavily tally-only), not a gap — db `first_seen`
  2021-12-07 matches; tenure anchored by the appointment minutes. ✓

---

## (B) Calibration / honest-gap items (not defects — no fix required)

1. **Folder-date vs meeting-date citation labels.** Two `sources`/prose citations use
   Logan's *folder* date rather than the *meeting* date:
   - The AL-A1 VACANT row and `build_roster.py` (line 131) cite *"minutes:2025-12-01"* for
     the vacancy quote, but the meeting was held **2025-12-02** (file
     `2025/2025-12-01/2025-12-02_city-council-meeting.md`).
   - `CLAUDE.md` prose says Bradfield was *"present through the 2020-09-14 meeting"*; the
     meeting was **2020-09-15** (folder `2020-09-14`).
   The quotes are genuine and correctly attributed to those meetings; only the date *label*
   uses the folder (agenda) date. **No `council_terms.csv` date column is affected** — all
   tenure/vacate dates are correct. Cosmetic only.

2. **AL-A2 "serving as Chair" citation.** The Simmonds AL-A2 (2020) row cites
   *"minutes:2020-01-07 (serving as Chair)."* At that organizational meeting Simmonds was
   the **carryover 2019 Chair** presiding at the start; Amy Z. Anderson was then elected
   **2020 Chair** during the same meeting (`2020-01-07…` lines 396–400). The citation is
   defensible for that moment but reads oddly next to Amy's row ("Chair in 2020-2021").
   Purely descriptive; no data impact.

## (C) HARDENING recommendations

1. **Normalize citation dates to meeting dates.** When re-authoring `sources`/`vacate_source`
   strings (or a future refresh), prefer the meeting date embedded in the minutes filename
   (`YYYY-MM-DD_*.md`) over the parent folder's agenda date, so `minutes:2025-12-01`
   becomes `minutes:2025-12-02` and `2020-09-14`→`2020-09-15`. Eliminates the only
   ambiguity a reader could trip on.

2. **(Optional) Cross-body role assertion in `--check`.** The `non_voting_mayor` flag is
   correctly emptying the two MAYOR rows today; consider an explicit `--check` assertion
   that *no* `Mayor`-body row ever carries a non-empty `first_vote`/`last_vote` (it already
   holds), so a future mayor who happens to share a `person_key` with a voting councilmember
   (as Mark A. Anderson does) can never silently regress. Belt-and-suspenders; not needed
   for correctness now.

**Bottom line:** the Logan roster is defect-free against all sources. The two appointment
chains, the council→mayor crossover with the non-voting-mayor flag, the two-Anderson
disambiguation (incl. the excluded Finance Director Richard Anderson), the appointed-after-
losing Dahle twist, the three pre-floor `medium` rows, and every structural invariant are
correct and honestly documented.

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
