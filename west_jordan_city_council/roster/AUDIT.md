# West Jordan roster — adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did not build this layer)
**Scope:** `roster/council_terms.csv`, `district_versions.csv`, `district_precincts.csv`,
`roster_overrides.csv`, `CLAUDE.md`, checked against `election_results/`,
`meeting_minutes/minutes/**`, and root `cities.db`.
**Verdict:** **PASS.** The mixed district + at-large + non-voting-mayor model is faithful to the
sources. Every structural invariant holds. Two **LOW / note-field-only** inaccuracies found (elected
leadership titles in free-text `note` cells — no impact on seat, person, dates, confidence, or any
query). No fabrication, no seat mis-filing, no dropped winner.

---

## Method / what was ground-truthed

- **cities.db** (root): 13 distinct WJ Council voters; `first_seen`/`last_seen`/`n_votes` per person.
  Max distinct voters on **any motion = 7** and on **any meeting date = 7** (never 8). `person` table
  for `city='west_jordan'` contains **no Burton / no Dirk** row.
- **Minutes read verbatim:** 2023-11-29 special (coin toss + Res 23-070), 2023-10-25 (Worthen
  farewell), 2022-04-13 (Res 22-011 redistricting roll), 2025-02-25 (Mayor-under-STAFF roll),
  2026-01-13 (current roll), 2024-01-10 (roll).
- **Precinct reconciliation** run independently against
  `election_results/west_jordan_results_by_precinct.csv`.
- **Structural checks** (overlap, chain continuity, sources/confidence completeness, key uniqueness,
  winner↔tenure bidirectional mapping) run directly on the CSVs.

---

## (A) CONFIRMED DEFECTS

### D-1 (LOW, note-field only) — Lamb credited as 2024 Council Chair; the 2024 Chair was Jacob
`council_terms.csv` row **D1 / Chad Lamb / 2024-01-10** note ends *"Currently serving (Council Chair
2024/2025)."* This **contradicts** the D3 / Zach Jacob / 2024-01-10 row, whose note says *"Council
Chair for 2024."* The source resolves it in Jacob's favor:

> 2024 minutes: **"Chair Jacob called the meeting to order"** — **34** meetings;
> **"Chair Lamb called the meeting to order"** — **4**; **"Chair Bloom …"** — 1.

Zach Jacob was the seated 2024 Council Chair; Lamb presided only a handful of fill-in meetings and
became Chair in **2025** (2025-02-25 roll: *"COUNCIL: Chair Chad Lamb, Vice Chair Kayleen
Whitelock…"*). **Fix:** change the Lamb D1 note from *"Council Chair 2024/2025"* to *"Council Chair
2025"* (drop 2024). No schema field changes.

### D-2 (LOW, note-field only) — Whitelock labeled "Vice Chair 2026"; the 2026 Vice Chair is Wignall
`council_terms.csv` row **AL1 / Kayleen Whitelock / 2026-01-13** note ends *"Currently serving (Vice
Chair 2026)."* Source contradicts:

> 2026-01-13 roll: **"COUNCIL: Chair Bob Bedore, Vice Chair Jessica Wignall, Annette Harris, Zach
> Jacob, Chad Lamb, Kent Shelton, Kayleen Whitelock"** — Whitelock is a plain member; **Wignall** is
> Vice Chair. Across all 2026 minutes: *"Vice Chair Wignall"* recurs; **zero** *"Vice Chair
> Whitelock."*

Whitelock was Vice Chair in **2025** (under Chair Lamb), not 2026. **Fix:** change the AL1/2026 note
to *"Vice Chair 2025"* (she was also Council Chair 2022). Correspondingly, `roster/CLAUDE.md`'s
"current roster" table row **`AL1 | Kayleen Whitelock (Vice Chair)`** should drop the "(Vice Chair)"
tag (only `AL3 | Jessica Wignall (Vice Chair)` is correct for the 2026-01-13 as-of). The Wignall and
Bedore ("Council Chair 2026") titles are correct.

