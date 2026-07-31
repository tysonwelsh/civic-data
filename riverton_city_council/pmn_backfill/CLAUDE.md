# pmn_backfill/ — Riverton City (source type 4: PMN / Granicus minutes backfill)

**Purpose.** A separate, reviewable set of Council + Planning Commission minutes that the
audited `meeting_minutes/` and `planning_commission/` layers were missing, recovered by
diffing the repo against **two** sources. As-of 2026-07-13. **PROMOTED 2026-07-16**: votes
from all 7 meetings are now merged into the audited `all_votes.csv` files (and the db/weeks
layers) with `provenance=pmn_minutes`, via each dataset's `extract_backfill_votes.py` —
Council 34 motions / 162 rows, PC 10 motions / 10 rows (all unanimous-consent tally-only).
The raw/text files here remain the canonical source for those rows (`source =
pmn_backfill/text/…`); nothing here was moved into `minutes/` or `minutes_index.csv`.

## What's here

- `raw/` — the 7 recovered source files verbatim (+ `_fetch_log.jsonl` from `polite_fetch.py`:
  url, http status, bytes, sha256, retrieved_utc).
- `text/` — one extracted-text sidecar per file (`<stem>.txt`).
- `index.csv` — SCHEMA_SPEC §9 `pmn_backfill/` contract header (14 cols):
  `date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`.
  `path` is dataset-relative including `raw/`. `body` uses the repo vote-layer values
  (`Council` / `PlanningCommission`).
- `coverage.md` — per year × body × source diff table (repo / PMN / Granicus / recovered /
  still-missing). Result: complete superset (0 still-missing).
- `AVAILABILITY.md` — PMN entity 251 + all 12 body ids, Granicus holdings, and the
  inventory of non-core bodies (RDA/LESA/FSA/HPC/BOE/Canvassers) that were **not** recovered.

## The two diffs (both were run)

1. **PMN full-history sweep** — for each body, one GET of `notices.html?id=<body>&page=200`
   returns the entire cumulative notice history. Attachment **filenames** were scanned, not
   only the `(Meeting Minutes)` type label, so minutes attached under `(Other)`/blank labels
   were still caught. Diffed by meeting date (±4d) vs the repo `minutes_index.csv`. Found 3
   Council (2020-01-07/-21, 2020-02-04) + 1 PC (2026-06-25) within the 2020 floor.
2. **Granicus-vs-repo independent diff** — Riverton's audited repo was itself harvested from
   PMN, so PMN is a completeness check, not an independent one. Granicus
   (`rivertoncity.granicus.com`, `view_id=1`) is the independent archive. Enumerated the full
   `ViewPublisher.php` server-rendered table (599 minutes links). Diffed council/PC dates vs
   the repo. Found 3 meetings **PMN never carried minutes for** (only notice pages exist):
   Council 2023-09-05, Council 2023-11-07, PC 2023-11-09.

## Provenance per row (`source` column)

- `source=pmn` (4 rows): fetched from `https://www.utah.gov/pmn/files/<id>.<ext>`;
  `pmn_file_id` + `notice_url` populated. The 3 early-2020 council files are Word
  (`.docx`/`.doc`) — PMN's native format for that era.
- `source=granicus` (3 rows): fetched from `DocumentViewer.php?file=rivertoncity_<hash>.pdf`;
  `source_url` = that DocumentViewer URL, `notice_url` = the Granicus `MinutesViewer.php` page.
  `pmn_body_id` is still set (the body exists on PMN) but `pmn_file_id` is blank — PMN posted
  no minutes attachment on those dates, which is exactly why the independent diff was needed.

## Granicus fetch vendor notes (important for re-runs)

- `MinutesViewer.php?view_id=1&clip_id=<c>&doc_id=<uuid>` does **not** serve raw PDF bytes for
  Riverton. It returns an HTML/Google-gview wrapper that embeds the real PDF at
  `DocumentViewer.php?file=rivertoncity_<hash>.pdf&view=1` — extract the `<hash>` from the
  wrapper (regex `DocumentViewer\.php\?file=rivertoncity_[a-f0-9]+\.pdf`) and fetch that.
- The **2015–early-2020** era behaves differently again: MinutesViewer serves the raw Word
  `.doc/.docx` (OLE / Word-2007+ bytes under a `.pdf` URL) or a server-generated HTML minutes
  page — no DocumentViewer PDF. For those the PMN copy (Word doc) is the cleaner source, which
  is why the 3 early-2020 council files here are sourced from PMN, not Granicus.
- Use a browser UA + `--referer https://rivertoncity.granicus.com/ViewPublisher.php?view_id=1`
  and follow redirects (`polite_fetch.py` does).
- Granicus `ViewPublisherRSS.php?mode=minutes` caps at the most recent 100 items — use the
  full `ViewPublisher.php` HTML table for whole-history enumeration.

## Extraction

