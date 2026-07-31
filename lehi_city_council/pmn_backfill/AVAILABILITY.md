# PMN backfill — availability record

**As-of:** 2026-07-02 · **Checked by:** expand-city-sources Source 4 (PMN cross-check)

## What was checked
- Utah Public Notice Website (PMN) full notice history for two Lehi public bodies, via the
  GET browse endpoint `/pmn/list/notices.html?id=<bodyId>&page=<N>` (cumulative paging):
  - **City Council — body 2512** — 981 notices, 2009-10-27 … 2026-06-09.
  - **Planning Commission — body 2651** — 565 notices, 2010-02-04 … 2026-07-09.
- Every notice's attachments were parsed for the `(Meeting Minutes)` type label and each
  minutes-bearing meeting date was set-differenced against the repo's audited minutes indexes
  (`meeting_minutes/minutes_index.csv`, `planning_commission/minutes_index.csv`), tolerance ±4 days.

## What exists / what was recovered
- **6 meeting-minutes PDFs** dated within the repo's 2020-present scope existed on PMN but not in
  the repo. All 6 were downloaded (`raw/`), extracted (`text/`, `pdftotext -layout`, born-digital,
  screener-clean), and indexed (`index.csv`). See `coverage.md`.
- After recovery, **0 in-scope PMN minutes remain unrecovered.**

## What is NOT here (honest gaps / deliberate exclusions)
- **Pre-2020 PMN minutes** (127 council, 10 PC) — below the repo's 2020 data floor; enumerated in
  the saturated notice pages + `council.json`/`pc.json` but deliberately not downloaded.
- **PMN historical search is POST-only.** `/pmn/searchresult.html` (the UI's path to arbitrary
  date-range queries) requires a POST with a CSRF token — disallowed by the polite-scraper rule and
  unsupported by `polite_fetch.py`. Full enumeration here relied instead on the **GET** cumulative
  browse endpoint, which returns the complete per-body history, so no coverage was lost by avoiding POST.
- **RDA (3315), LBA (7881), Board of Adjustments (2661)** and Lehi's advisory boards were not
  cross-checked — Source 4 was scoped to council + PC.
- **PMN is a pre-meeting NOTICE service, not a minutes archive.** Most Lehi notices are agendas /
  public-hearing notices with **no attachment**; minutes attachments appear on only ~26% of council
  notices and ~5% of PC notices, concentrated in specific eras. The authoritative minutes source for
  this repo remains **Granicus**; PMN's role here is a gap-filler, which yielded 6 items.

## Provenance
Raw bytes + SHA-256 + HTTP status for every fetch are in `raw/_fetch_log.jsonl`
(written by `scripts/polite_fetch.py`). Parser + cross-check code: `parse_notices.py`,
`crosscheck.py`. Full parsed notice inventories: `council.json`, `pc.json`.
