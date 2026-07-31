# Orem City PLANNING COMMISSION — vote extraction pipeline

Roll-call votes extracted from the Orem **Planning Commission** meeting minutes (markdown),
modeled on the City Council pipeline in `../meeting_minutes/`. Everything derived is
regenerable from the minutes by re-running the parser.

PURE PYTHON / REGEX. No LLM, no Anthropic SDK, no network calls anywhere in this pipeline.

## Layout

```
planning_commission/
├── minutes_index.csv                 # one row per recovered meeting (date,year,title,slug,path,source,source_url,format)
├── minutes_unrecovered.csv           # 17 in-range meetings with no usable published minutes
│                                     # (16 never published + 2025-10-15, whose only published
│                                     #  "Approved Minutes" is a city-side mis-upload of the 11-05 doc)
├── minutes/<year>/<week-monday>/<date>_planning-commission-meeting.md   # 114 source minutes
├── extract_votes.py                  # the parser/pipeline (run from anywhere)
├── validate_votes.py                 # consistency + roster + reconciliation checks
├── all_votes.csv                     # LONG format, one row per member-vote (rebuilt)
├── roster.csv                        # commissioners, years active, vote tallies, council-appointment date
├── votes/<year>/<week>/<date>_planning-commission-meeting.json   # per-meeting structured (114 files)
├── votes/_validation_report.txt      # written by validate_votes.py
├── report.json                       # acquisition + extraction summary
└── CLAUDE.md                         # this file
```

Run:  `python3 planning_commission/extract_votes.py`  then  `python3 planning_commission/validate_votes.py`
(idempotent: overwrites the JSONs, `all_votes.csv`, `roster.csv`).

## Current results (last run)

- **pc_meetings_parsed: 114** (every index row; the other 17 in-range meetings have no usable
  published minutes — see `minutes_unrecovered.csv`; 16 were never published, and the
  2025-10-15 meeting's only published "Approved Minutes" is a city-side mis-upload of the
  2025-11-05 document, removed 2026-07-02 — see `../VERIFICATION.md`).
- **motions: 562** (501 named roll-calls + 61 tally-only).
- **member_vote_rows: 2997** · vote labels seen: **Aye 2931, Nay 58, Abstain 8**
  (no Recuse/Absent rows — see below).
- **contested motions (any Nay or Abstain): 34**.
- **recommendations: 113 · final actions: 221 · procedural: 228** (action classes).
- **ocr_meetings: 6** · format breakdown: text 91, docx 17, ocr 6.
- **distinct commissioners: 25** across 2020–2026.
- **validation: ALL CHECKS PASS** — JSON↔CSV reconcile OK, 0 off-roster members,
  0 tally/consistency issues, 0 meetings missing a JSON.
- **113 of 114 meetings produced votes**; the 1 vote-less meeting (`2025-04-02`) is a
  correct non-failure — a General-Plan study/discussion session with no motions.

`all_votes.csv` columns (EXACT 13, same schema as the council CSV): `date,year,title,body,
motion_no,motion,motion_type,result,mover,seconder,member,vote,source`. Every row has
`title="Planning Commission"` and `body="PlanningCommission"`. `vote ∈ {Aye,Nay,Abstain}`
(Recuse/Absent never occur — Orem PC records recusal only as narrative "recused himself
from the item", i.e. the member leaves and does not appear in any vote list, so we never
synthesize a Recuse/Absent row; CARDINAL RULE: never fabricate).

## How Orem PC records votes — THREE formats, all handled

**(A) Classic prose roll-call** (2020–2024, all OCR, all docx) — the authoritative form:
```
Planning Commission Action: Jim Condie moved to vacate Lot 1 of Tucker Subdivision, Plat B
and approve the preliminary plat of Rolling Sand Subdivision, Plat A ... Amber Pope seconded
the motion. Those voting aye: Haysam Sakar, Jim Condie, Amber Pope, Madeline Komen, Tina
Okolowitz, and Murray Low. The motion passed unanimously.
```
`Those voting aye:` / `Those voting yes:` (+ optional `Those voting nay:`/`no:`,
`Those abstaining:`), full names, then a `(The )Motion passed/failed/did not pass` outcome.
Movers/seconders appear as full names or titled short forms (`Mr. Roberts`, `Commissioner
Erickson`, `Vice Chair Carpenter`, `Chair Komen`).