*Both D-1 and D-2 live only in free-text `note`/display cells. `seat_id`, `person_name`,
`person_key`, dates, `first_vote`/`last_vote`, `sources`, and `confidence` are all correct; no query
(`roster_as_of`, `representatives_for_address`) is affected. These are honest-accuracy nits, logged
per the "never fabricate" cardinal rule.*

---

## (B) Calibration / honest-gap items (all correct — no change needed)

- **The two `medium` at-large holdovers** (AL1 Whitelock 2020-01-08, AL3 Lamb 2020-01-08) are
  correctly `medium`: service is vote-documented from 2020-01-08 (cities.db) but the seating
  election predates the 2019 floor; **no fabricated seating date/election**. Not overstated to `high`.
- **`plan_pre2022` geometry + precinct composition** — honest acquisition GAP: `geometry_ref` blank,
  `confidence=low`, 4 blank-precinct gap rows in `district_precincts.csv`. Correct.
- **Person-level vote-bound smear on Chad Lamb** — both his AL3 (2020–2022) and D1 (2024–present)
  rows carry the whole-person span `first_vote=2020-01-08 / last_vote=2026-05-12` (matches cities.db
  Chad Lamb 2020-01-08..2026-05-12). Documented per-row as the logged fleet vote-bound-clamp batch
  item; the authoritative service dates are correct. Acceptable.
- **AT-LARGE seat ids are analytical** — disclosed in CLAUDE.md and driver; the Green→Harris and
  Bloom→Wignall AL2/AL3 pairings are arbitrary and stated as such. Faithful modeling choice.
- **Doc nit (very low):** CLAUDE.md §"4-layer reconciliation" says *"all 25 winner rows across the 4
  cycles map cleanly"* — the source actually has **17** municipal-general winner rows
  (6/2019 + 3/2021 + 5/2023 + 3/2025), all of which do map (verified below). The "25" is a stray
  narrative count, not a data error. Consider correcting to 17.

---

## (C) HARDENING recommendations

**None structural.** The two note-field title fixes (D-1, D-2) are the only edits; batch/known items
are already logged. Optionally, a validator that reconciles free-text leadership titles
("Chair YYYY" / "Vice Chair YYYY") against the minutes' `called the meeting to order` /
`Chair`/`Vice Chair` roll headers would have caught D-1 and D-2 — but this is a cosmetic layer, not
worth a library change for one city.

---

## Evidence log (what verified clean)

### 1. Mixed district + at-large split — FAITHFUL
- The **4 districts are real geographic contests.** Independent precinct-sum reconciliation of the
  2023 district races (grouping `results_by_precinct` by the `district_precincts` plan_2022
  assignment) reproduces every winner exactly: **D1 Lamb 2417 / D2 Bedore 2026 / D3 Jacob 1913 /
  D4 Shelton 2207** — identical to the certified `by_candidate` totals. **0** precinct
  assignment-vs-ballot mismatches (every precinct that voted in a District-N contest is assigned to
  District N). Composition D1=25, D2=21, D3=27, D4=23 (96 plan_2022 rows).
- The **3 at-large are one city-wide "Vote-for-3" field.** `results_by_candidate` shows a single
  `West Jordan City Council At-Large` contest with **three** `is_winner=True` rows per cycle:
  > 2021: KAYLEEN WHITELOCK (r1), KELVIN GREEN (r2), PAMELA BLOOM (r3) — CHAD LAMB r4 (loser)
  > 2025: KAYLEEN WHITELOCK (r1), ANNETTE HARRIS (r2), JESSICA WIGNALL (r3) — SERGIO SOTELO r4
