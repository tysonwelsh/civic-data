# planning_commission/ — Taylorsville Planning Commission vote extraction

Turns **91 PC minutes** (2020-01 → 2026-04, CivicEngage) into structured motions +
votes. Entry point **`extract_votes.py`** (reads `minutes_index.csv`, PURE deterministic —
no LLM/network, resumable); validator **`validate_votes.py`** (writes
`votes/_validation_report.txt`). Same schema as council; every `all_votes.csv` row
`body=PlanningCommission`, `title="Planning Commission"`.

## Coverage (verified — `validate_votes.py` PASS)
**91 meetings · 324 motions · 761 member-vote rows · 61 contested · 2020–2026.**
58 recommendations (47 pos / 9 neg / 2 failed) · 81 final actions · 185 procedural.
**112 named motions · 212 tally-only** (unanimous/consent — names not printed).
**31 OCR meetings (101 motions) / 60 born-digital.** 12 commissioners in `roster.csv`.
1 meeting (2024-12-03, a Special Work Session) has 0 motions (no formal vote — honest).

## Vote grammar — THREE formats, one `MOTION:` anchor
The `MOTION:` header (also `3.6 MOTION:` / `MOTION #1:`) anchors every year; the vote
resolution takes three shapes, all handled:
1. **Narrative tally** — `VOTE: All Commissioners voted in favor. Motion passes
   unanimously.` / `Motion passes 6 to 1.` → tally-only, **names NOT listed on
   unanimous** → `names_recorded:false`, empty member lists (never invented).
2. **Named inline roll-call** — `VOTE:/ROLL CALL VOTE: Commissioner Wright – AYE,
   … Commissioner Willardson – NAY.` (labels wrap across pdftotext line breaks → the
   region is flattened; the dash separator is optional — some clerks drop it).
3. **Tabular roll-call** (2024-12+) — one member per line `Commissioner Quigley  Aye` /
   `Chair McElreath: Aye` then `Motion Passed 5-0` (page-break footers flattened out;
   trailing OCR punctuation `AYE :`/`ABSTAINED ;` tolerated).
Prose exceptions (`passed unanimously, although Commissioners Wendel and Wilkey
abstained`, `with Chair Wilkey recusing herself`, `one abstention (Commissioner
Wilkey)`) capture the **named** abstainer/recuser while the unnamed majority stays
tally-only. Header-less tabular votes (2024-10-22) are recovered by a secondary pass.

## Result / direction taxonomy (encoded in `result`, city-faithful tally kept verbatim)
- **Recommendation** (`send/forward a positive/negative recommendation to the City
  Council` — rezones / text amendments / general-plan / plats): `Positive
  recommendation N-M` / `Negative recommendation N-M`; a FAILED rec is
  `… recommendation — motion failed N-M` (the PROPOSED direction is never flipped).
- **PC final action** (CUP / site-plan / preliminary-plat / permitted-use — never reach
  Council): `N-M Approved (Final Action)` / `N-M Denied (Final Action)` (a *passed* deny
  motion → `Denied`, ayes>nays, by design).
- **Procedural** (minutes / consent / adjourn / table / continue / chair election):
  `N-M Pass` / `Pass (unanimous)` / `N-M Fail`.
Direction uses XOR of (motion proposes approval) and (motion passed). **Case numbers**
(`12Z20` Z=rezone/text, `2G20` G=general-plan, `1S21` S=subdivision, `3P23` P=permitted-
use, `8C22`/`CUP-…` C=conditional-use) captured into `motion.case_no` (164/324 motions).

## CARDINAL RULE — never fabricate
- Unanimous / tally-only → `names_recorded:false`, EMPTY lists (the majority is never
  named in these minutes).
- **5 "No recorded vote" motions** = moved but not voted (superseded competing motion, or
  tabled for lack of quorum: 2021-07-27 m3, 2023-05-09 m3, 2024-07-09 m5, 2024-09-10 m2,
  2025-06-10 m2) — never asserted as a pass.
- OCR names fuzzy/variant-matched to the roster (`Mufioz→Munoz`, `Berggraaf→Burggraaf`);
  overall fuzzy/variant rate **21/2020 = 1.04%** (this corpus OCR is clean). A roll-call
  name too garbled to resolve is dropped (blank), never guessed.

## Known discrepancies (advisory; source-faithful, NOT corrected — see validation report)
- **4 named-vs-printed tally mismatches** (named < printed): 2021-11-09 m3 (5-1 vs 6-1,
  a source clerk omission — the roll call lists 6 of 7) + OCR name drops 2022-04-26 m2,
  2024-10-22 m1 (header-less, only 3 of 7 survived OCR), 2026-01-27 m1.
- **3 reduced-quorum roll calls** (3–4 seated): 2022-05-24 (vote paused mid-count by the
  Chair), 2023-05-09 m7 (`Motion passes with 4 in favor` — Russell signed off, Young
  excused), 2024-10-22 (OCR-partial). All faithful to source.
- Chair/vice-chair **elections** that carry no `MOTION:` header (mostly 2020-2023 "All
  Commissioners voted in favor") are not captured — a minor procedural gap.

## Roster (`roster.csv`: commissioner, first_seen, last_seen, n_meetings)
PC is **appointed** (no election). 7 voting members + 1–2 non-voting alternates; Chair &
Vice-Chair vote like members; **no mayor on the PC**. Built from attendance headers +
vote participation. Drift 2020→2026: Barbieri/Burggraaf (left 2020/2021) → Young (2021),
Wilkey (2022), Munoz (2025), Murphy (alternate, 2026). `B. Murphy` (alternate) moves
motions but never appears in a named roll call (correctly excluded from tallies).

## Outputs & re-run
`votes/<year>/<week>/<date>_planning-commission.json` (one per meeting; `present` +
`votes[]` with mover/seconder/aye/nay/abstain/absent/recuse/result/kind/vote_format/
outcome_detected/tally_text/case_no) → `all_votes.csv` (13-col) + `roster.csv`.
```
python3 extract_votes.py     # resumable; --force to rebuild all
python3 validate_votes.py    # writes votes/_validation_report.txt
```
## Normalized layer (`motions_std.csv` — BUILT, 324 rows)
`motions_std.csv` exists (324 rows, one per motion; `motion_type_std`, `land_use_type`,
`action_class`, `outcome`, tallies, `vote_mode`), generated by
`python3 ../scripts/normalize_motions.py --all` — the cross-city normalization layer joins on
`(source, motion_no)`. `result`/`motion_type` in `all_votes.csv` remain city-verbatim; the
standardized categories live alongside in `motions_std.csv`, never overwriting them.
(Registration into the repo-root `crosswalks/` + `cities.db` is the orchestrator's
cross-city step, confirmed when `scripts/build_cities_db.py` next runs — out of scope here.)
