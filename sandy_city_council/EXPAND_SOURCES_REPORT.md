# expand-city-sources — Sandy expansion report

**Date:** 2026-07-05 · **City:** Sandy (Salt Lake County) · **Skill:** `.claude/skills/expand-city-sources/`
**Fifth city** (after Lehi/Granicus, St. George/Revize, West Jordan/PrimeGov, Provo/OnBase). Purpose:
exercise the **Granicus Legistar Web API** portal family (`webapi.legistar.com/v1/sandyutah`) — the
first city where packets, ordinances, and event structure come from a real JSON API rather than HTML
scraping. All six datasets built; every one passes `validate_dataset.py`; no existing dataset modified;
parent docs written once by the orchestrator. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**agendas stored + attachments INDEXED**) | **462 agenda PDFs stored** (Council 296, PC 157, BoA 9; 60 MB) + **6,446 matter attachments index-only** (~14.9 GB catalogued) | Legistar 3-hop API (events → eventitems → matter attachments). Attachments 10× over the disk ceiling → index-only w/ live URLs + measured `size_mb`. 2020–2026, both bodies symmetric |
| 2 | Housing → `housing_plans/` | **8 docs (~26 MB)**: MIH element (2022 Ch.10 + Ord 23-01), 2017 biennial report, state 23/24/25 + SB 34 | **Current General Plan (adopted 2025-01-07) is a web/ArcGIS product with NO PDF** — landing-page HTML retained; the last PDF-form MIH element is Sept-2022 Ch.10 |
| 3 | Ordinances → `ordinances/` | **170 ordinance matters** (87 adopted, 65 land-use); 83 signed PDFs (194 MB) | Legistar `MatterTypeId=53`. Vote-linkage: **73 high / 7 medium / 6 low / 1 none** (the `none` is post-cutoff, not a defect). Every adopted ord ≤ vote-layer cutoff lands on a real meeting |
| 4 | PMN backfill → `pmn_backfill/` | **8 recovered** (6 Council minutes + 2 RDA; 8.9 MB) | Sandy PMN entity **260**; bodies Council 464 / PC 466 / RDA 465 / BoA 467. **PC & BoA carry zero PMN minutes** (honest coverage zero). Found a 0-byte broken "Final" upload → fell back to Draft |
| 5 | Transcripts → `transcripts/` | **79 ASR captions / 88 videos mapped** (86 MB) | On the third-party **Utah Record** YouTube channel (not a city channel) via OpenUtah's meeting index. **Hard 2025-01 cutoff** — all 215 pre-2025 council meetings have no video. yt-dlp installed clean |
| 6 | Campaign finance → `campaign_finance/` | **83 filings** (7 filers; 40 MB; 2021/23/25) | **EasyVote portal** (`sandycityut.easyvotecampaignfinance.com`, JSON API). 67/83 join elections; **2019 proven absent**; scanned → OCR |

**Existing layer untouched:** `all_votes.csv` 833 motions / 3,975 member-vote rows, 274 council minutes, `db/sandy.db` unchanged.
**New footprint on disk:** ~415 MB (packets attachments index-only; ordinances signed PDFs + transcripts are the bulk).

## Timing
Six agents in parallel; end-to-end ≈ slowest (packets ~70 min — 468 events × attachment enumeration + HEAD-probing 6,446 URLs).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **5 Legistar-vs-minutes ordinance-number discrepancies** (signed-PDF number differs from the minutes
   motion: 22-07↔"22-08", 24-03↔"23-04", 24-17↔"24-18", 24-25↔"2-25" OCR garble, 25-07↔"25-10"). The
   signed Legistar PDF is the enacted doc; the minutes number is the likely error → belongs in a minutes
   remediation pass.
2. **Campaign-finance vs elections:** **Parry Harrison** filed a full 2025 District 3 *primary* set but
   appears nowhere in `election_results` (which captures only the general). Real primary candidate who
   didn't advance → `election_results` primary-coverage review warranted.
3. **2019 Sandy campaign-finance filings** unrecoverable (CivicPlus client-side wall; zero Wayback
   captures) — open acquisition gap.

## Skill changes worth folding in before the next Legistar city
- **Legistar 3-hop packet recipe** (`events` → `eventitems` → `matters/{id}/attachments`): dedupe
  attachments by URL, key each to its **earliest** referencing meeting, carry `MatterAttachmentName` as
  the title (URLs are opaque `attachments/<guid>.pdf`). Legistar attachments are heavy (long tail to
  500 MB) → index-only is almost always right; store the tiny agenda PDFs.
- **`MatterFile` is NOT the ordinance number** (it's a planning case no.); the real `YY-NN` lives in the
  attachment name. `MatterStatusName` under-reports adoption — use `histories` (null flag = adopted,
  only `Fail` = failed).
- **EasyVote is a reusable Utah campaign-finance pattern** — read the SPA bundle for
  `ecf-api.easyvoteapp.com`, `getwebsiteuser/<sub>` → CustomerId → `filer/documentsearch/{id}` →
  `documents/{id}/viewfinalredactedpdf`. `polite_fetch.py` can't send the required headers → needs a
  `--header` passthrough (proposed).
- **Utah Record / OpenUtah** is the transcript source for Utah cities whose videos aren't on a
  city-branded channel — add to the transcript playbook.
- **PMN retroactive minutes:** some bodies (Sandy RDA) attach minutes under the *next* meeting's notice —
  take the meeting date from the PDF/filename, not the notice date.
- **Web/ArcGIS general plans** have no PDF — record `general_plan, format=html, extraction_method=none`
  and treat the newest chapter PDF as the last PDF-form element.

## Source index
`sandy_city_council/sources.csv` regenerated (`scripts/build_sources_index.py sandy`): **7,546 documents
indexed, 100% with recorded URLs** (up from 281 — the six new datasets are now fully cited). Repo-root
`sources_summary.md` refreshed.
