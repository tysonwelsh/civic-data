# PMN backfill — availability record (Sandy City)

**As-of:** 2026-07-05 · **Checked by:** expand-city-sources Source 4 (PMN cross-check)

## Sandy on the Utah Public Notice Website (PMN)
- **Entity id = 260** (found via `/pmn/list/entities.html?id=3&limit=2000`, govType 3 = Municipality).
- **Public bodies** (via `/pmn/list/publicBodies.html?id=260&limit=2000`) — ids are assigned
  GLOBALLY, not sequentially, so they were discovered, never guessed:

  | Body | PMN id | Checked |
  |------|-------:|:--------|
  | City Council | **464** | yes — cross-checked |
  | Planning Commission | **466** | yes — cross-checked |
  | Redevelopment Agency | **465** | yes — cross-checked |
  | Board of Adjustments | **467** | yes — enumerated (no minutes on PMN) |
  | Architectural Review Committee | 6495 | not checked (no minutes layer in repo) |
  | Public Utilities Advisory Board | 468 | not checked |
  | Historic Commission | 2532 | not checked |
  | CDBG Committee | 2533 | not checked |
  | Citizen Corps Council | 470 | not checked |
  | Sandy Arts Guild | 1990 · Alta Canyon Advisory 7675 · Alta Canyon Rec SSD 2322 · Business Continuity 3007 · City Recorder 9271 · CDD Admin Hearing 8859 · Metro Fire 2943 | not checked (advisory/ops bodies) |

## What was checked
Full notice history for the four meeting-body ids via the **GET** browse endpoint
`/pmn/list/notices.html?id=<bodyId>&page=300` (cumulative paging — one high page = entire history):
- **City Council 464** — 1,588 notices, 2014-10-28 … 2026-07-07.
- **Planning Commission 466** — 928 notices, 2008-04-10 … 2026-07-02.
- **Redevelopment Agency 465** — 90 notices, 2008-04-25 … 2023-08-22.
- **Board of Adjustments 467** — 28 notices, 2008-05-02 … 2025-12-11.

Each notice's attachments were parsed for the `(Meeting Minutes)` type label; each minutes-bearing
meeting date was set-differenced (±4 days) against the repo's coverage: council vs
`meeting_minutes/minutes_index.csv`, PC vs `planning_commission/all_votes.csv` dates, RDA vs
(none — no RDA minutes layer exists).

## What exists / what was recovered
- **8 meeting dates** within the 2020–2026 scope had PMN documents the repo lacked. **All 8
  recovered** (`raw/` PDFs + `text/` extractions + `index.csv`): 6 City Council minutes
  (2023-10-17, 2023-11-07, 2026-04-28, 2026-06-09, 2026-06-16, 2026-06-23) and 2 Redevelopment
  Agency minutes (2022-05-17, 2022-06-07). See `coverage.md`.
- After recovery, **0 in-scope PMN minutes remain unrecovered**.

## What is NOT here (honest gaps / deliberate exclusions)
- **Planning Commission minutes do not exist on PMN for Sandy** — every PC attachment is a
  project public-hearing `(Other)` notice or an agenda; there are **zero** `(Meeting Minutes)`.
  The repo likewise has no PC minutes files (PC is Legistar-API-built). Honest zero.
- **Board of Adjustments** — 28 notices, none with minutes. Nothing to recover.
- **2023-11-07 Council FINAL minutes** (PMN file 1052569) is a **0-byte broken file** on PMN;
  the Draft (file 1050973) was recovered in its place. The broken fetch is logged
  (`ok:false, bytes:0`) in `raw/_fetch_log.jsonl`.
- **Pre-2020 PMN council minutes** (174 notices) — below the repo's 2020 data floor; enumerated in
  `raw/_notices_464_p300.html` and `council.json`, deliberately not downloaded.
- **PMN historical search is POST-only** (`/pmn/searchresult.html`, CSRF) — disallowed by the
  polite-scraper rule. The GET cumulative browse endpoint returned each body's complete history, so
  no coverage was lost by avoiding POST.
- **Advisory / operational bodies** (Architectural Review, Public Utilities, Historic Commission,
  CDBG, etc.) were not cross-checked — Source 4 was scoped to the minute-bearing meeting bodies.

## Provenance
Raw bytes + SHA-256 + HTTP status for every fetch are in `raw/_fetch_log.jsonl` (written by
`scripts/polite_fetch.py`, browser UA, per-notice Referer, ≥1s throttle). Parser + cross-check
code: `parse_notices.py`, `crosscheck.py`. Parsed notice inventories: `council.json`, `pc.json`,
`rda.json`, `boa.json`. Recovery list: `recoverable.json`.