**(B) Late-2025/2026 labelled-block roll-call** (8 files) — ALL-CAPS labels:
```
Planning Commission Action: Vice Chair Mike Carpenter motioned to approve ... Rod Erickson
seconded the motion.  YES: Madeline Komen, Mike Carpenter, Rod Erickson, Jerry Crismon
NO: None   ABSTAIN: None
```
The block label regexes (`YES:`/`NO:`/`ABSTAIN:`) are **case-SENSITIVE** so they never match
a lowercase "... yes." inside ordinary prose. The outcome may be a **separate** sentence
("the motion failed" under a 4-vote supermajority rule even with aye>nay — see 2025-12-17
Rolling Sand) or **absent** (then the majority of the recorded names decides pass/fail).

**(C) Mid-2025 summary minutes** (~12 files) — **tally-only, NO per-member names**:
```
Commissioner Hawkes made the motion, and Commissioner Carpenter seconded. The motion passed
unanimously.   /   Motion to approve the Preliminary Plat made and seconded. Motion passed 5-0.
```
Recorded with `names_recorded=false`, **EMPTY member lists** (so they contribute **0** rows
to `all_votes.csv`), `mover`/`seconder` when a name precedes the verb (else blank). A printed
numeric tally ("5-0") is captured into `result`; individual voters are **never invented**.

A page-footer scrubber (`A complete video … www.orem.org/meetings`, `A recording … youtube`,
`Planning Commission minutes for <date>`, `(p.N)`, `DRAFT`) and an all-caps line-anchored
`MINUTES FOR <DATE>` page-header scrubber run **before** flattening so wrapped name lists
rejoin. The header scrubber is case-sensitive and full-line-anchored on purpose — a
case-insensitive "minutes for <date>" pattern would eat the legitimate "moved to approve the
meeting **minutes for** January 15, 2020" inside a real motion.

## `result` — machine-detectable PC disposition (action class + tally)

The **action class is decided on the MOTION TEXT only** (never the forward window, so an
adjacent item's "Staff recommends …" can't reclassify the current motion):

- **Recommendation to the City Council** — motion text contains `recommend(ation)`
  (rezones, plats, subdivisions, General-Plan amendments, annexations, code/ordinance
  amendments forwarded to Council):
  `Positive recommendation A:N` / `Negative recommendation A:N` / `Neutral recommendation A:N`
  (`… (Failed)` appended when the recommendation motion itself failed). Direction comes from
  the motion text first, then the immediate disposition sentence.
- **Final action by the PC itself** — approve/deny/vacate/grant (conditional use, site plan,
  plat amendments the PC approves outright):
  `A:N Approved (Final Action)` / `A:N Denied (Final Action)`. Disposition reflects the
  **item**: a *motion to approve* that **failed** ⇒ `Denied (Final Action, motion failed)`;
  a *motion to deny* governs inversely.
- **Procedural** — minutes / consent / continue / table / postpone / reconsider / adjourn /
  agenda / calendar / **officer elections** (elect/appoint Chair & Vice-Chair):
  `A:N Pass` / `A:N Fail`.

Tally-only motions (format C) drop the `A:N` unless the minutes printed a numeric tally.
The pass/fail word comes from the verbatim `(The) Motion passed/failed/did not pass/was (not)
approved` outcome (case-insensitive prose; explicit fail cue beats a pass cue; otherwise
majority of recorded names).

## `motion_type` taxonomy (subject; text-first)

