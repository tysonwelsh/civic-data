# South Jordan City — Planning Commission subtree

Parallel dataset for South Jordan's **Planning Commission**, sibling of `meeting_minutes/`,
built to the same schemas (SCHEMA_SPEC.md applies in full). Every `all_votes.csv` row is
`body=PlanningCommission`. Data floor **2020**.

## Files
- `minutes/<year>/<week>/<date>_planning-commission*.md` — 125 PC minutes (CivicPlus +
  PMN), indexed in `minutes_index.csv`. Meetings noticed but with no minutes ever posted are
  in `minutes_unrecovered.csv` (3 early-COVID electronic meetings). Raw PDFs in `raw/`.
- `all_votes.csv` — long format, one row per member-vote (or one placeholder row per
  tally-only motion), the standard 13 columns. **730 motions across 123 meetings; 797 data
  rows.**
- `votes/<year>/<week>/<date>_*.json` — the resumable per-meeting intermediate. Carries
  normalized fields **alongside** the verbatim `result`: `tally_aye`/`tally_nay`,
  `action_kind` (recommendation / final_action / procedural / other), `file_numbers`, and
  the `present`/`absent_header` attendance lists. `all_votes.csv` is rebuilt from these.
- `roster.csv` — 13 commissioners observed (from Present/Absent header blocks + named votes):
  `commissioner, first_seen, last_seen, meetings_present, vote_rows`.
- `extract_votes.py` — PURE deterministic parser (no LLM, no network; resumable).
- `validate_votes.py` — the sanity report (totals, per-year roster, tally-vs-named
  consistency, plausibility, contested list).

Run: `python3 extract_votes.py` then `python3 validate_votes.py`.

## Vote grammar — NARRATIVE TALLY, majorities honestly UNNAMED
South Jordan's clerk records votes as a **narrative tally**, never a per-name roll-call
block. So — exactly like Sandy's council inline-tally form — the winning **majority is
never named**; only **dissenters and absentees are named**. The parser therefore:
- **Unanimous** (`"Roll Call Vote was 5-0, unanimous in favor."` / `"Vote was 4-0 …"` /
  `"Vote was unanimous in favor."` with no number): tally captured, **no individual aye
  names** (`names_recorded:false`) → one placeholder row. The X ayes are never guessed.
  (231 motions use the number-less `"unanimous in favor"` form — faithful, not a gap.)
- **Named dissent** (`"6-1 with Commissioner Bevans voting No."` / `"3-2 … with Chair
  Hollist and Commissioner Bevans issuing no votes."` / `"… Commissioner Darby was a no
  vote."` / `"no votes made by Commissioner Bevans, Chair Hollist, and Commissioner
  Catmull."` / `'Chair Hollist gave "no" vote.'`): the named dissenter(s) → `Nay` rows; the
  majority stays **unnamed** (`names_recorded:false`). 12 motions.
- **Unnamed dissent** (`"3-2, majority of negative votes."` — a contested tally with no name):
  tally recorded, dissenters **blank** (never invented). 2 motions.
- **Named absentees** (`"Commissioner Bishop and Commissioner Harding were absent from the
  vote."`) → explicit `Absent` rows (a source statement, not a guess). Named abstentions →
  `Abstain` rows.
- **Mover/seconder** captured on every motion (incl. the `"Commissioner X said I move that…"`
  quote form). **Case numbers** (`File No. PL…` — PLCUP/PLSPR/PLPP/PLPLA/PLZBA/PLZTA/PLADU/…)
  are pulled into the JSON `file_numbers` (feeds referrals). 29 motions leave `mover` blank —
  genuine long-distance/public-hearing-context votes where no motion phrase sits within the
  backward window; left blank rather than mislinked.

`result` and the numeric tally are **verbatim as printed**. `motion_type` (fixed 12-cat) and
the `action_kind` recommendation-vs-final-action split live **alongside**, per the PC
playbook: rezones / general-plan / code-or-text amendments / annexations are *"positive/
negative recommendation to City Council"* (recommendation); CUP / site-plan / plat /
subdivision / dwelling-unit items are PC **final actions**. Distribution: 388 procedural,
205 final_action, 95 recommendation, 42 other.

## Parsing guards (why counts are trustworthy)
- The parseable region is **cut at the "true and correct copy" clerk-certification line** so
  quoted prior-meeting motions inside post-adjournment attachments (a real hazard in 2 files)
  can never fabricate a phantom motion. Reconciliation: **730 raw vote-clauses = 730 parsed
  motions**, 0 phantom / 0 drop.
- Commissioner names resolve through a fixed surname→canonical-name canon (folds OCR/first-
  name variants: Steve→Steven Catmull, Michelle/Michell→Michele Hollist, Trever→Trevor Darby,
  Hading→Lori Harding, Stark→Aaron Starks). Surnames are unique across the SJ PC, so
  resolution never collides. Roster is built from title-prefixed **and** bare known-surname
  mentions in the Present block (the clerk sometimes drops the "Commissioner" title).

## Roster (13 commissioners, appointed not elected)
Michele Hollist (Chair), Nathan Gedge, Steven Catmull, Trevor Darby, Laurel Bevans, Sean
Morrissey, Sam Bishop, Aaron Starks, Ray Wimmer, Lori Harding, Bryan Farnsworth, Michael
Peirce, Brad Sanderson. No mayor; the Chair/Vice-Chair vote like any member. Commission has
~7 seats; observed tallies run 3-0 … 6-1 (denominator derived empirically per meeting).

## Known source anomaly (faithful capture, NOT fixed in place)
- **2022-10-11 motion 4** — the minutes print *"Roll Call vote was 4-0, no votes made by
  Commissioner Bevans and Chair Hollist … Motion passed with majority of votes in favor."*
  The `4-0` tally contradicts the two explicitly-named no-votes (almost certainly a clerk
  typo for `4-2`). Per the cardinal rules the tally is kept **verbatim** and both named nays
  are captured faithfully; `validate_votes.py` surfaces it as the sole WARN. Any correction
  belongs in a documented override file, never an in-place edit.

## validate_votes.py result
125 meetings · 123 with ≥1 motion · 730 motions · 797 rows · **off-roster names 0 · vote-
vocabulary clean · named-nay vs printed-tally mismatches: 1 (the documented 2022-10-11 m4
source contradiction) · all tallies within 1..7 voters**. Classification: 485 unanimous /
12 named-dissent / 2 tally-only dissent. Corpus screen (audit skill) is clean (all years
dict-ratio 0.77–0.84, 0 PUA/OCR outliers).


## 2026-07-17 — PMN crosscheck: PC 2024-05-14 promoted
Recovered the FINAL 05-14-2024 PC minutes from Utah PMN (file 1128177, notice 912655; repo
previously had 05-28 and 06-25 but not 05-14). source=pmn/format=pdf-text; +6 motions
(all 5-0, Wimmer absent). Raw: `raw/2024-05-14_planning-commission.pdf`.
