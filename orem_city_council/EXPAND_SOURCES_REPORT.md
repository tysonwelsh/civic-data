# expand-city-sources — Orem expansion report

**Date:** 2026-07-05 · **City:** Orem (Utah County) · **Skill:** `.claude/skills/expand-city-sources/`
**Sixth city** (after Lehi/Granicus, St. George/Revize, West Jordan/PrimeGov, Provo/OnBase,
Sandy/Legistar). Purpose: exercise the **CivicClerk (CivicPlus) OData API** portal family
(`oremut.api.civicclerk.com/v1`) + Orem's Google Drive minutes archive. All six datasets built;
every one passes `validate_dataset.py`; no existing dataset modified; parent docs written once by
the orchestrator. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**agendas stored + packets INDEXED**) | **221 agenda PDFs stored** (35 MB) + **204 full agenda-packets index-only** (~5.8 GB catalogued) | CivicClerk OData. Docs live in `event.publishedFiles[]` (null `minutesFile`/`agendaFile` slots are a red herring); download via `Meetings/GetMeetingFileStream(fileId,…)`. Council 88% carry a full packet, PC 96% (asymmetry logged) |
| 2 | Housing → `housing_plans/` | **14 docs (~51 MB)** | **MIH element = General Plan Chapter 4 §4.4.2, not a standalone doc** (2023 GP update; 2018 study; 2025 FrontRunner Station Area Plan/HB 462 record; state 23/24/25 + SB 34). R-2023-0004 URL dead post-migration (gap) |
| 3 | Ordinances → `ordinances/` | **95 adopted** (47 land-use, Title 22) | **Orem minutes NEVER print an ordinance number** (0 hits across 130 files) → minutes-derived `within_source` backbone (89 within_source / 6 none, no independent `high` tier). Code host = EnCodePlus/GovOS (current text only); orem.gov WP "Ordinance" posts (`O-YYYY-NNNN`) began mid-2026 |
| 4 | PMN backfill → `pmn_backfill/` | **39 meeting-dates recovered** (44 files, ~38 MB) | Entity 229; bodies Council 734 / PC 642 / BoA 643 / RDA 893 / MBA 894 / SSLD 895. Fills the documented **Apr–Jun 2021 Council gap**; recovers **new RDA (13) + MBA (6)** layers the repo never had |
| 5 | Transcripts → `transcripts/` | **10 ASR sampled / 111 videos mapped** (~11 MB) | YouTube **"Orem City" @TheCityofOrem** (Council + PC playlists). Sample-only per owner policy. 2020 = 1 video (COVID); PC video stops 2022-09. yt-dlp installed clean (real recovery, not URL-only) |
| 6 | Campaign finance → `campaign_finance/` | **91 filings, 23 candidates** (~33 MB; 2021 annuals/2023/2025) | Self-hosted on **`orem.gov/wp-content/uploads/`** (no third-party portal). **100% election join** (28/28 candidate-year pairs); no discrepancies. **2019 + 2021 candidate filings confirmed absent** (paper-only at the recorder). 41 born-digital / 50 OCR |

**Existing layer untouched:** `all_votes.csv` (Orem is Aye/Nay-only), 130 council + 114 PC minutes, `db/civic.db` unchanged.
**New footprint on disk:** ~168 MB raw (packets index-only; housing + PMN + campaign-finance are the bulk).

## Timing
Six agents in parallel; end-to-end ≈ slowest (campaign finance ~29 min — OCR of 50 scanned filings).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **Minutes/votes trail the recorder's ordinance publishing by ~1 meeting:** all 6 June-2026
   ordinances post-date `all_votes.csv`'s 2026-05-05 cutoff (`match_confidence=none`). A refresh target.
2. **New RDA + MBA minutes layers** recovered via PMN (26 meetings) that the core repo never had —
   candidate for promotion into the audited minutes layer after review.
3. **Campaign finance corroborates the "no central DB" finding:** `disclosures.utah.gov` municipal
   folders enumerate only via JS/POST and are empty via GET — Utah-County cities file with the city,
   confirming the repo-wide research note (see `TODO.md`).

## Skill changes worth folding in
- **CivicClerk OData:** documents are in `event.publishedFiles[]`, NOT the null `minutesFile`/`agendaFile`
  slots; download via the **collection-bound** `Meetings/GetMeetingFileStream(fileId=…,plainText=false)`
  (event-scoped/unbound variants 404/500); HEAD→405 and Range ignored (size via a streamed GET reading
  `Content-Length`); `$top` still paginates at 15 (follow `@odata.nextLink`); `$select`+`$orderby asc`→500.
- **Ordinances Source 3:** grep the minutes for a number pattern FIRST and branch to a number-less
  `within_source` backbone when absent (Orem prints none — the counter-example to Lehi's rich citations).
- **PMN Source 4:** the meeting-datetime column is unreliable — resolve date by filename → title →
  datetime, and reassign body from the filename (bundled RDA/SSLD minutes get re-filed); no `(Agenda)`
  type label exists on PMN; budget OCR (16/44 files scanned).
- **Campaign finance Source 6:** run Wayback **CDX on the uploads host** after finding the live page —
  it surfaces still-live but unlinked superseded filings; dedupe the election universe (primary+general
  double-rows) before the last-name join; the `disclosures.utah.gov` GET-empty check is the fastest proof
  a city self-hosts.
- **Skill path bugs to fix:** `polite_fetch.py` is under `.claude/skills/expand-city-sources/scripts/`
  (not `scripts/`); `screen_corpus.py` is under `audit-city-data/scripts/` (not expand-city-sources);
  validators must map `format=ocr → scanned`.

## Source index
`orem_city_council/sources.csv` regenerated: **1,034 documents indexed, 100% with recorded URLs**
(up from 262). Repo-root `sources_summary.md` refreshed.
