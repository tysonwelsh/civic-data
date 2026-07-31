# pmn_backfill/ — Midvale PMN cross-check & gap recovery

Utah Public Notice (PMN, `utah.gov/pmn`) backfill for Midvale City, built by the
`/expand-city-sources` skill (source type 4).

✅ **PROMOTED (2026-07-16).** 24 of the 25 recovered docs are merged into
`meeting_minutes/all_votes.csv` with **`provenance=pmn_minutes`** (a documented trailing
14th column; audited rows = `minutes`) — 179 motions / 549 rows (Council 125 + RDA 49 +
MBA 5 motions). Merge driver: **`meeting_minutes/extract_backfill_votes.py`** (run it after
any `extract_votes.py` re-run, or the pmn rows drop out). Vote rows' `source` points at the
`text/` sidecars here. NOT merged: the 2023-03-30 budget retreat (zero motions — honest).
**Date correction applied at merge:** the doc PMN filed as "RDA Minutes 1-17-2023"
(`raw/2023-01-17__rda__…`) contains the 2023-01-17 RDA *agenda* plus the minutes **OF the
2022-12-06 RDA meeting** (every page header prints December 6, 2022) — merged under
date=2022-12-06; the 2023-01-17 RDA session's own minutes are logged in
`meeting_minutes/minutes_unrecovered.csv`. `index.csv` below keeps the PMN-filed date
verbatim (it records what PMN posted).

## Why PMN matters here (independent cross-check, not a superset)
Midvale's core minutes came from the city's **own Revize Document Center**, so PMN is an
*independent* second source (like murray/herriman/draper), not the PMN-sourced-superset case.
It surfaced **14 genuine council-session meeting dates** the repo was missing — most in a real
2024 coverage hole. Planning Commission has **zero** recoverable gaps in the 2020+ window.

## Contents
- `index.csv` — SCHEMA_SPEC §9 `pmn_backfill` contract header
  (`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,`
  `retrieved_date,format,extraction_method`) + one extra col `orig_filename`. 25 rows.
- `raw/<date>__<body>__<origname>.pdf` — retained source PDFs verbatim, + `_fetch_log.jsonl`.
- `text/<stem>.txt` — extraction sidecars (pdftotext for born-digital; OCR for the 4 scanned
  2020-2021 docs — `extraction_method` per row).
- `coverage.md` — per-year × body table (repo / PMN / recovered / still-missing / ocr-upgrade)
  + below-floor availability + out-of-scope finds.
- `AVAILABILITY.md` — what was checked, recovered, and honestly not.
- `_work/` — build artifacts (crawled notices HTML, `attachments_all.csv`, manifests). Not part
  of the dataset contract.
- Helper scripts (kept in-dataset, unique names): `pmn_parse_notices.py` (list HTML → attachments),
  `pmn_diff.py` (filename-date extraction + repo diff), `pmn_build_index.py`, `pmn_extract_text.py`.

## PMN ids (entity 201)
Bodies: **753 City Council**, **754 Planning Commission**, **756 Redevelopment Agency**,
**757 Municipal Building Authority**, 755 Board of Adjustments, 9155 Appeal Authority,
758 Midvale Community Council, 760 Union Community Council, 9179 White City Council. Only
753/754/756/757 hold minutes; the rest hold agendas/notices only. All bodies were swept.

## Method / rebuild
1. `list/entities.html?id=3` → entity 201 → `list/publicBodies.html?id=201` → body ids.
2. `list/notices.html?id=<body>&page=200` (cumulative full history) per body → `pmn_parse_notices.py`.
3. `pmn_diff.py` — parse the meeting date out of each minutes-like **filename** (Midvale uses
   many date formats: `CC Minutes M-D-YYYY`, `M-D-YY001`, `YYYYMMDD`, `MM.DD.YY`, `MM DD YYYY`),
   map CC+RDA+MBA to the Council session date and PC to its own, diff ±4d vs the repo indexes.
4. Fetch genuine 2020+ gap docs via `scripts/polite_fetch.py` → `raw/`.
5. `pmn_extract_text.py` → `text/` (auto OCR-fallback when text layer < 200 chars).
6. `pmn_build_index.py` → `index.csv`. Validate with the skill's `validate_dataset.py` (PASS).

## Caveats
- **Body modeling:** the repo treats RDA (and MBA) as **in-session** bodies embedded in the
  Council minutes doc. PMN files them as **separate** documents, so a recovered date can carry a
  CC doc + an RDA doc (+ MBA). Each is indexed with its `body`; on merge, the CC doc is the
  primary Council-session minutes (2024-08-06 is RDA-only — no CC doc was posted).
- **OCR seam:** PMN's 2020-2021 copies are the SAME scanned images as the repo (verified zero
  text layer) — **no born-digital upgrade available**. The 2 recovered seam dates are themselves
  `format=scanned`/`ocr`.
- **Below-floor (2015-2019)** PMN docs exist but are deliberately NOT recovered (2020 floor).
- **Harvest Days Committee** docs cross-filed under the Council body are NOT council meetings —
  excluded.
