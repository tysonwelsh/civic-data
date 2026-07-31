# planning_commission/ — Planning Commission vote extraction (St. George, UT)

Roll-call votes of the **St. George City Planning Commission** (Washington County,
UTAH — not Louisiana). Sibling of `meeting_minutes/` (the City Council pipeline) and
modeled on it, but the PC minutes use a **different vote-block format** so this has its
own extractor. Data floor: **2020**.

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **132 born-digital PC minutes
  (2020–2026)**. Indexed by `minutes_index.csv` (`source` = `pmn` for the Utah Public
  Notice backfill, `revize` for the 2024+ city portal). Immutable source of truth.
- `extract_votes.py` — the extractor (below). `python3 planning_commission/extract_votes.py`
- `validate_votes.py` — independent auditor (`python3 planning_commission/validate_votes.py`).
- `votes/<year>/<week>/<date>_<slug>.json` — per-meeting structured votes.
- `votes/_validation_report.txt` — tally-mismatch + per-format log.
- `all_votes.csv` — long format, one row per member-vote. **13-col schema identical to
  the council file**: `date,year,title,body,motion_no,motion,motion_type,result,mover,
  seconder,member,vote,source`. **`body`="PlanningCommission" and `title`="Planning
  Commission" on every row.**
- `roster.csv` — reconstructed commissioner roster: `commissioner,first_seen,last_seen,
  n_meetings`.

## Run
```
python3 planning_commission/extract_votes.py          # resumable: skips existing JSON
python3 planning_commission/extract_votes.py --force   # re-write every JSON
python3 planning_commission/validate_votes.py          # audit (exit 0 = PASS)
```
`all_votes.csv`, `roster.csv` and the validation report are **always rebuilt in full**
(every meeting is parsed in memory); only the per-meeting JSON writes are skipped when
they already exist, so re-running is cheap and idempotent.

## Latest run (PASS)
- **133 meetings**, **1,025 motions**, **6,372 member-vote rows**, **16 commissioners**.
- **685 recommendations**, **100 final actions**, **240 procedural**; **89 contested**
  (a Nay/Abstain/Recuse), **1 tally-only** motion.
- Validator: **0 off-roster**, **0 out-of-range**, JSON↔CSV reconcile **6,372 = 6,372**.
- **2026-07-19: line-number-gutter tolerance** (`_strip_line_number_gutter`, shared with the
  council extractor; detector gated per-file so non-gutter files stay byte-identical)
  recovered **two born-digital gutter PDFs** that had extracted 0 motions —
  **2024-04-09** (5 motions) and **2024-12-10** (7 motions, incl. **m1 the 3-to-2 FAILED**
  hillside-ridgeline recommendation: Austin Anderson[Chair]/Rogers Nay, Fisher/Casey/Draper
  Aye), +67 member-vote rows, all source-verified. Two 2022 gutter siblings
  (2022-06-09 work, 2022-08-25) are joint/councilmember-roll docs already captured on the
  council side — see "Joint meetings" below.
- 2026-07-02 (plan 3.5): role-prefix fix recovered the 3 dropped 2025-02-25 m1/m2 ayes
  (Chapman/Rogers/Draper; results 2:0 → 5:0) — see VERIFICATION.md.

## Joint / councilmember-roll PC docs (do NOT double-count)
A handful of docs indexed under the PC (`*joint*`, or a PC "work"/"meeting" whose only
recorded motion is a **councilmember** adjournment — 2022-06-09, 2022-08-25, 2024-02-29,
2024-05-23, 2026-05-28) print `Councilmember X – aye` rolls the PC role-parser does not
recognize. This is **correct**: those votes are COUNCIL votes cast by councilmembers, and
every one is already captured on the **council** side (`meeting_minutes/all_votes.csv`,
`body=Council`, via a cross-listed council-index twin of the same meeting). Capturing them
here would duplicate the rows AND mislabel them `body=PlanningCommission`, so the PC
pipeline emits **0 PC-member votes** for them by design (no planning commissioner cast a
recorded vote). Verified 2026-07-19: all five councilmember-roll adjournments have a
matching `body=Council` motion on the same date.

## Two source formats (auto-detected per motion block)
St. George PC minutes use **two** roll-call layouts; the parser detects which one
follows each `MOTION:` and parses accordingly.

**(A) `AYES (n) / NAYS (m)` tally-with-names** — most 2020–2023 PMN files + a few Revize
files. Member names are listed *under* each `AYES`/`NAYS` (and rarely `ABSTAIN`) header:
```
MOTION: Commissioner Brager made a motion to recommend approval of Item 2A ...
SECOND: Commissioner Draper
[ROLL CALL VOTE:]
AYES (6)
    Chairman Nathan Fisher
    Commissioner David Brager
    ...
NAYS (0)
Motion carries
```

