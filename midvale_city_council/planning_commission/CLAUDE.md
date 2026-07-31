# planning_commission/ — Midvale Planning & Zoning Commission vote pipeline

Same schemas and pipeline as `meeting_minutes/` (see that CLAUDE.md), for Midvale's own
**Planning & Zoning Commission**. `body=PlanningCommission` throughout.

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **104** P&Z Commission minutes,
  2020 → 2026. PC meets **2nd & 4th Wednesdays** (6:00 p.m.); folder keyed on that week's
  Monday. Provenance header on every file; indexed in `minutes_index.csv`
  (`format=text` / `format=ocr`).
- `raw/<date>_<slug>.pdf` — retained Revize originals (all PDF).
- `extract_votes.py` / `validate_votes.py` — identical self-contained scripts to the council
  dataset; the body is inferred from this directory name (→ Planning Commission).
- `votes/<year>/<week>/<slug>.json`, `all_votes.csv`, `roster.csv`,
  `votes/_validation_report.txt`.

## Run
```
python3 extract_votes.py
python3 validate_votes.py
```

## Vote grammar — named roll call, SURNAMES only
```
MOTION: Commissioner <Surname> MOVED to <desc>. SECONDED by Vice Chair <Surname>.
Chair <Surname> called for a roll call vote. The vote was as follows:
      Chair <Surname>            Yes
      Vice Chair <Surname>       Yes
      Commissioner <Surname>     No
```
The Commission records members by **surname** (roles: Chair / Vice Chair / Commissioner) and
uses **Yes/No** (mapped to aye/nay). Many routine items are **voice votes** (`... called for a
voice vote. The motion passed unanimously with all voting in favor.`) → no names recorded.
Chair/Vice-Chair elections are decided by paper-slip ballots reported narratively
(`Voting Results: 4 votes – <Name>`); the associated confirmation MOTION is captured, the
slip tally is left as minutes prose. Advisory land-use recommendations to Council carry the
case in the motion text (`motion_type=Land-Use/Zoning`).

## Roster
No hard-coded roster (names captured as printed; canonical map repairs whitespace/OCR typos).
Commission size runs ~5-7 seats — `validate_votes.py` flags roll calls exceeding 7 decisive
voters. There is no mayor.

## Coverage / formats
Floor **2020**. **2020–2021 minutes are SCANNED image PDFs → OCR** (`format=ocr`); 2022+ is
born-digital text (a couple of later scans exist and are OCR'd too). The three PC docs whose
Revize links were bare-relative (`<base href>` quirk, 2024-2026) were resolved to the CDN root
during acquisition. Run `python3 scripts_screen_corpus.py` (repo root) before trusting the
corpus.
