# Ogden rolling-roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `ogden_city_council/roster/` (council_terms.csv, district_versions.csv,
district_precincts.csv, roster_overrides.csv) vs. ground truth: election_results,
meeting_minutes/minutes/**, root `cities.db`.
**Verdict:** **CLEAN. Zero confirmed defects.** Every load-bearing claim reconciles to a
quoted source. The two `cities.db` vote-bound smears and the precinct middle-initial
"discrepancies" are correctly documented as informational-only and do NOT corrupt any
tenure date. Findings below are calibration notes + hardening options only.

---

## A. CONFIRMED DEFECTS

**NONE.** No row carries a wrong start/end date, wrong seat, wrong person, missing
source, wrong confidence, overlap, or fabricated citation.

---

## Verification log (each checkpoint, with quoted source)

### 1. Nadolski council-chair → mayor CROSSOVER — CONFIRMED
- D4 row: `start=2020-01-07 end=2024-01-02 end_event=became-mayor`, vote bounds
  `first_vote=2020-01-07 last_vote=2023-12-19`.
  - `cities.db`: `Ben Nadolski | Council | 2020-01-07 | 2023-12-19 | 381` — **exact match**,
    no smear.
  - `minutes/2020/2020-01-06/2020-01-07_city-council-meeting.md` L12 "Chair Ben Nadolski",
    L64-66 "Oath of Office for newly elected Council members Richard A. Hyer, Luis Lopez,
    and Ben Nadolski."
- MAYOR row: `start=2024-01-02 end=(empty, serving)`, vote bounds **both empty**.
  - `minutes/2024/2024-01-01/2024-01-02_city-council-meeting.md` L67-68 "City Recorder
    Hansen administered the Oath of Office to newly elected/re-elected Council members Dave
    Graf, Richard A. Hyer, and Shaun Myers and to newly elected Mayor Benjamin K.
    Nadolski." L116 "excited to see how he will transition from the office of Council member
    to Mayor."
- **Half-open, no overlap:** D4 ends 2024-01-02, MAYOR begins 2024-01-02. Chaining check:
  D4 `Ben Nadolski end=2024-01-02` → `Dave Graf start=2024-01-02` (clean cycle handoff).
- **No VACANT row** — D4 filled by Dave Graf, 2023 winner (elections CSV L18: DAVE GRAF
  2465/52.68). Correct: cycle boundary, not a mid-term vacancy.
- Caldwell = Mayor 2020-01-07..2024-01-02, `did-not-run`, **empty vote bounds**; no Caldwell
  person exists in `cities.db` at all (0 council rows). CONFIRMED.

### 2. The preserved clerk-typo vote-bound smears — CONFIRMED informational-only
- **Blair & Choberka `last_vote=2026-05-19`** matches `cities.db`
  (`Bart E. Blair|Council|2020-01-07|2026-05-19`, `Angela Choberka|Council|2020-01-07|2026-05-19`).
  Source of the smear quoted:
  `minutes/2026/2026-05-18/2026-05-19_city-council-meeting.md`
  - Present block L16-22: Chair **Hyer**, Vice Chair **Graf**, members **Flor Lopez,
    Lundell, Myers, Richey, Washington** (the correct 7 seated) — Blair/Choberka **absent**.
  - AYE line L220: "COUNCIL MEMBERS **BLAIR, CHOBERKA**, LOPEZ, LUNDELL, MYERS, RICHEY,
    WASHINGTON, VICE CHAIR [Graf]…" — departed members erroneously printed.
  - Tenure END dates are **NOT** corrupted: Blair final row `end=2026-01-06 end_event=lost`
    (`minutes/2026/2026-01-05/2026-01-06_...meeting.md` L97 "Former Council Member Blair
    spoke"; election L29 lost to Lundell 39.76). Choberka final row `end=2026-01-20`
    (holdover until Flor Lopez sworn; L181 "her final meeting after eight years").
- **Stephens `last_vote=2022-01-11`** matches `cities.db`
  (`Doug Stephens|Council|2020-01-07|2022-01-11`). Source quoted:
  `minutes/2022/2022-01-10/2022-01-11_city-council-special-meeting.md` L97 "VOTING AYE —
  COUNCIL MEMBERS CHOBERKA, HYER, LOPEZ, NADOLSKI, **STEPHENS**, VICE CHAIR WHITE, AND
  CHAIR BLAIR" — departed Stephens printed; Richey (his successor) omitted. Stephens tenure
  END is `2022-01-04` (`end_event=did-not-run`), NOT the smeared 2022-01-11. CONFIRMED not
  corrupted.

### 3. Redistricting — CONFIRMED
`minutes/2022/2022-03-14/2022-03-15_city-council-meeting.md`
- L346-347 "Proposed Joint Resolution-2022-3 Ordinance 2022-9 revising the four municipal
  districts and adopting the official municipal district boundary map of Ogden City."
- L371 amends "Section 1-7-2"; L356 "This map most closely resembles the existing
  boundaries"; L354 "must follow new precinct boundaries—which were established by the
  county in December"; L373 "effective immediately upon posting after final passage."
- **Roll call L381-384:** "COUNCIL MEMBER HYER MOVED ORDINANCE 2022-09 BE ADOPTED …
  VOTING AYE—COUNCIL MEMBERS BLAIR, HYER, RICHEY, WHITE, VICE CHAIR LOPEZ, AND CHAIR
  NADOLSKI. VOTING NO — COUNCIL MEMBER CHOBERKA." = **6:1, Choberka dissenting.** L386-388
  Choberka explanation: "there could have been community outreach." Matches
  `district_versions.csv` verbatim.
- `plan_2022` (D1-D4): real geometry_ref, high; `plan_2012` (D1-D4): geometry_ref blank,
  `low`, explicit acquisition GAP. CONFIRMED not fabricated.

### 4. Pre-floor `medium` rows — CONFIRMED, honestly flagged
Exactly 4 medium rows: Choberka (D1), Stephens (D3), White (AL-A), Blair (AL-B). All present
and **NOT among those sworn** at `minutes/2020/2020-01-06/2020-01-07_...meeting.md` (oath
L63-66 lists only Hyer, Lopez, Nadolski) → continuing 2017-cycle incumbents. Stephens→D3 is
assigned by elimination (honestly labeled). No fabricated citations; only the 2018-01-01
term-start is inferred. CONFIRMED.

### 5. Non-voting mayor — CONFIRMED
Both Mayor rows have empty `first_vote`/`last_vote`. Caldwell: absent from `cities.db`
entirely (0 council rows). Nadolski-as-Mayor: `cities.db` council role stops 2023-12-19,
no Mayor voting role. CONFIRMED.

### 6. Precinct "DISCREPANCY" prints — CONFIRMED cosmetic
Election CSV winners: D2 2023 "RICHARD HYER" (roster "Richard A. Hyer"); D3 2025
"KEN R. RICHEY" (roster "Ken Richey"). Same individual, correct winner; the flag is an
exact-string middle-initial artifact. Does not affect any tenure. CONFIRMED (already logged
in roster CLAUDE.md).

### 7. Structural invariants + election crosscheck — CONFIRMED
- 20 rows: 16 high / 4 medium / 0 low. 0 rows missing sources or confidence.
- Per-seat chaining: **0 gaps, 0 overlaps** (every `end_date` == next tenure's `start_date`).
- **All 16 general winners** (District + At-Large + Mayor, 2019/2021/2023/2025) map to a
  roster row by surname+year. 0 unmapped.
- District-seat transitions present: D1 Choberka→Flor Lopez (2026-01-20), D3 Stephens→Richey
  (2022-01-04), D4 Nadolski→Graf (2024-01-02), plus AL-A/AL-B/AL-C/MAYOR.
- `roster_overrides.csv`: 0 data rows (header only). `district_precincts.csv`: 41 plan_2022
  (high) + 4 plan_2012 GAP (low).

---

## B. Calibration / honest-gap items (not defects)

1. **`plan_2022` `effective_start=2022-03-15` uses the ADOPTION date**, while Ordinance
   2022-9 is "effective immediately upon posting after final passage" (posting typically
   same/next day). Negligible: no election falls in the gap — 2021 used the old lines, 2023
   & 2025 used the new. Honest and load-neutral; flagging only for completeness.

2. **Flor Lopez `start_date=2026-01-20` is the first-attested-vote date, not an oath date.**
   The 2026-01-06 minutes (L51-52) state Lopez "was unavailable to be sworn in to office
   until the second week of January"; the 2026-01-20 minutes show her present + voting
   (L18, and voting NO at L79). No oath-administration line was located for 2026-01-20, so
   the roster honestly anchors to first attestation rather than inventing an oath date.
   Correct handling; no fix needed.

3. **Source-side OCR inconsistency in the 2022-01-11 special-meeting file** (not a roster
   error): its present block reads "Chair Ben Nadolski / Vice Chair Luis Lopez" (2020-21
   leadership) while the same file's roll call reads "VICE CHAIR WHITE, AND CHAIR BLAIR"
   (2022 leadership) and prints departed STEPHENS while omitting sitting RICHEY. This is the
   known 2022-scan carve artifact already documented in `meeting_minutes/CLAUDE.md`; the
   roster is unaffected (Richey's tenure starts 2022-01-04 per `cities.db` first_seen + the
   2022-01-04 oath; Stephens ends 2022-01-04). Minor descriptive nit: the meeting_minutes
   doc calls this a "chair-election roll call," but the specific smeared roll call is on
   Ordinance 2022-1 (school-board districts). Substance is correct.

---

## C. HARDENING recommendations (NEW — precinct-crosscheck cluster already logged)

1. **Add an explicit `vote_bound_artifact` boolean column** to `council_terms.csv`.
   `first_vote`/`last_vote` carry the `cities.db` smears verbatim (by design), and today the
   only signal that Blair/Choberka/Stephens's `last_vote` is a preserved typo lives in prose
   in the `note` column. A downstream consumer that (incorrectly) derived "who served on
   date X" from vote bounds rather than the authoritative `start_date`/`end_date` interval
   would wrongly seat Blair & Choberka on 2026-05-19. A machine-readable flag would let
   consumers programmatically distinguish smeared bounds. **Low priority** — the tenure
   intervals are the source of truth and are correct; this only hardens against misuse of the
   informational fields.

2. **(Reiterating an already-noted gap, not new)** the exact-string precinct comparator and
   the `29OG##`/`OGD##` naming split are already in the roster CLAUDE.md hardening backlog;
   nothing to add.

No other hardening items. The roster is well-constructed, fully sourced, and internally
consistent.

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