- **Merged 2026-07-16** (see the PROMOTED note at the top): sidecar-merge pattern (docs stay
  here; `extract_backfill_votes.py` parses `text/` with the audited parser + an agency-roles
  variant for the "Board Member"/"Chair" RDA/MBA grammar). One clerk anomaly retained
  verbatim: the 2024-05-07 MBA doc's page running header prints a stale "May 2, 2023"
  template date (the meeting is verified 2024-05-07 — title header, FY2025 budget content,
  "Approved this 3rd day of December 2024").


## 2026-07-17 — PMN cross-check flag verification (24 flags -> 9)
Verified every crosscheck_flags row; 15 exceptions added (on top of the 6 pre-seeded
Harvest Days rows -> 21 total suppressed).
- **Exceptions (15):** the Harvest Days Festival Committee family continues — 5
  missing_minutes (2022-07-14, 2023-04-27, 2023-05-11, 2023-05-25, 2024-04-10) ->
  not_minutes + 6 agenda (2022-06-02, 07-07, 07-28, 2024-01-10, 05-15, 09-10) -> other;
  'Legislative Breakfast' 2021-01-13 -> other; 'Bonds to be Issued' UIA-Telecom notice
  2025-09-08 (non-meeting Monday) -> other; TWO wrong-PMN-date cases -> wrong_date:
  2023-05-07 (agenda/packet filenames read 5-7-2024; true 2024-05-07 already in repo via
  pmn_backfill) and 2024-09-30 (attachment '...10-9-2024.pdf'; true 2024-10-09 in repo).
- **Recovery leads (9), remain flagged:** 2024-02-06 Council + its RDA companion
  (n890171/n890173 — genuine gap, repo council jumps 2024-01-16 -> 03-26) are the
  strongest; 2020-03-17 (COVID, likely cancelled — verify), 2021-03-23 (extra council
  date); PC agenda gaps 2020-05-27, 2021-05-12, 2021-07-28 (workshop), 2021-12-08,
  2023-01-11. All agenda-grade (no minutes on PMN; midvale core came from Revize).
- **Hardening:** the two wrong_date cases corroborate the filename-date-rescue candidate
  extended to agenda/packet attachment filenames (see report).
- Re-run (`--cached`): **9 flags** (all agenda_only), 21 suppressed.

## 2026-07-17 (wave2) — the 9 agenda-grade leads RESOLVED (9 -> 0)
Probed the city CMS (Revize Document Center, direct URL variants) + PMN notices for real
recorded minutes on each of the 9 leads; verified every disposition in-body / at source.
Outcome: **1 recovered, 3 genuine gaps logged, 5 false-positives suppressed.**
- **RECOVERED (1):** **2023-01-11 Planning Commission** — the minutes ARE on Revize
  (`.../Planning & Zoning Commission/2023/Minutes/11123 Approved PC Minutes.pdf`, 200; the
  original href-crawl missed it, PMN held only the agenda). Verified in-body (Chair Snow,
  Jan 11 2023, 3 motions). Promoted into the **standard PC pipeline** (native Revize file →
  `planning_commission/minutes/2023/2023-01-09/`, `source=revize`, `format=text`, PC
  `all_votes.csv` stays 13-col by design) — NOT pmn_backfill, which is for off-portal docs.
  +3 motions / 9 vote rows (m1 voice-vote placeholder; m2 4-0 Pass close hearing; m3 4-0
  Pass Land-Use recommendation).
- **GENUINE GAPS -> minutes_unrecovered.csv (3):** **2024-02-06 Council** (notice 890171,
  business meeting, agenda+packet, not cancelled; `CC Minutes 2-6-2024.pdf` -> 404; repo
  jumps 2024-01-16 -> 03-26) + its **2024-02-06 RDA** companion (notice 890173) ->
  `meeting_minutes/minutes_unrecovered.csv`; **2021-12-08 PC** (notice 720135, agenda, not
  cancelled; `20211208 PC Minutes` -> 404) -> `planning_commission/minutes_unrecovered.csv`.
  No minutes on PMN or Revize on any channel — GRAMA-request candidates.
- **FALSE POSITIVES -> pmn_exceptions.csv (kind=other, 5):** **2020-03-17 Council** POSTPONED
  to 2020-03-24 (notice 595265; the 03-24 session IS in the repo); **2021-03-23 Council**
  notice 666037 is an advance public-hearing notice for the meeting held **2021-04-06** (in
  repo; Council meets 1st/3rd Tue only — no distinct 03-23 meeting); **2020-05-27**,
  **2021-05-12**, **2021-07-28 (workshop)** PC all CANCELLED at source (notices 606579 /
  674265 / 691873 — "MEETING CANCELLED"; the crosscheck's cancel-detector reads titles/
  attachments, not the notice body, so they had slipped through as agenda_only).
- Re-run (`--cached`): **0 flags** (clean), **26 suppressed**, 6 pending-adoption.
