# utah_county / land_use — how to use this module

County land-use minutes + extracted PC votes for growth/housing/development research. The
**LAND_USE** module of the `utah_county/` entity — the single **Utah County Planning
Commission** (unincorporated-area land use; recommends to the 3-member Board of
Commissioners). Read `SOURCES.md` first for provenance and the recording ceiling.

## What's here

- `minutes/<year>/<date>_planning_commission.md` — vision transcriptions of the signed
  minutes (born-scanned PDFs; `extraction: claude-vision`). Filter on the `body` /`date`
  front-matter.
- `raw/<date>_<pmnfileid>_minutes.pdf` — retained source PDFs (PMN body 1711).
- `minutes_index.csv` — one row per PC meeting date, 2015–2026 (145 rows):
  `date, body, md_path, source_url, minutes_status, agenda_url, cms_minutes_file, note`.
  `md_path` is relative to `utah_county/` (federation loader reads it).
- `all_votes.csv` — one row per (motion, named member): `date, year, title, body, motion_no,
  motion, motion_type, result, mover, seconder, member, vote, source`. `title` = the agenda
  item; `result` = the verbatim outcome sentence; `body`=`PlanningCommission`; tally-only
  motions emit a single blank-`member` row.
- `motions_tally.csv` — one row per motion: `date, body, motion_no, motion, result, mover,
  seconder, names_recorded`.
- `enumerate_pmn.py`, `pmn_notices.csv` — reproducible source enumeration.

## Coverage (retrieved 2026-07-20)

| Layer | Count | Range |
|---|---|---|
| Meetings with extracted minutes+votes | **11** | 2025-01-21 … 2026-05-19 |
| Motions extracted | 73 (71 named / 2 acclamation-tally) | — |
| Named vote rows | 382 (369 Aye, 4 Nay, 9 Recuse) | — |
| Contested motions | 3 | see below |
| PC meetings catalogued (all statuses) | 145 | 2015-01 … 2026-12 |

**Vote ceiling: HIGH ATTRIBUTION** — every Aye and every Nay is named on each substantive
motion (not tally-only). Recusals captured from narrative. See SOURCES.md.

Contested (named-dissent) motions:
- **2025-02-18** — J L.C. RA-5 minimum-lot text amendment, *recommend denial* passed 5–1
  (Nay: Chris Herrod).
- **2025-08-19** — PacifiCorp/Rocky Mountain Power CU2025-05 (345 kV line), motion to
  *withhold decision* pending proof of notice (Utah Code 54-18-304) passed 5–1 (Nay: Chair
  Shayne Pierce).
- **2026-04-21** — Jamie Evans impound-yards text amendment, *recommend approval* (staff
  version) passed 4–2 (Nay: Stanford Sainsbury, Sullivan Love).

## Honest gaps (never fabricate)

- **2015–2019**: PMN agenda-only; minutes never published to a reachable channel.
- **2020–2024 (+ a few 2025)**: minutes catalogued in the county CMS but the media host
  `cms.utahcounty.gov` is offline (NXDOMAIN) — `minutes_status=catalogued_media_offline`,
  `cms_minutes_file` names the PDF. **Backfillable** when the county's media host comes up
  (queued for TODO). This is the largest recoverable gap.
- Cancelled (10) and scheduled/pending-approval meetings carry no minutes by definition.
- **No Mountainous Planning District PC exists for Utah County** (that body is Salt Lake
  County's — see SOURCES.md "MPDPC verdict").

## Cardinal rules

- Never fabricate minutes text, names, or dates. Blank `member`/`vote` = the source printed no
  roll (the acclamation elections). `catalogued_media_offline` = the minutes exist but the
  county's host is down — report it, don't infer content.
- `raw/` PDFs + the vision markdown are canonical; regenerate derived layers, don't hand-edit.
- `result` is verbatim; normalized/disposition layers are computed downstream in the db.

## For the closing (db) pass

Ingest votes into `utah_county/db/utah_county.db` from:
- `utah_county/land_use/all_votes.csv` (named + tally rows)
- `utah_county/land_use/motions_tally.csv` (motion spine)
- `utah_county/land_use/minutes_index.csv` (document catalogue → `document`/FTS)
- development pipeline: `utah_county/development/applications.csv`