- **AL1/AL2/AL3 are honest analytical labels** (no legal seat number; disclosed). Per-id chains are
  internally consistent with **no two people overlapping on one AL id** and the **3 concurrent
  holders always on 3 distinct ids**: 2020 {AL1 Whitelock, AL2 Green, AL3 Lamb} → 2022 {AL1
  Whitelock, AL2 Green, AL3 Bloom} → 2026 {AL1 Whitelock, AL2 Harris, AL3 Wignall}.
- **No mis-filing:** every district member sits on a D-id, every at-large member on an AL-id; none
  crossed.

### 2. D2 resignation → coin toss → appointment — CONFIRMED, no overlap
- Worthen honored 2023-10-25 (*"Outgoing District 2 Council Member … deeply missed … her new
  adventures"*); her last cities.db D2 vote is **2023-10-25**.
- VACANT begins the day **after** last service: **[2023-10-26, 2023-11-29)**, `confidence=high`.
- Coin toss + appointment quoted verbatim:
  > "The Council submitted votes electronically, with 50% cast for Bob Bedore and 50% for Robert
  > Bennett. … Ms. Sloan designated Mr. Bennett 'heads' and Mr. Bedore 'tails' and tossed a coin to
  > break the tie vote. The coin landed 'heads' up, and Mr. Bennett was selected…"
  > "e. Resolution 23-070 appointing Robert Bennett to fill the vacancy … The motion passed 6-0. …
  > City Recorder Tangee Sloan administered the Oath of Office to Robert Bennett."
- Bennett tenure [2023-11-29, 2024-01-10) ends exactly when Bedore is seated 2024-01-10 — **no
  overlap.** cities.db Rob Bennett first/last vote **2023-11-29 … 2023-12-20 (5 votes)** matches.
  (The 6-0 appointment roll is the 6 seated members with D2 vacant; Bennett then voted 7-0 on the
  next item after his oath.)

### 3. Chad Lamb — one person, two non-contiguous seats — CONFIRMED
- Single `chad_lamb` key on both AL3 [2020-01-08, 2022-01-12) and D1 [2024-01-10, open). **No
  overlap**; genuine ~2-year off-council gap. Lost the 2021 at-large race (rank 4 of 6, 18.41%). Not
  two people; not a fabricated bridge (cities.db carries one Chad Lamb, span 2020-01-08..2026-05-12).

### 4. Non-voting strong Mayor — CONFIRMED
- Max distinct voters per motion = 7, per meeting = 7; Mayor **absent from every roll**. Burton
  **absent from cities.db `person`/`role`.** MAYOR rows carry blank `first_vote`/`last_vote`.
  Quoted 2025-02-25 (Burton under STAFF; 7-0 names only the seven), 2022-04-13 (5-0, Mayor explains
  the *next* item only), 2026-01-13 (Burton under STAFF; 7-0).

### 5. Redistricting — CONFIRMED
- Res 22-011, 2022-04-13, roll quoted 5-0 (Whitelock, Green, Jacob, Pack, Worthen Yes; Bloom +
  McConnehey absent). plan_2022 real geometry (high) + plan_pre2022 GAP (blank geometry_ref, low).
  Precinct cross-check reconciles the 2023 district winners (see §1).

### 6. Structural invariants — CONFIRMED
- **0** overlapping tenures per seat; every seat chain continuous with the sole explicit VACANT (D2).
- Every row has non-empty `sources` + `confidence` (19 high incl. VACANT, 2 medium; 0 low).
- `person_key` ↔ `person_name` bijective (no split/merged keys).
- **All 17 municipal-general winners (2019/2021/2023/2025) map to a tenure with matching
  `election_year` — including all six at-large Vote-for-3 winners; 0 unmapped, 0 reverse drift.**
- Current roster (D1 Lamb, D2 Bedore, D3 Jacob, D4 Shelton, AL1 Whitelock, AL2 Harris, AL3 Wignall,
  MAYOR Burton) matches the 2026-01-13 roll and the 2025/2023 winners. No OCR/PrimeGov name
  corruption (roster names match cities.db `full_name` up to the Chris/Christopher display variant).

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