- Born-digital PDFs → `pdftotext -layout` (Council 2023-09-05/-11-07, PC 2023-11-09,
  PC 2026-06-25). All clean, selectable text; **no OCR**.
- Word docs → `textutil -convert txt` (Council 2020-01-07/-21 `.docx`, 2020-02-04 `.doc`).
- `extraction_method` records the tool per row. `screen_corpus.py` on `text/`: no mojibake,
  stubs, split-words, or dict-ratio outliers (2 advisory flags — repeated page-footer lines and
  natural "Approved: Pending"/footer endings — both benign; files verified complete).

## Rebuild

The recovered raws are fixed. To regenerate `index.csv` deterministically, re-run the builder
kept with the session scratch (`build_index.py`) — it re-asserts every `path` exists. The
diffs are reproducible from `parse_notices.py` (PMN inventory) + the ViewPublisher table.

## Caveats / non-goals

- **Votes PROMOTED 2026-07-16** (the follow-up this section used to defer): all 7 meetings
  are now in `all_votes.csv`, `motions_std.csv`, `db/`, and `weeks/` with
  `provenance=pmn_minutes` — run each dataset's `extract_backfill_votes.py` after any
  `extract_votes.py` re-run to re-merge. Three bounded parse tolerances for the early-2020
  clerk era (missing name-vote hyphens verified absent in the raw .docx; one
  "Roll Call vote." roll-call introducer; one un-anchored "made a SUBSTITUTE motion") are
  documented in `../meeting_minutes/extract_backfill_votes.py` — the raw/text files here
  stay verbatim.
- Bodies other than Council and PC (RDA, RLESA, RFSA, HPC, BOE, Canvassers) are **inventoried
  in AVAILABILITY.md but not recovered** — out of core-repo scope.


## 2026-07-17 — crosscheck flag verification (18 flags → 6 leads, 12 exceptions)

Verified every 2026-07-17 crosscheck flag by fetching each notice page (throttled) +
repo index checks. PMN event dates map 1:1 to repo meeting dates here. Re-run after
appending exceptions: **6 flags** (12 suppressed).

**Recovery leads (6, agenda-grade — real meetings held, agenda on PMN, NO minutes on
PMN, absent from repo).** RESOLVED 2026-07-17 (wave2): each was re-probed against the
independent Granicus `ViewPublisher.php?view_id=1` archive — **all 6 are DEAD ends**
(no minutes on Granicus either) and are now logged in the core datasets'
`minutes_unrecovered.csv`:
- **PC 2022-05-26** — Granicus AgendaViewer clip523, **no MinutesViewer link**; repo has NO May-2022 PC minutes (05-12 cancelled, 05-26 held). → `planning_commission/minutes_unrecovered.csv`.
- **Council 2023-05-02** — hybrid work meeting; **absent from the Granicus archive entirely** (May-2023 Council rows are 05-11/05-16/05-25); repo has 05-16 only. → `meeting_minutes/minutes_unrecovered.csv`.
- **PC 2023-07-27** — Granicus AgendaViewer clip601, **no MinutesViewer link**; repo has 07-13 only. → `planning_commission/minutes_unrecovered.csv`.
- **PC 2023-08-24** — Granicus AgendaViewer clip608, **no MinutesViewer link** (one agenda item postponed, meeting held); repo has 08-10 only. → `planning_commission/minutes_unrecovered.csv`.
- **Council 2026-01-06** — Oath-of-Office / inauguration meeting; **absent from the Granicus archive entirely** (Jan-2026 Council rows begin 01-20); repo has 01-20 only. → `meeting_minutes/minutes_unrecovered.csv`.
- **PC 2026-01-08** — 'Green Bin' PLZ-25-2055 etc.; **absent from the Granicus archive entirely**; repo has NO Jan-2026 PC minutes (01-08 held, 01-22 cancelled). → `planning_commission/minutes_unrecovered.csv`.

These 6 corrected the dataset's earlier 'complete superset (0 still-missing)' claim
(the bluffdale-pilot lesson) — see `coverage.md` CORRECTION note. Contrast: the 2023-09-05/
-11-07/-11-09 dates DID have Granicus MinutesViewer docs and were recovered into this
backfill, proving the Granicus re-probe method works and these 6 are true no-minutes gaps.
No vote layer changed (no minutes to extract). A drafted GRAMA request is in the wave report.

**Exceptions written (12), all `other` — meetings CANCELLED per the notice body** (title
stayed 'Meeting'; RE_CANCEL only reads the list title, so body-level cancellations slip
through): PC 2022-05-12, 2023-06-08, 2024-01-25, 2024-03-14, 2024-09-26, 2025-01-23,
2025-09-11, 2026-01-22, 2026-03-26; Council 2022-09-06, 2024-09-17, 2025-09-02.

**Hardening candidate:** body-level cancellations dominate the agenda_only_gap noise here
(9 of 12) — the engine cannot see them from the list HTML. See engine notes.
