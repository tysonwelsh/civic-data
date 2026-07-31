# pmn_backfill/ — Kearns (Source 4: Utah Public Notice)

Additive, review-only backfill of minutes recovered from **Utah Public Notice (PMN)**
that are absent from the audited `meeting_minutes/` / `planning_commission/` layers.
**Never merged in place** — promotion into the audited layer (and vote extraction) is a
separate, deliberate task. Built 2026-07-13 per `/expand-city-sources` Source 4.

✅ **PROMOTED 2026-07-16 — all 3 recovered docs are now in the audited layer** (this
dataset stays as the provenance record; raws retained here AND copied into the audited
`raw/` dirs, sha256-verified identical): the 2 CRA minutes as
`../meeting_minutes/minutes/2025/<date>/<date>_cra-meeting.md` (**`body=CRA`**, 9
motions) and the PC 2019-04-08 doc as
`../planning_commission/minutes/2019/2019-04-08/…` (2 motions; the FALSE
`minutes_unrecovered.csv` row removed). All promoted rows carry
**`provenance=pmn_minutes`** in the trailing 14th `all_votes.csv` column (audited rows
= `minutes`). Backups: `_backups/2026-07-16-minutes-promotion/kearns/`.

## What's here (3 recovered minutes documents)

| date | body | pmn_body_id | file | format | note |
|---|---|---|---|---|---|
| 2025-07-14 | CRA | 9273 | 1320109 | scanned→OCR | CRA approved minutes |
| 2025-09-08 | CRA | 9273 | 1430807 | text | CRA draft minutes |
| 2019-04-08 | PlanningCommission | 1561 | 502755 | text | genuine recovery — was mis-logged unrecovered |

The **CRA (Community Reinvestment Agency, body 9273)** was previously **0 rows** in the
repo ("a real honest gap") — this dataset lights it up. The CRA convenes in-recess
before the City Council (city era only); tally-style votes like the Council.

## Files

- `raw/` — the 3 source PDFs verbatim + `_fetch_log.jsonl` (url, bytes, sha256,
  retrieved_utc) from `polite_fetch.py`. Never delete/normalize.
- `text/` — extraction sidecars (labeled by method).
- `index.csv` — §9 `pmn_backfill` contract header
  (`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,
  pmn_file_id,retrieved_date,format,extraction_method`) + extras
  `recovery_source,orig_filename,text_path`. `path` is dataset-relative incl. `raw/`.
- `coverage.md` — the full per-body accounting + the purge-gap verification.
- `AVAILABILITY.md` — what was checked / exists / stays a gap, as-of date.
- Helper scripts (this dir, unique-named — never in the shared scratchpad):
  `kearns_pmn_parse.py` (notices-list parser), `kearns_pmn_notice.py` (notice-page
  attachment+type parser), `kearns_pmn_minutesdump.py` (minutes-attachment dump),
  `kearns_pmn_supersetcheck.py` (per-date set-difference vs repo index).
- `work/` — intermediate fetched HTML + OCR pages (not part of the dataset contract).

## PMN discovery (for a future refresh)

- Entity: Kearns = **1321** (govType 3). Bodies: Council **5823**, PC **1561**,
  **CRA 9273**, Community Committee 9553 (advisory, no minutes). Decoy: Kearns
  Improvement District = water special district (govType 5 entity 584) — exclude.
- Crawl each body with cumulative `notices.html?id=<body>&page=500` (one GET = full
  history). Minutes attach to the NEXT meeting's notice → parse the meeting date from
  the FILENAME, not the notice's event date. Filenames vary
  (`MM-DD-YYYY Kearns CC Meeting Minutes...`, `YYMMDD_KearnsPC_MinutesApproved.pdf`,
  the odd `..._Approved.pdf` and generic `Month minutes.pdf`) — key off the
  `(Meeting Minutes)` type label AND the filename; content-detect every hit.

## Verification results (see coverage.md for detail)

- **Council 5823 superset CONFIRMED** — repo holds all recoverable PMN council minutes;
  the only PMN-listed-but-absent ones are the 25 purged 2017-01→2018-06 meetings.
- **Purge VERIFIED genuine** — all 25 minutes file objects (ids 285127–413299) now
  return HTTP 404 (315-byte stub); live controls return 200 application/pdf; zero
  Wayback captures. Stays a gap.
- **PC 1561** — one genuine recovery (2019-04-08); PC 2017-2018 gap confirmed genuine
  (MSD approved minutes begin 2019-03); a 2016-02-08 PC doc exists but is below the
  2017 data floor (not ingested).

## Rules honored

Additive only; existing datasets untouched; raws retained; nothing fabricated (the
purge gap stays a gap); polite GET-only. Parent `README.md`/`CLAUDE.md`, `sources.csv`,
`cities.db`, `coverage.json`, `TODO.md` are owned by the orchestrator — not edited here.

## 2026-07-17 — final PMN-crosscheck flag verification (6 flags -> 1)

Verified all 6 against the 2017 floor / 2017-2018 purge; appended 5 exceptions;
re-run (--cached) 6 -> **1**.
- **Recovery lead (1, agenda-grade):** council 2025-01-02 Notice of Public Hearing (body 5823).
- **Exceptions:** wrong_date x2 (2023-03-06 'February minutes.pdf' = held 2023-02-06 PC min /
  file 951487, month-name rescue; 2026-02-09 '01-12-2026 ... DRAFT.pdf' = held 2026-01-12
  council min / file 1390559, filename-date rescue — 2026-02-09's own minutes remain a genuine
  unrecovered gap); other x3 (2019-12-09 'Kearns Metro Township Council' council notice riding PC
  body 1561 — council meeting IS held; 2021-07-21 'Land Use Hearing Officer' admin hearing on PC
  list; 2023-03-20 joint council/PC workshop already documented in PC minutes_unrecovered.csv).
