# South Salt Lake pmn_backfill — availability (as-of 2026-07-13)

## What was checked
1. **Every SSL Utah Public Notice (PMN) body** — PMN municipality entity **271**. Confirmed the
   three governance bodies the core used (**1295** City Council, **1296** RDA, **1297** Planning
   Commission) and swept all other SSL bodies for misfiled/late-attached minutes:
   Arts Council 5067, Civilian Review Board 7603, Community Development Director 4109, Director of
   Community Development 4247, Municipal Building Authority 2821, Ordinances 7441, Police 4553,
   Public Works 4571, Purchasing 6733, Taxing Entity Committee 2763/2839. Crawled each body's
   cumulative notice list (`/pmn/list/notices.html?id=<body>&page=500`, GET-only) and captured
   every attachment (file id, ext, filename).
2. **The `>22 MB` PMN candidates the core skipped** under its size cap (21 council, 2 RDA, 18 PC)
   — each downloaded and content-detected for roll-call grammar.
3. **The city's CivicPlus AgendaCenter** (`sslc.gov/AgendaCenter`, categories 4/3/5) — every
   *Minutes*-slot doc across 2020–2026, plus every `ArchivedMinutes` reachable through each doc's
   `PreviousVersions` page — content-detected for recorded-minutes grammar.
4. **Wayback / legacy domains** — `web.archive.org` CDX for `southsaltlakecity.com` and `sslc.gov`
   minutes; the `sslc.gov` City-Recorder and Archive pages.

## What exists / was recovered
- **130 recorded roll-call minutes (2022–2026)** the core had logged as agenda-only, recovered
  from the **AgendaCenter `ArchivedMinutes` slot (113)** and, for 2022–23 PC, the **`Minutes`
  slot (17)**. Council 79, RDA 30, PC 21. See `coverage.md` and `index.csv`. Born-digital,
  clean `pdftotext -layout` (corpus screen CLEAN — no OCR garble, no dict/weird-char outliers).
- **2022 Planning-Commission minutes** exist (9 recovered) — the core's "PC minutes begin
  2023-01-19; 2020–2022 never published" is refuted for 2022 (published on the AgendaCenter).

## What does NOT exist (honest gaps — not scraper misses)
- **216** council/RDA/PC agenda-only dates have **no recorded minutes on either PMN or the
  AgendaCenter** — the residual, now-smaller publication cliff (mostly council work-meetings and
  mid-2021→2022 council regulars). Verified: the PMN "Minutes" slot served agenda packets, and the
  AgendaCenter had no `ArchivedMinutes`/minutes previous-version for these dates.
- **2020–2021 Planning-Commission minutes** — genuinely absent; the AgendaCenter PC listing itself
  starts 2022 and PMN 1297 carries no PC minutes before 2023-01-19.
- **No PMN minutes were missed within the 2020 data floor.** The only genuine PMN minutes the core
  did not take are **2014–2017** (before the floor) — out of scope, not recovered.
- **Legacy `southsaltlakecity.com`** held council minutes only for **1999–2008** (HTML) — far
  before the floor; irrelevant to the 2021→2025 gap.
- **City YouTube** `@SouthSaltLakeCity` carries meeting **video** (not minutes) — noted, not
  fetched (video is not a substitute for a recorded roll-call minutes document).

## Caveats / acquisition limits
- Recoveries are **from the city portal (AgendaCenter), not PMN** — `source=agendacenter`,
  `pmn_body_id`/`pmn_file_id` blank, `recovery_source` set. This is a *separate* dataset for
  deliberate review; the audited `meeting_minutes/`, `planning_commission/`, `db/` layers were
  **not** modified.
- **87** current-*Minutes*-slot AgendaCenter files `>12 MB` (agenda packets) were HEAD-size-skipped
  rather than downloaded in full; where those dates have recorded minutes they were recovered from
  the small `ArchivedMinutes` previous-version instead, so no sampled recovery was lost to the cap.
- Non-governance bodies with real minutes (**Civilian Review Board**, **Arts Council**) were
  identified but **not** recovered — outside the council/RDA/PC scope of this repo.