**(B) `VOTE:` per-member lines** — Revize 2024+. Council-style:
```
MOTION: A motion was made by Planning Commission Member X to recommend ... to City Council
SECOND: ... seconded by Planning Commission Member Y.
VOTE: ... called for a vote, as follows:
    Planning Commission Member X – aye
    Planning Commission Chair Anderson – absent
    ...
The vote was unanimous the motion passed
```
Vote values map: `aye/yes→Aye`, `nay/no→Nay`, `abstain→Abstain`,
`absent/excused→Absent`, `recuse/recused→Recuse`.

### 2020–2021 (PMN) fragmentation handling
- **Empty placeholder blocks** for pulled/postponed items render as
  `MOTION: Commissioner` / `SECOND: Commissioner` / `AYES (0) / NAYS (0)` (no mover, no
  names). Some pulled items instead carry a **stale all-present template roll call**
  (`AYES (7)` with every member). Both are **skipped** — a blank-motion block (no mover
  and <15 chars of motion text) is not a recordable decision, so attaching names to it
  would be a guess.
- **Page-break noise** inside a vote block (`Planning Commission Minutes` /
  `Planning Commission Agenda` / `Page N of N` / a stray date) is stripped. The footer in
  some 2020 files is literally `Planning Commission Agenda` (not `Minutes`).
- **ALLCAPS slide/section titles** that bleed into a vote block after a page break
  (`CONFLICTS OF`, `INTEREST`, `PLANNING COMMISSION TRAINING`) are rejected as voter
  names (voter names are Title Case, never ALLCAPS).
- **Role-token case/word-order variants** (`Pro tem Chair Steve Kemp`) are stripped
  case-insensitively so the name is captured.

## RECOMMENDATION vs FINAL ACTION (the key contract — encoded in `result`)
The PC both **recommends** items to City Council and takes **final action** on others
(CUPs, site plans, hillside permits, some subdivisions). This is machine-detectable from
the `result` string. **The DB keys on the substring `recommend`/`forward` → it's a
`pc_recommendation`; absence → `pc_final_action`; and `positive`/`negative` → direction.**

| motion intent | `result` string | DB reads |
|---|---|---|
| recommend **approval** … to City Council | `Positive recommendation N:N` | recommendation / positive |
| recommend **denial** … to City Council | `Negative recommendation N:N` | recommendation / negative |
| **final** approve (CUP/site plan/hillside/plat …) | `N:N Approved (Final Action)` | final action |
| **final** deny | `N:N Denied (Final Action)` | final action |
| procedural (minutes, agenda, elect/nominate, continue/table, adjourn) | `N:N Pass` | (neither) |

- `N:N` is **ayes:nays** from the **authoritative named roll call** (see tally rule).
- A motion that **failed** gets a ` (failed)` suffix (e.g. `Positive recommendation 2:2
  (failed)`, `2:2 Approved (Final Action) (failed)`).
- Direction logic: a motion is **Negative** only on explicit denial phrasing
  (`denial`/`deny`/`denied`/`negative recommendation`/`do not approve`) — **not** a bare
  "negative", which shows up in descriptive text ("mitigated any *negative* effects").
- Recommendation is detected first (`recommend`/`forward` in the motion), then procedural,
  else final action. So "recommend approval of Item 2A" is a recommendation even though
  approving a CUP outright is a final action.

## Tally rule — named counts are authoritative
The `AYES (n)`/`NAYS (m)` **header numbers are frequently wrong** in the source (often a
page-break split the name list, or a plain miscount). The parser captures the **actual
listed names** and uses **`len(names)`** for the `result` tally and pass/fail — never the
declared `(n)`. The declared numbers are kept only to **flag** the discrepancy.

### Tally mismatches (58 this run — all genuine source artifacts, none fabricated)
- **51 declared-vs-named**: source `AYES (n)` count ≠ the number of names listed. Verified
  real (e.g. 2024-01-09 m2 lists 7 names under `AYES (6)`; 2020-01-28 m3 puts 2 names under
  `NAYS (0)`). Names are extracted as written; the `(n)` typo is reported, not "corrected".
- **7 "unanimous" with a recorded nay**: the minutes write "Motion Carries unanimous" yet
  list a Nay in the roll call (same class of source quirk seen in the council file). The
  Nay is kept; the contradiction is logged.
All are in `votes/_validation_report.txt`, tagged `[PMN]` vs `[REVIZE]`.

### Parse quality by source format
- **PMN 2020–2023** (71 vote-meetings, 3,740 rows): format (A). Names are listed as **full
  "First Last"** in the roll call → high fidelity. Most declared-vs-named mismatches live
  here (loose early formatting).
- **Revize 2024–2026** (50 vote-meetings, 2,516 rows): mostly format (B) per-member lines
  (surnames only) + a few format (A). Clean, except page-break-split `AYES` blocks in early
  2024 that drive the declared-vs-named flags.

## Name normalization & the two surname collisions
The Planning Commission is a **separate body** from the Council — its members are NOT
councilmembers, so surnames are mapped to the **PC** roster, never to council names.
Unambiguous surnames → canonical "First Last" (`PC_SURNAME` in the script). **Two genuine
surname collisions** are handled explicitly (documented heuristics, not guesses about how
anyone voted):

