# meeting_minutes/ — Midvale City Council vote pipeline

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **151** City Council minutes,
  2020 → 2026. Council meets **1st & 3rd Tuesdays** (6:00 p.m.); the folder is keyed on that
  week's **Monday** (build_weeks MEETING_WEEKDAY = Tuesday = 1). Special / budget / truth-in-
  taxation / legislative-breakfast meetings are separate files (a date can carry >1 doc).
  Each file opens with a provenance header (Source URL, vendor=revize, raw file, `Format`,
  Retrieved date). Indexed in `minutes_index.csv` (8-col standard;
  `format=text` born-digital / `format=ocr` scanned-and-OCR'd). PMN-promoted docs
  (2026-07-16) are NOT in this index — they live in `../pmn_backfill/` and enter the vote
  layer via `extract_backfill_votes.py` (see below).
- `minutes_unrecovered.csv` — the one council-family gap: the **2023-01-17 RDA session's own
  minutes** (verified held; PMN's "1-17-2023" file actually carries the 2022-12-06 minutes).
- `raw/<date>_<slug>.pdf|.docx` — retained source originals (Revize Document Center), never
  modified. 142 PDF + 9 docx (2020 Word originals).
- `extract_votes.py` — the PURE deterministic parser (no LLM, no network; resumable). One
  self-contained file, body inferred from the parent dir (an identical copy runs the PC).
- `votes/<year>/<week>/<slug>.json` — one structured JSON per meeting (resumable intermediate).
- `validate_votes.py` → `votes/_validation_report.txt` — roster/mayor/oversize/contested checks.
- `roster.csv` — the **observed** roster (every name that cast a recorded vote, with tenure
  and per-outcome counts). Midvale's roster CHANGES across the window — this is the evidence.
- `all_votes.csv` — long format, **one row per member-vote** (or one placeholder per
  tally-only motion): `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`
  **+ a documented trailing 14th `provenance` column since 2026-07-16** (`minutes` = audited
  Revize doc; `pmn_minutes` = PMN-recovered doc merged by `extract_backfill_votes.py`).
- **+24 PMN-promoted council-session docs** (14 dates, 2026-07-16): 12 Council + 11
  standalone RDA + 1 standalone MBA minutes living in `../pmn_backfill/` (text sidecars in
  `pmn_backfill/text/`, which is what their vote rows' `source` points at), merged by
  **`extract_backfill_votes.py`** — 179 motions / 549 rows. Standalone RDA/MBA docs print
  **"Board Member <Name>" / "Chair <Name>"** roles (an agency-roles regex variant); the
  Mayor presides as Chair and does not vote. The 25th recovered doc (2023-03-30 budget
  retreat) has no motions — honest zero. One PMN label lie corrected: the doc filed as
  "RDA Minutes 1-17-2023" contains the **2022-12-06** RDA minutes (merged under the true
  date); the 2023-01-17 RDA session's own minutes are in `minutes_unrecovered.csv`.

## Run
```
python3 extract_votes.py            # writes votes/*.json then rebuilds all_votes.csv + roster.csv (13-col)
python3 extract_backfill_votes.py   # REQUIRED: merges the PMN-promoted docs + adds the provenance
                                    # column + refreshes roster.csv — skipping it drops all
                                    # pmn_minutes rows
python3 validate_votes.py           # writes votes/_validation_report.txt (audited JSONs only)
```
`all_votes.csv` is RFC-4180 (motion text has commas) — parse with a real CSV reader.

## Vote grammar — NAMED roll call (high quality)
Midvale prints a per-member roll call, unlike the narrative-tally councils:
```
MOTION: Council Member <Name> MOVED to <desc>. The motion was SECONDED by Council Member <Name>.
Mayor <Name> ... called for a roll call vote. The voting was as follows:
      Council Member <Name>            Aye
      Council Member <Name>            Nay
      Council Member <Name>            Absent
The motion passed unanimously.        (or "... failed", or a tally)
```
Voice-vote fallback (`... called for a vote. The motion passed unanimously.`) records no names
(`names_recorded:false`, one placeholder row). `result` is derived `"<aye>-<nay> Pass/Fail"`
for named roll calls, `"Unanimous Pass"` for voice votes; `motion_type` uses the fixed
12-category taxonomy. Normalized cross-city fields belong **alongside** in `motions_std.csv`
(not built here).

## Names captured AS PRINTED — no hard-coded roster
The roster changes across 2020-2026 and the extractor **never assumes a fixed set**: it records
whoever the minutes name. **Dustin Gettel is a Council Member 2020-21, then Mayor 2022+**;
**Quinn Sperry** serves early; **Bonnie Billings / Denece Mikolash** arrive later. A canonical
map (built in pass 1 from the whole corpus) only repairs whitespace jams (`BryantBrown` →
`Bryant Brown`) and OCR typos within edit-distance 2 (`Paut Glover` → `Paul Glover`,
`Gette` → `Dustin Gettel`). `validate_votes.py` prints the per-year observed roster and a
rare-name list to spot-check OCR garble.

## The Mayor does NOT vote on ordinary motions (six-member form)
Max ordinary tally = **5** district members; the presiding Mayor is absent from the roll block.
A literal `Mayor <Name>  <vote>` line inside a roll block is a genuine **tie-break** → the vote
is captured faithfully and flagged `mayor_voted:true` (surfaced by the validator). "Mayor
Pro-Tem <Name>" is a councilmember chairing (they appear as `Council Member <Name>` in the
roll) and is never a mayor vote.

## Coverage / formats
Floor **2020** (Midvale incorporated 1909 — 2020 is a normal analysis floor, not an
incorporation edge). **2020–2021 council minutes are SCANNED image PDFs → OCR** (`format=ocr`,
`pdftoppm -r 300` + tesseract); 2020 has 9 born-digital `.docx` originals; 2022+ is
born-digital text. Run `python3 scripts_screen_corpus.py` (repo root) — the stub<200B +
per-year length gate — before trusting the corpus.
