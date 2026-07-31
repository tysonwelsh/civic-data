# PMN backfill — availability record

**As-of:** 2026-07-05 · **Checked by:** expand-city-sources Source 4 (PMN cross-check)

## Park City PMN entity + public-body ids (CONFIRMED 2026-07-05)

Discovered via the GET entity chain (no guessing, ids are assigned globally not per-city):
`/pmn/list/entities.html?id=3&limit=2000` (government type 3 = Municipality) → **Park City entity
id = 233** → `/pmn/list/publicBodies.html?id=233&limit=2000` → every Park City body + id.

| Body | PMN body id |
|------|------------:|
| **City Council** | **653** |
| **Planning Commission** | **1860** |
| **Redevelopment Agency (RDA)** | **654** ✅ confirmed |
| Housing Authority | 657 |
| Municipal Building Authority | 655 |
| Historic Preservation Board | 659 |
| Board of Adjustment | 4645 |
| Board of Appeals | 663 |
| Blue Ribbon Housing Commission | 5301 |
| Library Board | 662 |
| Recreation Advisory Board | 661 |
| Public Art Advisory Board | 666 |
| Citizens Open Space Advisory Committee | 665 |
| Water Service District | 656 |
| (plus ~12 advisory / task-force / procurement bodies — see `raw/_bodies_233.html`) | — |

## What was checked
Full PMN notice history for three Park City bodies, via the GET cumulative browse endpoint
`/pmn/list/notices.html?id=<bodyId>&page=300` (saved saturated to `raw/_notices_<id>_p300.html`):
- **City Council — 653** — 1,020 notices, 2015 … 2026-07-09; 432 carry a `(Meeting Minutes)`
  attachment (232 dated ≥2020).
- **Planning Commission — 1860** — 612 notices, 2008-10-08 … 2026-07-08; 43 with minutes (all ≥2020).
- **Redevelopment Agency — 654** — 44 notices, 2008-10-30 … 2025-06-12; 14 with minutes (all ≥2020).

Every notice's attachments were parsed for the `(Meeting Minutes)` type label; each minutes-bearing
meeting date was set-differenced against the repo's audited indexes (`meeting_minutes/`,
`planning_commission/`), tolerance ±4 days. For each candidate gap the meeting date printed **inside**
the PDF was read to confirm before counting.

## What exists / what was recovered
- **2 City Council meeting-minutes PDFs** dated in scope existed on PMN but not the repo
  (**2026-06-04**, **2026-06-11** — newer than the repo's last CivicClerk minutes, 2026-05-22).
  Both downloaded (`raw/`), extracted (`text/`, `pdftotext -layout`, born-digital, screener-clean),
  indexed `status=recovered`. See `coverage.md`.
- After recovery, **0 in-scope PMN minutes remain unrecovered.**
- **0 source-unavailable (404-purged)** attachments.

## Redevelopment Agency (654): honest zero net-new
CivicClerk has no RDA category, so RDA body 654 was the high-value target. Its 14 in-scope
Meeting-Minutes attachments were all downloaded and read — **every one is the combined
"PARK CITY COUNCIL MEETING MINUTES" document** (with the in-council Redevelopment Agency recess
section) for a council date the repo already holds. **0 standalone RDA-only minutes exist on PMN.**
The 14 files are retained (`raw/`+`text/`) and indexed `status=duplicate-not-promoted` for reviewer
verification. There is no separate RDA minutes layer to promote — the repo's `body=RDA` rows
(extracted from the in-council recess) already model the RDA.

## What is NOT here (honest gaps / deliberate exclusions)
- **Pre-2020 PMN minutes** (195 council; 0 PC/RDA below floor) — below the repo's 2020 data floor;
  enumerated in the saturated notice pages + `council.json` (file ids present) but not downloaded.
- **PMN historical search is POST-only** (`/pmn/searchresult.html`, CSRF) — disallowed by the
  polite-scraper rule. Enumeration used the GET cumulative browse endpoint, which returns the
  complete per-body history, so no coverage was lost.
- **Housing Authority (657), MBA (655), Historic Preservation Board (659), Board of Adjustment
  (4645)** and advisory boards were not cross-checked — task scoped to Council + PC + RDA. HA/MBA,
  like RDA, run as in-council recesses already captured in the repo.

## Provenance
Raw bytes + SHA-256 + HTTP status for every fetch: `raw/_fetch_log.jsonl` (written by
`scripts/polite_fetch.py`, browser UA, notice-page Referer, ≥1.5s throttle). Parser + cross-check
code: `parse_notices.py`, `crosscheck.py`. Parsed notice inventories: `council.json`, `pc.json`,
`rda.json`. Cross-check output: `recoverable.json`.
