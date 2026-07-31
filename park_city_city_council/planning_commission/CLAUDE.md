# planning_commission/ — Park City Planning Commission vote extraction

Turns 160 minutes markdown (2020–2026, CivicClerk) into structured roll-call votes for the
**Planning Commission** — a separate, APPOINTED body from the City Council (`body=PlanningCommission`
on every row). No mayor, no elections; the Chair is a seated commissioner and **votes like any member**.
Entry point: **`extract_votes.py`** (resumable; `--force` re-extracts). Validate with **`validate_votes.py`**.

## Format (`MOTION:` / `VOTE:` convention — and the 2024-10-09+ **folded** grammar)
```
MOTION: Commissioner Kenworthy moved to forward a NEGATIVE recommendation to the City
        Council ... Commissioner Suesser seconded the motion.
VOTE:   Commissioner Kenworthy-Aye; Commissioner Hall-Nay; Commissioner Johnson-Aye;
        Commissioner Van Dine-Nay; Commissioner Suesser-Aye. The motion passed 3-to-2.
```
**Folded grammar (sporadic from 2024-06, UNIVERSAL from 2024-10-09 onward):** the separate
`VOTE:` marker was DROPPED and the outcome sentence is folded INTO the `MOTION:` block
(optionally with a `Vote on Motion:` per-name roll call and/or a prose named-dissent clause):
```
MOTION: Commissioner Van Dine moved to APPROVE the Plat Amendment for 2411 Main ...
        The motion was seconded by Commissioner Sigg. The motion passed with the
        unanimous consent of the Commission.
MOTION: Commissioner Johnson moved to APPROVE the CUP ... The motion passed 5-to-1 with
        Commissioner Frontero voting Nay.
```
`extract_votes.py` emits a motion whether its outcome sits after a `VOTE:` marker OR is
folded in the `MOTION:` block; a `MOTION:` block with NO outcome sentence anywhere (e.g. a
bare "moved to ADJOURN") is honestly dropped, never given a fabricated result. Prose
dissent inside a folded outcome ("voting Nay", "voted against", "abstaining", "abstention
from Commissioner X", the repeated-prefix "Commissioner X and Commissioner Y voted 'No'")
is attributed to the named dissenter/abstainer (`names_mode='partial'`) WITHOUT overriding
the printed tally — the majority stays unnamed. Full `Vote on Motion:` roll calls set
`names_mode='rollcall'`; pure tally-only sets `names_mode='tally'`.

VOTE forms (`VOTE:`-marked or folded):
- **Per-name roll call** (~52 full roll calls): `Commissioner X-Aye; Commissioner Y-Nay; … The
  motion passed N-to-M.` — either `VOTE:`-marked (classic) or a folded `Vote on Motion:` list
  (2024-10-09+). (also `-Yes`/`-No`; role words `Chair X-Aye` map to the seated person). Captured
  across line wraps with `[\s\S]`, comma/semicolon/"and" separators.
- **Tally-only** (~780): `The motion passed with the unanimous consent of the Commission.` /
  `The motion passed unanimously.` → `names_recorded:false`, member lists left EMPTY (never guessed).
- **Partial (name-only-dissenters, ~19):** a printed tally with only the dissenter(s)/abstainer(s)
  named in prose — `The motion passed 5-to-1 with Commissioner Frontero voting Nay`; `…4-0, with
  an abstention from Commissioner Suesser`; `…unanimously with one abstention by Commissioner
  Johnson`. Named dissent captured, tally kept authoritative, majority unnamed.
- **`The motion failed for lack of a second.`** → failed motion, no roll call.

## Recommendation vs final action (`action_type`)
PC business is land-use heavy. A motion is one of:
- **Recommendation** — "forward a POSITIVE/NEGATIVE recommendation to the City Council" on a
  plat / MPD / rezone / annexation / LMC amendment (Council casts the binding vote).
- **Final Action** — CUPs, design review, appeals, steep-slope permits are usually PC-final.
- **Procedural** — minutes, continuances, adjournment, chair elections.

`result` encodes direction + tally: `Positive recommendation 4-1`, `Negative recommendation 3-2`,
`Denied 2-3`, `Approved 5-1`, `Continued unanimous`. The direction label uses the motion's
**operative (earliest) verb**, so a later "denial" inside a Conditions-of-Approval block can't
flip an APPROVE motion to "Denied".

## Source-quality fixes baked in
1. **Watermark filter** — the `-layout` PDF→text stamps a vertical "APPROVED"/"DRAFT" watermark +
   page numbers as stray short tokens on their own lines (`D`, `O`, `VE`, `ed`, `ro`, `Ap`, `03`).
   `clean_lines()` drops lone ≤4-char alpha / ≤3-digit lines and the repeated page-header block
   (`Park City Municipal Corporation` / `Planning Commission Meeting` / a date line) BEFORE parsing,
   so they can't split a `Commissioner X-\n <noise> \n Vote` sequence or corrupt motion text.
2. **Line-wrap capture** — roll-call lists and motion text are flattened across wraps and injected
   page headers.
3. **OCR/spelling folds** — `VanDine`/`Van Dine`→Christin Van Dine, `Kenworth`→Kenworthy,
   roster keys `Sara`→Sarah Hall, `Rich`→Rick Shand. Full-name movers ("Commissioner Christin Van
   Dine moved", 3 tokens) resolved by trailing surname. Names not on the 14-member roster (staff,
   applicants, public) are **dropped, never invented**.
4. **Mislabeled marker guard** — a `VOTE:` line that is really a motion ("VOTE: Commissioner X moved
   to …", no outcome sentence) is re-parsed as the pending MOTION (1 occurrence in corpus).

## Roster (14 appointed commissioners, keyed on surname)
Phillips (Chair ’20–’22) · Sletten · Thimm · Kenworthy · Hall (later Chair) · Suesser · Van Dine
(later Vice Chair) · Johnson · Frontero · Sigg · Shand · Tilson · Beal · Strachan. Date ranges +
per-year observed roster are asserted by `validate_votes.py`. Classic per-name `VOTE:` roll
calls appear 2020–2024; from 2024-10-09 the folded grammar (above) makes most motions
tally-only unanimous-consent, but NOT all — folded meetings still carry `Vote on Motion:`
roll calls and prose named dissent (e.g. 2025-03-26, 2025-04-23, 2026-04-22, 2026-05-13), so
2025–2026 commissioners (Tilson, Beal, Strachan) DO have per-name rows where they dissented.
(Sletten's 2020 tenure is short + tally-only, so he has no per-name row — that one is expected.)

## Coverage (verified, re-extracted 2026-07-19, +1 after the post-audit token-strip repair)
**162 meetings · 873 motions · 1,086 rows · 52 contested · 198 recommendations · 208 final actions · 2020–2026.**
0 names off-roster, 0 out-of-range appearances, 0 roll-call tally mismatches (full roll calls);
20 motions are `names_mode='partial'` (folded name-only-dissenters — dissenter/abstainer named
beside a printed tally, so `validate_city f.tally[planning_commission]` reports 51/59 = 86.4% by
design, NOT a defect).

### 2026-07-19 folded-outcome parser fix (HIGH-priority Q3 refresh item)
Before this fix `parse_meeting()` only emitted a motion paired with a following `VOTE:` marker,
so **every motion in the folded grammar (2024-10-09 → 2026-06-24) was silently dropped** — 40
folded-era meetings, **264 motions / 289 member-vote rows recovered** (incl. named dissent that the
old note wrongly claimed was never lost: 2025-03-26/04-23/11-12, 2026-04-22/05-13). The fix also
recovered **6 sporadic pre-2024 folded/mislabel cases** (2020-03-11 the mislabeled-outcome
`MOTION:` "The motion passed 4-1" with Suesser dissenting; 2021-11-17; 2023-01-18; 2024-06-12 ×3),
each source-verified; the rest of the pre-2024-10-09 corpus is byte-identical (0 rows removed).
(A line-wrap that split "The\nmotion" hid some outcomes until `folded_vote_window` was made
whitespace-robust.) See `../_backups/2026-07-19-parkcity-pc-parser/`.

### 2026-07-19 post-audit token-strip repair (audit fixes #1 + #2)
The folded fix above verified its reconciliation on an **11-meeting folded sample that EXCLUDED
2024-11-13**, so its "0 mismatches / all folded meetings reconcile" claim was overstated — one
un-fixed root cause remained: the `-layout` conversion sometimes stamps a page-number/watermark
token **with a trailing period** as a lone line (`1.`, `3.`, `7.`, `8.`, `0.`, the watermark letter
`D.`). `clean_lines()` dropped only the period-LESS shapes, so this dotted furniture survived wedged
between "The motion" and its outcome verb and severed the folded outcome sentence at the spurious
period. Effect: **1 motion silently dropped** (2024-11-13 the Johnson/Sigg unanimous-consent motion
to CONTINUE to Jan 8, 2025 and amend Conditions of Approval #13 & #16) and **6 result strings garbled
to a bare `Approved`** (2024-11-13 m5, 2025-06-25 m3, 2025-08-13 m4, 2026-01-14 m4, 2026-05-27 m6,
2025-04-02 m6). Fix (in `folded_vote_window`, NOT global `clean_lines`, so stored motion text stays
byte-identical): drop lone dotted-furniture lines from the outcome window before the whitespace
collapse, plus a tightly-guarded reunification for the one scrambled 2025-04-02 "D" layout (the
completion "unanimous consent of the Commission." was hoisted above a truncated "passed with the D."
head — both verbatim fragments spliced back, never inventing words). **Result: 872→873 motions /
1,085→1,086 rows**; all 6 healed to their true `passed with the unanimous consent of the Commission`
form (outcome/disposition unchanged — they were already correct); **contested unchanged at 52**;
everything before 2024-11-13 byte-identical; derived chain (db with the 9 vote-overrides + 2 mayoral
tie-breaks intact, +12 PC→Council referrals, weeks, motions_std) rebuilt; `validate_city` 0 FAIL.
Backups: `../../_backups/2026-07-19-audit-fixes/park_city/`.

## Outputs
- `votes/<year>/<week>/<date>_planning-commission-meeting.json` — one per meeting.
- `all_votes.csv` — long format, one row per member-vote (`csv.writer`, comma-safe):
  `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`.
  Tally-only motions emit one row with empty `member`/`vote`.
- `votes/_validation_report.txt` — counts, per-year roster, contested list, integrity checks.

## Run
```
python3 planning_commission/extract_votes.py            # resumable
python3 planning_commission/extract_votes.py --force     # rebuild all
python3 planning_commission/validate_votes.py            # report
```

## Cross-body project crosswalk
`project_timeline.csv` (built by `build_project_timeline.py`) links these PC votes to the **council's**
votes on the same development project — a long-format trace: `project, spans_both_bodies, date, body,
stage, result, dissenters, motion, source`. **Stages**: PC `recommendation` (positive/negative, forwarded
to Council), PC `final action` (CUP/design-review/steep-slope — PC is final, never reaches Council),
`Council vote`. 47 projects (32 span both bodies). It's a **heuristic text-join** on the project name in
the motion field — a navigation aid; spot-check before quoting. Rebuild: `python3 build_project_timeline.py`.
