# planning_commission/ — Vineyard, UT Planning Commission vote pipeline

Recorded motions + roll-call votes for the **Vineyard Planning Commission** (an appointed
body), 2020–2026, extracted from the minutes markdown. Mirrors the council pipeline in
`../meeting_minutes/` (same CivicClerk vendor → similar minutes format) but with
PC-specific roles, a reconstructed appointed roster, and a recommendation-vs-final-action tag.

## What's here
- `minutes/<year>/<week-monday>/<date>_planning-commission-meeting.md` — **102 minutes**
  (index: `minutes_index.csv`). Meetings with no published minutes yet: `minutes_unrecovered.csv`.
- `extract_votes.py` — reads `minutes_index.csv`, parses each meeting's `Motion:` blocks →
  per-meeting JSON + rebuilds `all_votes.csv` + `roster.csv`. Resumable: skips a meeting
  whose JSON already exists unless `--force`.
- `validate_votes.py` — tally / roster / JSON↔CSV checks → `votes/_validation_report.txt`.
- `votes/<year>/<week-monday>/<date>_planning-commission-meeting.json` — one per meeting
  (`date,title,body,source,names_present,votes[]`).
- `all_votes.csv` — long format, one row per member-vote. **`body="PlanningCommission"` and
  `title="Planning Commission"` on every row.** 13 cols:
  `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`.
- `roster.csv` — `commissioner,first_seen,last_seen,n_meetings`.

Run order: `python3 extract_votes.py && python3 validate_votes.py`.

## Headline numbers (current build)
102 meetings · 375 motions · 1,617 member-vote rows · 23 distinct commissioners.
58 recommendations · 102 final actions · 215 procedural · 4 contested · 13 tally-only.
Validation: **PASS** (0 tally mismatches, 0 off-roster, 0 out-of-range, CSV reconciles).
NB 2026-07-02 repair: the CivicClerk minutes attachment for event 815 (2023-06-21) is a
mis-uploaded copy of the 2023-06-07 minutes; the real June 21 minutes were recovered from
PMN (`source=pmn` in the index). Its clerk-typo `MOTION.` header and `Graden Oster`
spelling are handled in `extract_votes.py` (see `../VERIFICATION.md`).

## `result` encodes recommendation vs final action vs procedural (machine-detectable)
The Planning Commission **recommends** some matters to the City Council (rezones, plats,
subdivisions, GPAs, annexations, ordinances) and takes **final action** on others (CUPs,
site plans, design/sign waivers — these never reach Council). This is encoded in `result`
so the DB build can key on it:
- **recommendation** → `"Positive recommendation N:N"` / `"Negative recommendation N:N"`
  (a failed recommendation gets a trailing ` (Failed)`). Direction: "deny/denial/denying/
  negative" ⇒ Negative, otherwise Positive. Triggered when the motion text contains
  **"recommend"** or **"forward"**.
- **final action** → `"N:N Approved (Final Action)"` / `"N:N Denied (Final Action)"`.
  Denied when the motion was to deny, or a motion-to-approve **failed**.
- **procedural** (minutes, agenda, open/close public hearing, continue/table, adjourn,
  chair/vice-chair elections) → `"N:N Pass"` / `"N:N Fail"`.

DB keying: substring **"recommend"/"forward"** ⇒ `pc_recommendation`, else ⇒
`pc_final_action`; **"positive"/"negative"** gives direction; **"(Final Action)"**
distinguishes a true final action from a procedural `Pass`.

### The N:N tally
N:N is the **source's stated tally** when the minutes give an explicit number
(`Motion Passed 6-0`, `CARRIED FOUR (4) TO ONE (1)`); otherwise the **named roll count**
(`len(aye):len(nay)`). For tally-only motions with neither names nor a stated number
(`ALL WERE IN FAVOR. THE MOTION CARRIED UNANIMOUSLY`) N:N is left **`0:0`** — the count is
not in the source and is never invented (see *names_recorded* below).

## Roll-call formats handled (one phrasing per motion block, all case-insensitive)
Blocks split on `^Motion:`; tail trimmed at the result sentence so a block can't pull the
next item's names.
- **ALL-CAPS inline / trailing-verb**: `... CHAIR BRADY, COMMISSIONER GUDMUNDSON VOTED AYE.
  COMMISSIONER BRAMWELL VOTED NO.` — parsed clause-by-clause (a "VOTED NO" clause can't
  reach back across a period and swallow the preceding "VOTED AYE" names).
- **Leading-label**: `Those voting aye: NAMES`, `THOSE WHO VOTED IN FAVOR: NAMES`,
  `ALL IN FAVOR: NAMES`, `ALL IN FAVOR VOTED/SAID YES: NAMES`, `ALL VOTED YES: NAMES`,
  `ROLL FOR YES WENT AS FOLLOWS: NAMES`, plus bare `VOTED YES:`/`SAID YES:` (the bare form
  also rescues OCR mid-word wraps like `ALL IN F\nAVOR VOTED YES:`). Names may be bare
  surnames.
- **Structured (2026)**: `Yes: Commissioners A, B, C.  No: None.  Absent: D.  Motion Passed N-N`.
- **Per-member (rare, 1 file)**: `ROLL CALL WENT AS FOLLOWS: BRAD, YES; DAVID, YES; ...`
  (first names) — mapped via a first-name table used **only** for this parser.
