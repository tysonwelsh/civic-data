# expand-city-sources — Park City expansion report

**Date:** 2026-07-05 · **City:** Park City (Summit County) · **Skill:** `.claude/skills/expand-city-sources/`
**Tenth city** (after Lehi, St. George, West Jordan, Provo, Sandy, Orem, Logan, Vineyard, Nephi) — the
last of the queued batch. Portal: **CivicClerk OData** (minutes/packets/video) + a **Revize static
`/Documents/` tree** (housing/campaign-finance) + a **Municode S3 ordinance bucket**. All six datasets
built; every one passes `validate_dataset.py`; no existing dataset modified. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**HYBRID**) | **942 rows**: 474 agendas STORED (52 MB) + 468 agenda packets INDEX-ONLY (**30 GB**) | CivicClerk (Council 26 + PC + HPB). Agendas tiny/born-digital → stored; packets avg 66 MB (resort image-heavy) → index-only. 100% vote-date join; PC agenda PDFs only reliable from ~2023 (older = video-only, honest zeros) |
| 2 | Housing → `housing_plans/` | **15 docs (~71 MB)** | **Standalone Five-Year MIHP** (2022 + amended + 2025, w/ signed resolutions) AND a **GP housing chapter** (2025 GP, goal to house 15% of workforce). Deed-restricted affordable-housing program |
| 3 | Ordinances → `ordinances/` | **260** (160 land-use, 62%) | **Strong independent archive** — Municode **public S3 bucket** of signed ordinance PDFs (each w/ its own PASSED-AND-ADOPTED date) → **93 high** / 162 within_source / 5 none. 2 consent-agenda adoptions flagged missing from votes |
| 4 | PMN backfill → `pmn_backfill/` | **2 net-new Council** (June 2026); RDA honest zero | Entity 233; Council 653 / PC 1860 / **RDA 654**. RDA convenes **in-council** (recess model) — all 14 PMN "RDA minutes" are the combined council doc the repo holds (verified 14/14). No purge |
| 5 | Transcripts → `transcripts/` | **194 videos mapped / 0 captions** | Park City publishes **meeting VIDEO** (MP4s via CivicClerk's own media feed) but **NO captions of any kind** (no ASR, no YouTube). The map is the deliverable; video only 2023-09+. Whisper proposed for the 3 newest un-minuted meetings |
| 6 | Campaign finance → `campaign_finance/` | **126 filings** (2017–2025; 91 text / 45 scanned) | Self-hosted on the Revize `/Documents/.../Campaign Disclosures/` tree. **89% election join.** Flags **Betsy Wallace** (2023 primary filer absent from the roster — withdrew) |

**Existing layer untouched:** `all_votes.csv` (5 at-large council; Mayor tie-breaker), 238 council + 160 PC minutes, 97 public comments, `db/parkcity.db` unchanged. Park City **runs its own elections** (Summit County defers).
**New footprint on disk:** ~475 MB raw (packets agendas 52 MB + pmn 170 + campaign-finance 100 + housing 71 + ordinances 83; packets index-only 30 GB catalogued off-disk).

## Timing
Six agents in parallel. The packets agent needed one orchestrator resume (stalled on a background 468-file
size-probe monitor; the agenda-store/packet-index split was already decided → finalized synchronously; PASS).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **2 consent-agenda ordinance adoptions** (2024-08, 2026-08) exist as signed PDFs but the vote layer records
   only "approve the Consent Agenda" — vote-extraction leads.
2. **Betsy Wallace** filed a 2023 primary campaign-finance statement but is absent from `election_results`
   (candidacy withdrawn) — finance surfacing an election-record gap.
3. **Meeting video exists but is un-captioned** (194 recordings) — a Whisper transcript layer is the only path
   to text for the pre-minutes-publication meetings.

## Skill changes worth folding in
- **CivicClerk is a video source** — its `Events` feed carries `mediaSourcePathMp4`/`mediaStreamPath` (Azure
  CDN MP4); add as a first-class transcript probe. `$expand=publishedFiles`→400 (publishedFiles is inline);
  `EventCategories.name` is null (map category names off events); `$top`/`$skip` ignored (follow `@odata.nextLink`).
- **Municode cities expose a public, listable S3 ordinance bucket** (`municipalcodeonline.com-new/<city>/ordinances/documents/`)
  — a first-class independent Source-3 archive, far stronger than the minutes-only default.
- **parkcity.gov is Revize, not CivicPlus**, and its `showpublisheddocument/<id>` deep links **404 sitewide** to
  non-browser clients — the working route is the static **`/Documents/<section>/…pdf`** tree found by crawling the
  `.php` content pages' relative hrefs. Campaign-finance filings live there, distinct from the canvass `showpublisheddocument` pattern.
- **OCR env trap:** tesseract/leptonica can't read `pdftoppm` output from an absolute path / with anaconda on `PATH`
  — render `-jpeg` and run tesseract from the image dir with a relative name (foreground). Recurs across cities.
- **Scratchpad hygiene:** per-agent harvest/build scripts MUST use dataset-unique filenames (a leftover Vineyard
  `harvest.py` briefly polluted Vineyard during this run — caught + restored).

## Source index
`park_city_city_council/sources.csv` regenerated: **2,066 documents indexed, 100% with recorded URLs**
(up from 503). Repo-root `sources_summary.md` refreshed.
