# expand-city-sources — Ogden expansion report

**Date:** 2026-07-06 · **City:** Ogden (Weber County) · **Skill:** `.claude/skills/expand-city-sources/`
**Twelfth city** (after Lehi, St. George, West Jordan, Provo, Sandy, Orem, Logan, Vineyard, Nephi,
Park City, SLC). Portal: **CivicPlus CivicEngage** (DocumentCenter minutes + AgendaCenter) + PMN + YouTube.
All six datasets built; every one passes `validate_dataset.py`; no existing dataset modified. Concurrency
pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**STORED**) | **166 agendas** (PC 162, Council 4), 19 MB | **Ogden's AgendaCenter has NO packet/staff-report type** — only thin agendas (no bundles, contrary to the disk lesson) → all stored. **Council publishes almost nothing here** (substance is in DocumentCenter minutes); **PC agendas are a SUPERSET — 71 PC meeting-dates whose minutes the repo never recovered** (additive) |
| 2 | Housing → `housing_plans/` | **6 docs (~97 MB)** | MIH = **General Plan Chapter 7 (amended 2022)**; 2020 GP consolidated update; state 23/24/25 + SB 34. "Plan Ogden" rewrite in progress (not yet adopted) |
| 3 | Ordinances → `ordinances/` | **308 adopted** (107 land-use) | Minutes cite numbers richly → **27 high** (Recorder "Synopsis of Ordinance" affidavits on DocumentCenter/PMN) / 276 within_source / 5 none. **Ord 2025-01 adopted 2025-01-07 but there's no 2025-01-07 meeting in `meeting_minutes/`** — first 2025 council meeting appears un-ingested |
| 4 | PMN backfill → `pmn_backfill/` | **10 recovered** (2.9 MB) — incl. the **2022–23 RDA/MBA target gap** | Entity 225; historical CC/RDA/MBA filed under a **combined body 6587** (the individual RDA 321/MBA 322 pages are 6-month-capped → why originally missed). **Recovered 7 of the 2023 RDA minutes** (they existed after all) + 1 2024 RDA + 2 2020 MBA. **2022 RDA/MBA and 2023 MBA confirmed NOT on PMN** (honest zeros) |
| 5 | Transcripts → `transcripts/` | **683 videos mapped / 10 ASR sampled** (11 MB) | Ogden City Council YouTube (`/videos`+`/streams` disjoint = 683). Coverage 2018–2026. **Recipe fix:** the `player_client=android` yt-dlp flag returns ZERO subs here — default client works |
| 6 | Campaign finance → `campaign_finance/` | **38 filings** (2019/21/23; 93 MB) | Self-hosted on per-cycle `/<id>/<YYYY>-Elections` DocumentCenter pages. **100% election join 2019–2023** (all 12 winners); 18 primary-eliminated filers imply primaries the general-only `election_results` omits (flagged). **2025 cycle not yet published** (verified 4 ways) |

**Existing layer untouched:** `all_votes.csv` (7-member council + strong mayor; Mayor doesn't vote; RDA/MBA in-council pre-2024), 504 council + 72 PC minutes, `db/ogden.db` unchanged.
**New footprint on disk:** ~230 MB raw (packets + housing + campaign-finance stored; ordinances/pmn small).

## Timing
Six agents in parallel; end-to-end ≈ slowest (ordinances ~20 min). No packet-agent stall (the AgendaCenter had no bundles to probe → stored directly).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **First 2025 council meeting (2025-01-07) appears un-ingested** — Ord 2025-01 adopted there per the Recorder
   synopsis, but `meeting_minutes/` jumps to 2025-01-14. Ingestion gap to check.
2. **7 recovered 2023 RDA minutes** (net-new, via PMN combined body 6587) — flagged for promotion into the audited layer.
3. **71 PC meeting-dates have agendas but no minutes** in the repo (2020–2023 PC minutes are sparse) — an
   additive PC-coverage signal.
4. **Ogden ran municipal primaries 2019/2021/2023** (18 primary filers) not reflected in the general-only
   `election_results` — flagged for an elections review.
5. **2025 campaign-finance cycle unpublished** (winners known, no filings online yet) — watch for republication.

## Skill changes worth folding in
- **A CivicPlus AgendaCenter may expose only thin Agendas + Minutes and NO packet type** — check for `AgendaPacket`/"Packet" up front; if absent, the thin agenda IS the deliverable (store it), don't assume index-only.
- **PMN "combined-body" pattern:** where Council also sits as RDA/MBA, the per-body pages are 6-month-capped and near-empty — the full history lives under a single combined public body; enumerate ALL bodies and check for a combined one before concluding a gap.
- **CivicEngage Recorder "Synopsis of Ordinance" affidavits** are an independent Source-3 corroborator; the authoritative campaign-finance index is the per-cycle `/<id>/<YYYY>-Elections` page (grep the hub's sidebar hrefs — not the sitemap/nav/DocumentCenter root).
- **yt-dlp `player_client=android` returns zero subs on some channels** — fall back to the default client.

## Source index
`ogden_city_council/sources.csv` regenerated: **1,142 documents indexed, 98% with recorded URLs**
(up from 603). Repo-root `sources_summary.md` refreshed.
