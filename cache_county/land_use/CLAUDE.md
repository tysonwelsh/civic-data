# cache_county / land_use — how to use this module

The **Cache County Planning Commission** minutes as a searchable text corpus + an
extracted vote layer, for growth / housing / development research. This is the
**LAND_USE** module of the `cache_county/` entity (the county's land-use / zoning /
subdivision decisions on **unincorporated** Cache County). One deliberative body — the
County PC — meets the **first Thursday** monthly.

## What's here

- `minutes/<year>/<date>_planning_commission.md` — one markdown per meeting: YAML
  front-matter (`date`, `body`, `source_url`, `raw_file`, `provenance`,
  `minutes_status`) + the pypdf/docx-extracted text. **The searchable corpus.**
- `raw/<date>_planning_commission.pdf|.docx` — the born-digital source (2 early
  meetings are `.docx`; the rest PDF).
- `minutes_index.csv` — one row per meeting: `date, body, md_path, source_url,
  minutes_status, note`. `md_path` is relative to the repo root (federation reads it).
  `minutes_status`: `Approved` (123), `NoMinutesPosted` (14 genuine source gaps),
  `PendingApproval` (4 recent 2026 meetings, minutes not yet posted).
- `all_votes.csv` — 13-col named-member vote rows (**named era only**, 2024-11 on).
- `motions_tally.csv` — one row per **tally-only** motion (the 2015→2024-10 era + a few
  procedural named-era motions), `names_recorded=false`.
- `roster.csv` — honest record of WHO the commissioners are, from named roles.
- `build_votes.py` — DERIVED regenerator (reads the markdown, writes the 3 CSVs). No
  network. `python3 build_votes.py`.
- `SOURCES.md` / `VOTES_README.md` — provenance + the recording-ceiling method.

## The recording ceiling — TWO grammar eras (READ THIS before analyzing votes)

Cache County PC minutes state motions inline in prose. There is a hard **vote-grammar
seam at 2024-11-07**:

- **TALLY era (2015-01-08 … 2024-10-03):** `"<Mover> motioned to <text>; <Seconder>
  seconded; Passed <aye>, <nay>."` — only the **numeric tally** is recorded. **No voter
  is named — not even dissenters on split votes** (a 3–1 vote names nobody). These
  motions are in `motions_tally.csv` with `names_recorded=false`. This is a source
  ceiling, NOT an extraction gap — never infer who dissented.
- **NAMED era (2024-11-07 onward):** the same motion line is followed by
  `"Ayes: <full names>"` / `"Nays: <full names or 0>"` — **every voter is named, even on
  unanimous motions**. These are in `all_votes.csv` (one row per member). A handful of
  procedural named-era motions (open/close hearing, extend meeting) print only a tally
  and stay in `motions_tally.csv` — honest ceiling variation.

So `all_votes.csv` covers **only 2024-11 → present**; the ~10 prior years are
tally-only by source. Contested signal: 44 split votes in the tally era (counts only)
+ 17 named-contested motions in the named era.

## Coverage (retrieved 2026-07-20, county website)

- **123 meetings with minutes**, 2015-01-08 … 2026-03-05 (~11/year, first-Thursday).
- **1,025 motions** extracted (848 with a numeric tally, 4 died-for-lack-of-second,
  173 named-vote). **930 named-member vote rows** (Aye 903 / Nay 25 / Abstain 2).
- Honest gaps: **14 held meetings with no minutes on the county site** (agendas exist —
  see `minutes_index.csv` `NoMinutesPosted`; PMN body 1479 is the recovery channel, not
  yet pulled) + **4 recent 2026 meetings** pending minutes approval. 2026-05-07 was
  **cancelled** (omitted).

## No structured development-application pipeline (honest scope note)

Unlike Salt Lake County, Cache County publishes **no structured development-application
log** — the county is a thin agricultural-valley land-use pipeline, and applications
surface only as PC agenda items (rezones, CUPs, subdivisions, ordinance amendments).
There is deliberately **no `development/` module**; the motions in `motions_tally.csv` /
`all_votes.csv` ARE the development-decision record (each motion names its project).

## Cardinal rules (repo-wide)

- **Never fabricate.** Tally-only blanks (no named voter) and `NoMinutesPosted` rows are
  honest data — report them, never fill them. OCR name variants (e.g. "Nate Dauges" for
  "Nate Daugs", "Christesen" for "Christensen") are kept **verbatim** — do not silently
  correct canonical values.
- `raw/` + the markdown are canonical; the CSVs are DERIVED — regenerate with
  `build_votes.py`, never hand-edit.
- `result` and mover/seconder are city-faithful/verbatim; any normalization lives
  downstream (the repo `motions_std` / crosswalk layer), never in these files.