- **Anderson** — *Austin Anderson* (seated PC **Chair** 2021–Jan 2026) vs *Brandon
  Anderson* (joined as a Member, Dec 2023; written **`B. Anderson`**). **Resolution is
  ATTENDANCE-BASED as of 2026-07-19** (replacing the old year GUESS, which was unsound
  because BOTH serve 2024–2025): explicit first name (`Austin`/`Brandon`/`B.`) wins; role
  **`Chair`** (not Vice) → Austin; role **`Member`** → Brandon when Brandon is on the
  meeting's PRESENT/EXCUSED roster (else Austin if only Austin is rostered); a **bare**
  `Anderson` (no first name, no disambiguating role) resolves from attendance only when
  **exactly one** Anderson is rostered — with **both** (or neither) rostered it **ABSTAINS**
  (leaves the printed token, never guesses). `normalize_pc_name` takes the meeting's
  Anderson roster (`andersons`) built in `parse_meeting`. Impact on attribution: **zero rows
  changed** — every 2024–2026 roll line already carries `Chair Anderson`/`Member Anderson`
  (Austin is Chair through Jan 2026; from 2026-02 Austin has LEFT the PC for City Council,
  so only Brandon remains), so all existing attributions were already correct; the switch
  only replaces the fragile mechanism and adds honest abstention for any future ambiguity.
  Verified 2026-07-19 across the corpus (incl. 2025-02-11 `Chair Anderson – absent` /
  `Member Anderson – aye` → excused Austin / present Brandon). **Austin F. Anderson is the
  SAME person who was appointed to the City Council 2026-01-22** (he applied as a former PC
  Chair, was sworn in, and vanishes from the PC roster from 2026-02) — the person layer
  correctly links the two bodies. Both Andersons co-occur in 2024+ contested votes.
- **Draper** — *Ray Draper* (2020–2022) vs *Teri Draper* (2023–2026). They **never serve as
  commissioners at the same time**, so a bare `Draper` resolves to Ray (year ≤ 2022) or
  Teri (year ≥ 2023). (`Ray Draper` appears once in 2025 as an *applicant*, not a voter.)

Spelling variants folded: `Terri/Teri Draper`→Teri Draper, `B. Anderson`→Brandon Anderson.

## Roster (appointed — no elections)
PC members are **appointed by the City Council**, not elected. `roster.csv` is
reconstructed from the `PRESENT:`/`EXCUSED:` attendee headers (full names), with each
commissioner's span (`first_seen`..`last_seen`) **extended to cover every recorded
appearance, including roll-call votes**. This matters because a few source minutes carry a
**stale roll-call template** that lists a voter absent from that meeting's own `PRESENT:`
block — e.g. **Emily Andrus** is listed voting Aye in the **Jan-2024** files (m's of
2024-01-09 / 2024-01-23) although her term ended Dec 2023 and she is not in those PRESENT
blocks. The vote is recorded as written (never dropped/invented); her roster span just
covers it, so the validator shows 0 out-of-range.

`n_meetings` = meetings where the commissioner is in `PRESENT:`.

### Appointment cross-check (vs `meeting_minutes/all_votes.csv`, `motion_type=Appointment`)
The Council's own appointment motions corroborate the roster:
- Austin Anderson appointed **2021-02-25** (roster first_seen 2021-03-09);
- Steve Kemp & Elise (Mortensen) West + Ray Draper reappointed **2020-12-03**;
- Terri Draper appointed **2023-07-20** (roster 2023-08-08);
- Casey & Brandon Anderson joined **Dec 2023** (introduced 2024-01-09);
- Ben Rogers reappointed 2025-02 / 2025-07; Brandon Anderson, Lori Chapman, Nathan Fisher,
  Austin Anderson reappointed Oct 2025; **Kelly Taysom appointed 2026-02-05** (roster
  2026-02-10). All consistent.

## motion_type taxonomy
Same fixed 12-category set as the council extractor (`classify_motion`). PC docket is
overwhelmingly **Land-Use/Zoning** (712 motions), then Procedural/Administrative (233);
a PC-aware fallback maps a substantive `recommend/approve` motion that cites an agenda
"Item N" or land-use noun to Land-Use/Zoning (PC motion text often only says "Item 2A").
Residual **Other** = 56 (genuine edge cases / source typos like "condition use permit").

## `names_recorded` convention
`true` when the block lists individual members; `false` for a tally/outcome only. We
**never invent who voted which way** — a `names_recorded:false` motion is a JSON record but
contributes **zero** rows to `all_votes.csv`. Only 1 such motion this run (2023-08-22 m6
adjourn, whose roll call was interrupted by an embedded training document in the source).

## For analysis
- All rows are `body=PlanningCommission`; filter `result` for `recommend` (recommendations)
  vs `Final Action` (final actions) vs `Pass` (procedural).
- **Contested = any Nay/Abstain/Recuse** — the signal worth surfacing.
- Join to the Council pipeline on the recommendation → the Council's subsequent vote on the
  same item (Council `all_votes.csv`, `body=Council`).