- **Tally-only**: `ALL WERE IN FAVOR` / `THE MOTION CARRIED/PASSED UNANIMOUSLY` with **no
  per-member list** ⇒ `names_recorded:false`, empty member lists, N:N=`0:0`. (13 motions.)

Vote mapping: aye/yes/in favor→Aye, no/nay/against/in opposition→Nay, abstain→Abstain,
recuse→Recuse, absent/excused→Absent. Name lists split on `,`, `;`, `and`, `&`.

## names_recorded convention (cardinal rule: never fabricate)
`names_recorded:true` iff ≥1 member appears in `aye`/`nay`/`abstain`. Tally-only / unanimous
phrasings with no per-member names keep **empty** lists — we never back-fill "who voted"
from attendance.

## Joint City Council + Planning Commission meetings
A few early files (2020-04-01, 2022-10-26) are joint meetings whose minutes embed a **City
Council** roll-call. Motions whose **mover is a councilmember/mayor are skipped** (council
actions, not PC motions); and name resolution is **role-aware** — a `COUNCILMEMBER`/`MAYOR`
token returns no commissioner. This also disambiguates `WELSH`: `COMMISSIONER WELSH` ⇒
commissioner **Jessica Welch** (OCR variant of Welch), while `COUNCILMEMBER … WELSH` (Cristy
Welsh, council) is dropped.

## Roster (appointed body — no elections)
`roster.csv` is reconstructed from each meeting's attendance header (`Commissioners present:`,
`COMMISSIONERS PRESENT:`, `Planning Commission Members:`, per-line `Present:` blocks, joint
`Planning Commission:` sub-blocks). The attendance region starts at the present-header and
ends at the next `Staff`/`Others`/section marker (so staff & residents are excluded — e.g.
resident *Johnny/Jordan Christensen* before he was appointed in 2026). `n_meetings` counts
meetings where a commissioner is **present or appears in a vote** (voting ⇒ presence, which
covers attendance formats the parser can't reach); `first_seen`/`last_seen` also extend over
meetings where the commissioner is listed *excused*.

### Name normalization
Members are stored as **canonical full names** (not surnames) because two distinct people
share the surname **Blackburn** — **Tim Blackburn** (2020–2023) and **Spencer Blackburn**
(2020, 2022). They never co-occur in a meeting, so a `BLACKBURN` roll vote is resolved to
whichever Blackburn is in that meeting's text (default Tim). All other surnames are unique.
OCR/spelling variants are folded in `VARIANTS` (e.g. `GUDMUDSON/GUNDMUNDSON→Gudmundson`,
`STELE/STEEL→Steele`, `RHOTTON/RHOOTON→Rhoton`, `PIERCE→Pearce`, `HRBIN→Harbin`,
`JEKNINS→Jenkins`, `KINGTON→Knighton`, `RASSMUSSEN→Rasmussen`, `WELSH→Welch`). Staff
(e.g. City Engineer **Naseem Ghandour**) and residents are not in the commissioner allowlist
and are dropped, never invented.

### Council appointment cross-check (corroborates the roster)
PC commissioners are appointed by **Council vote** — these appear in `../meeting_minutes/
all_votes.csv` (`motion_type=Appointment`) and corroborate the reconstructed roster:
- 2020-02-26 Amber **Rasmussen** (4-yr term) · 2022-08-10 Tay **Gudmundson** (reappointed) ·
  2022-08-24 Craig **Bown** (alternate) · 2022-09-28 Steve **Anderson** (alternate) ·
  2024-09-25 Natalie **Harbin** (fills Gudmundson's term — matches Gudmundson's roster
  `last_seen` 2024 and Harbin's `first_seen` late-2024). Other appointments
  ("…as presented", 2022-01-12 / 2025-01-29) name no individual in the council motion text.

## Council size over time
Mayor sits on the City Council, **not** the Planning Commission. The PC ran ~5–7 seated
commissioners (incl. alternates) 2020–2025 and **6 voting commissioners by mid-2026**
(2026-05-06 roll: Evans, Fagg, Huntington, Ostler, Pearce, Steele).

## motion_type taxonomy (12-cat, shared with council)
`classify()` keys on motion text in priority order: Public Hearing Action; Procedural/
Administrative (minutes/agenda/adjourn/continue/table/elect/nominate); Ordinance; Budget
Amendment; Grant-Funding; Interlocal; Appointment; **Land-Use/Zoning** (rezone/plat/
subdivision/site plan/CUP/annex/waiver/design/concept/master plan); Contract/Purchase;
Resolution; Ceremonial; else Other. NB generic "forward a positive recommendation to City
Council" motions (no subject keyword) land in **Other** — the recommendation signal lives in
`result`, not `motion_type`.

## Validation (`validate_votes.py` → votes/_validation_report.txt)
- Tally: for `names_recorded` motions with a numeric N:N, N:N must equal the named
  aye:nay counts (abstains tolerated on the No side). A source typo is **FLAGGED, not fixed**.
  Current build: **0 mismatches** (the only two explicit-number motions, 2023-12-06 4-1 and
  2026-05-06 6-0, both match their rolls exactly).
- Roster: every voting commissioner is on `roster.csv` and votes fall within tenure range
  (**0 off-roster, 0 out-of-range**).
- `all_votes.csv` row count reconciles with the JSON member lists.
- 13 expected tally-only motions are listed (procedural "ALL WERE IN FAVOR" + a few
  unanimous recommendations/final actions with no per-member roll).