`Procedural/Administrative` 225 · `Plat/Subdivision` 139 · `Site Plan` 55 ·
`Code/Ordinance Amendment` 41 · `Rezone` 38 · `General Plan` 13 · `Conditional Use` 8 ·
`Appointment` (officer elections) 2 · `Annexation` 1 · `Other` 40 (genuinely ambiguous:
naming a ball field, "adopt the EDSP", "amend the Agreement", a few condominium plat
amendments). Note `motion_type` (subject) is orthogonal to the action class encoded in
`result`.

## Name normalization

PC roll-call lists print **full names**, so vote-list members are taken verbatim and only
spelling/OCR drift is folded (`extract_votes.py` `FULLNAME_VARIANTS` + `SURNAME_CANON`):
- Gerald / **Jerry** Crismon, **Crimson**, council-minutes **Grismon** → **Gerald Crismon**
- James / **Jim** Hawkes, **James (Jim) Hawkes** → **James Hawkes**
- **Murry** Low → **Murray Low** · **Saakar/Haysatn** Sakar, "(via Zoom)" → **Haysam Sakar**
- 2026 near-total turnover, OCR drift: **Radmill→Karl Radmall**, **Ladel→Micah Ladle**,
  plus Darren Hawkins, Jeff Reeves, Susan Madsen.
Movers/seconders given as titled short forms (`Mr. Roberts`, `Commissioner Erickson`,
`Vice Chair Carpenter`, `Chair Komen`) are stripped of the title and resolved by surname
(`resolve_actor`). Council **liaisons / staff** (Dave Spencer, Crystal Muhlestein, Jared
Hall, Grant Allen, legal counsel, …) are in a `NON_COMMISSIONERS` block-list so a noisy
capture can never emit them as a voting member. Unknown single-token captures are dropped
(never emitted) rather than guessed.

To add a new commissioner or spelling, extend `FULLNAME_VARIANTS` + `SURNAME_CANON`.

## Roster

`roster.csv` = the 25 commissioners seen in recorded votes (and in `Those present/excused`
PC-member segments), with `first_year,last_year,years_active,vote_motions,aye,nay,abstain,
in_recorded_votes,council_appointment_date`. Per-year counts exceed 7 in transition years
(2022 = 13, 2026 = 12) because the **7-seat** commission turned over mid-year — that is real,
not duplication. OCR variants are folded to one canonical name before counting.

**Appointment cross-check** (`pc_appointments_from_council`): PC commissioners are appointed
by the City Council, so the parser scans `../meeting_minutes/all_votes.csv` for "appoint X to
the Planning Commission" motions. Found: Madeline Komen, Amber Pope, Murray Low (2022-01-25),
Gerald Crismon (2022-05-10). Pre-2022 commissioners' appointments predate the council vote
data window (same caveat as the council pipeline) — a sanity flag, not an error.

## Known limitations (truthful, not failures)

- **52 procedural motions** (mostly "Chair X called for a motion to adjourn / approve the
  minutes **and moved**…") have a blank `mover` — no name sits directly before "moved", and
  attributing it to the chair would be a guess, so it is left blank (CARDINAL RULE). Members,
  seconder, result are still captured.
- A handful of format-C summary motions have terse motion text (the minutes themselves are
  terse); disposition/result/classification are still correct.
- 6 OCR-sourced meetings are lower fidelity; born-digital `text`/`docx` were preferred where
  available. OCR vote blocks parsed cleanly (spot-checked 2024-09-18: 5 motions, all 7-0,
  movers/seconders incl. "Mr. Crimson"→Gerald Crismon correct).

## Validation performed

`validate_votes.py`: JSON↔CSV row reconciliation, 0 off-roster members, per-motion
consistency (no member in both aye&nay, ≤7 voters, non-empty lists when `names_recorded`,
outcome vs tally), every index row has a JSON. **All pass.** Hand spot-checks vs source:
2022-06-15 (recommendation vs final-action plats), 2023-12-06 (2:2 Failed + abstain),
2025-12-17 (labelled-block + supermajority fail + reconsider), 2025-07-02 (anonymous
tally-only), 2024-09-18 (OCR) — all exact.
