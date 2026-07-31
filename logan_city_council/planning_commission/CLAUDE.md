# planning_commission/ — Logan Planning Commission vote extraction

Turns 130 minutes markdown (2020–2026) into structured PC motions + roll-call votes.
Entry point: **`extract_votes.py`** (reads `minutes_index.csv`); validator: **`validate_votes.py`**.
Modeled on `../meeting_minutes/extract_votes.py` (same vendor/Revize), adapted to the PC format.

## Coverage (verified — `validate_votes.py` PASS)
**130 meetings · 549 motions · 2,629 member-vote rows · 60 contested · 2020–2026.**
112 recommendations · 242 final actions · 195 procedural · 113 tally-only (no per-member names).
**52 OCR meetings (200 motions) / 78 born-digital text.** 15 distinct commissioners.

## Format (per-member roll call)
```
MOTION: Commissioner Newman moved to recommend approval to the City Council for a
zone change as outlined in PC 20-014. Commissioner Croshaw seconded the motion.
   ...(RECOMMENDED CONDITIONS / FINDINGS — often 50–150 lines)...
Moved: D. Newman  Seconded: R. Croshaw  Approved: 5-1
Yea: Croshaw, Dickinson, Lucero, Newman, Ortiz  Nay: Nielson  Abstain:
```
- **Primary anchor** = the `Moved: … Second(ed): … Approved|Denied|failed: a-b` summary line
  (gives mover, seconder, numeric tally). **2025–2026 files use `Second:` (no "-ed")** — handled.
- The **next** line `Yea: … Nay: … Abstain: …` is the per-member roll call (surnames only).
- The **motion text/subject** (incl. the `PC ##-###` id) comes from the preceding `MOTION:`
  header; we scan backward to it, stopping if we cross a prior `Moved:` line.
- **Procedural prose motions** (minutes approval, adjournment, agenda) appear inline as
  "Commissioner X moved to / made a motion to … The motion was approved unanimously." with
  **no** summary line and **no** names → `names_recorded:false`, `result:"Pass (unanimous)"`.

## CARDINAL RULE — never fabricate
- **yea/nay/abstain counts come from the NAMED `Yea:/Nay:/Abstain:` lists, not the numeric
  tally.** The `Denied: a-b` orientation is inconsistent in the source (sometimes nay-first
  e.g. 2020-03-12, sometimes yea-first e.g. 2020-08-13), so the names are authoritative and the
  tally is kept only as `tally_text` for cross-check.
- Tally-only / "approved unanimously" with no per-member names → `names_recorded:false`, EMPTY
  member lists. We never invent the members behind a unanimous tally.
- When the source names FEWER members than its own tally (clerk omission), we keep the names as
  written and the validator flags it (see "Known discrepancies"). We never pad to the tally.

## Recommendation vs final action (encoded in `result`)
Logan PC motions don't label this, so we infer from the **motion verb**:
- motion text contains **"recommend"/"forward"** → recommendation →
  `"Positive recommendation N:N"` / `"Negative recommendation N:N"` (DB → `pc_recommendation`).
- otherwise → final action → `"N:N Approved (Final Action)"` / `"N:N Denied (Final Action)"`
  (DB → `pc_final_action`). Default-to-final-action when no recommend/forward verb (per spec).
- procedural (continue/table/minutes/elect chair/adjourn/recess/withdraw/agenda) →
  `"N:N Pass"` (or `"Pass (unanimous)"`/`"Fail"` when no numeric tally).

**Direction** = XOR of *(motion proposes approval)* and *(motion passed)*, where pass/fail is taken
from named counts (yea>nay). So a **failed "recommend approval"** → *Negative recommendation*
(e.g. 2020-03-12 PC 20-014, 2:4) and a **carried "deny"** → *Denied (Final Action)* (e.g.
2020-08-13 PC 20-011, 5:2). Subdivision/CUP denials with no "forward to Council" wording are
treated as **final actions**. N:N is always written yea:nay.

## Roster (`roster.csv`: commissioner, first_seen, last_seen, n_meetings)
PC is **appointed** (Council ratifies; no election). Built from per-meeting
`Commissioners Present:` headers (multi-line, OCR variants folded) **unioned with** anyone who
moved/seconded/voted that meeting. 15 commissioners 2020–2026. Roll-call lines carry **surnames
only**; mapped via `SURNAME_MAP` (+ `FIRST_MAP` for OCR given-name-only cases) with a difflib
fuzzy fallback for OCR misspellings: `Crowshaw/Royland→Croshaw`, `Petersen→Peterson`,
`Daivd→Lewis`, `Here→Heare`. Variants folded: `Sandi/Sandy Goodlander`, `Jess/Jessica Lucero`.

**Council appointment cross-check** (`../meeting_minutes/all_votes.csv`, `motion_type=Appointment`
"approve ratification of …"): ratification dates precede PC `first_seen` by ~2–3 weeks for Guth
(2021-04-06→04-22), Lewis & Heare (2021-05-04→05-13), Doutré & Peterson (2022-02-15→03-10),
McNamara (2024-07-16→08-22), Duncan (2025-04-15→04-24), Maughan (2026-01-20→02-26) — roster
confirmed. Caveat: council "Bill Peterson" (other boards) ≠ commissioner **Eldon Peterson**; a
2021 "Jennifer Duncan" ratification predates her 2025 PC service (likely another board/term).

## OCR notes (52/130 files, mostly late-2023 → 2026, `format=ocr` in index)
Moved/Yea lines survive OCR fairly cleanly; quirks handled: `Second:` vs `Seconded:`; digit/letter
confusion in tallies (`7-O`→7-0, `l/I`→1); merged surnames with a dropped comma
(`"Lewis Peterson"` → both recovered by whole-word roster scan); stray `| =` chars; mangled
attendee headers. **4 OCR meetings have no parseable `Commissioners Present:` header**
(2024-02-08, 2024-02-22, 2024-08-08, 2024-12-12) — their attendees still enter the roster via
vote participation; `present:[]` in those JSONs.

## Known discrepancies (advisory; NOT fabricated)
5 motions where the source `Yea:` list names fewer members than its own numeric tally (clerk
omitted a name): 2020-03-12 m3 (6 vs 7), 2024-02-08 m2 (5 vs 6), 2025-07-10 m1 & m2 (6 vs 7),
2025-11-13 m2 (6 vs 7). Kept as written; listed by `validate_votes.py`.

## Outputs
- `votes/<year>/<week-monday>/<date>_planning-commission-meeting.json` — one per meeting
  (`present` + `votes[]` with mover/seconder/aye/nay/abstain/result/kind/tally_text/names_recorded).
- `all_votes.csv` — 13-col long format matching council schema
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  **`body="PlanningCommission"` and `title="Planning Commission"` on every row.**
- `roster.csv`, this file.

## Re-run
`python3 extract_votes.py` (resumable: skips meetings whose JSON exists; `--force` to rebuild all),
then `python3 validate_votes.py`.
