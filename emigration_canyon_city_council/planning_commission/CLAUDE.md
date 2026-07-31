# planning_commission/ — Emigration Canyon Planning Commission votes

The canyon's **own** Planning Commission ("Township Planning Commission" pre-2024, "Planning
Commission" after). Source: **Utah PMN body 1562**. Monthly, ~2nd week, Thursday mornings.
Born-digital **MEETING MINUTE SUMMARY** PDFs (no OCR needed — one exception: the late-posted
**2025-11-13** doc is an image-only scan, tesseract-OCR'd, promoted from `../pmn_backfill/`
2026-07-16). See repo-root `CLAUDE.md`.

## Files
- `minutes/<year>/<date>/<date>_<slug>.md` — **60** docs (2018-11 → 2026-06; 59 `pdf-text`
  + 1 `ocr`).
- `raw/<year>/…pdf` — retained PMN originals (60).
- `minutes_index.csv` — standard + `meeting_type,pmn_notice_id,pmn_file_id`; `source=pmn`.
- `minutes_unrecovered.csv` — **73** meetings with a PMN notice but no recovered minutes
  (heavily 2017–2021 early-TPC era + notice/meeting-date drift; all month-name-filename
  minutes that DO exist were matched to their in-body date, so 0 recoverable docs were
  dropped). The 2025-11-13 row was satisfied and dropped 2026-07-16 (minutes posted late;
  recovered by the pmn_backfill sweep, promoted here).
- `extract_votes.py` (PURE) → `votes/*.json` → `all_votes.csv` + `roster.csv`.
  `all_votes.csv` carries the collection-standard trailing **`provenance`** 14th column:
  `minutes` (audited primary harvest) | `pmn_minutes` (the promoted 2025-11-13 doc, 2 motions).
- `validate_votes.py` → `votes/_validation_report.txt`.

## STRUCTURED grammar (unlike the Council's narrative tally)
```
Motion: To recommend file #OAM2026-001638 …
Motion by: Commissioner Geroux
Second by: Commissioner …            (optional)
Vote: Commissioners voted unanimously in favor
```
Named dissent: `Vote: Commissioner Wallace voted nay, all other commissioners voted in
favor. Motion passed.` Inline procedural: `Commissioner X motioned to open the public
hearing, Commissioner Y seconded that motion.` The PC **recommends** land-use files to the
Council — those motions are `motion_type = Land-Use/Recommendation`.

## Extraction (`votes/_validation_report.txt`)
60 meetings · **141 motions** (138 tally-only · 3 named-dissent) · **3 contested**
(2019-11-14, 2022-11-17 Harpst abstain on minutes; 2026-06-11 Wallace nay on an ordinance
recommendation) · body all `PlanningCommission` · CSV==JSON **OK**. "Commissioners voted
unanimously in favor" → one tally-only row (blank member); named dissent → the named row.

## Roster (OBSERVED)
`roster.csv`: Karkut, Wallace, Berreth, Harpst, Geroux, Pinon, Tippets (+ earlier TPC
members via attendance). Born-digital text is trusted — an unmapped "Commissioner <Surname>"
is kept **verbatim** (it is literally in the record), never dropped or guessed. Staff (Gurr,
Tucker, Gillmor, McLean) are not commissioners and never appear as "Commissioner <Name>".

## Seconder label — three forms, all parsed (regex extended 2026-07-17)
The clerk writes the seconder line three ways: `Second by:`, `Seconded by:`, and — in **125
blocks across 51 docs, the DOMINANT PC form** — **`2nd by:`**. The original `MOTION_BLOCK`
regex matched only `Second(ed)? by:`, so ~115 named seconders were blank though the source
named them. The seconder alternation is now `(?:Second(?:ed)?|2\s?nd)\s+by:` (constant
`SECOND_LABEL`). Re-extraction (2026-07-17) **filled 115 blank seconders** (all real
commissioners: Berreth 44, Karkut 30, Wallace 18, Harpst 17, Geroux 14, Clark 1) with
**nothing else changed** (141 rows byte-stable at the (date,motion_no,member,vote) level;
mover/result/vote/motion_type all identical; 3 contested unchanged). **17 seconders stay
honestly blank** — 14 are `2nd by: Commissioner`/`2nd by:` lines with NO surname in the
source, and the 2025-11-13 OCR scan's `2nd by:` OCR'd as `2™4 by:`/`2"4 by:` (not parsed —
the documented OCR-quality caveat; never guessed). The fix is conservative: it does not
attempt the OCR-garbled form.

## Run
`python3 extract_votes.py [--force]` then `python3 validate_votes.py`.
