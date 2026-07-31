# expand-city-sources — Vineyard expansion report

**Date:** 2026-07-05 · **City:** Vineyard (Utah County) · **Skill:** `.claude/skills/expand-city-sources/`
**Eighth city** (after Lehi, St. George, West Jordan, Provo, Sandy, Orem, Logan). Purpose: a **second
CivicClerk OData city** (after Orem), and a short-history / fast-growing town (Geneva Steel
redevelopment; usable records ~2014+). All six datasets built; every one passes `validate_dataset.py`;
no existing dataset modified; parent docs written once by the orchestrator. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**INDEX-ONLY**) | **926 rows** (Council 432, PC 336, RDA 158): 807 agendas + 119 agenda packets | CivicClerk OData; ~7.2 GB catalogued (18× budget → index-only). **`$top` is a hard result CAP, not a page size** (silent truncation — must page unbounded). Vineyard's *agendas* are bundled/large too (avg 5 MB), not thin outlines |
| 2 | Housing → `housing_plans/` | **7 docs (~156 MB)** | MIH element = **GP chapter, updated by Ord 2022-17** (2022-09-14); 2019 GP + Future Land Use Map; state 23/24/25 + SB 34. FrontRunner Station Area Plan still **in progress** (forward gap) |
| 3 | Ordinances → `ordinances/` | **84 ordinances** (18 land-use) | Minutes cite numbers richly → within_source backbone (79); **4 high** (signed PDFs from PMN). Code host `municipalcodeonline.com` (JS-gated). Clerk writes `ORDINANCE 2021- 08` (space in number). 2021-12 flagged missing from votes |
| 4 | PMN backfill → `pmn_backfill/` | **59 meeting-dates recovered** (122 MB), almost all **RDA** | Entity 294; Council 530 / PC 531 / RDA 2598. **Repo had NO RDA layer** → every RDA row net-new. **KEY: PMN purges older attachment blobs** — 198/296 listed minutes now 404 (a notice-list diff overstates gaps ~3×). 28 oversize RDA minutes deferred to a future uncapped pass |
| 5 | Transcripts → `transcripts/` | **10 ASR sampled / 47-video map** (~6 MB) | YouTube "Vineyard City". **Video exists only 2019-09 → 2020-12** (brief COVID livestream era); hard cutoff after Dec 2020, so 160+ later meetings have no video |
| 6 | Campaign finance → `campaign_finance/` | **59 filings** (5 cycles 2015–2025) | Self-hosted (Revize live = 2025 only; legacy CivicPlus recovered via **Wayback**). **100% in-scope election join**; extends named coverage **2 cycles below** the 2019 floor. **2023 fully unrecoverable** (purged in CMS migration, Wayback caught only 404s); 2025 general candidates filed no finance statements (city gap) |

**Existing layer untouched:** `all_votes.csv` (at-large; Mayor+5 since 2026, was Mayor+4; **Mayor votes** in the six-member form), 172 council + 102 PC minutes, `db/civic.db` unchanged.
**New footprint on disk:** ~350 MB raw (packets index-only; housing + PMN + campaign-finance are the bulk).

## Timing
Six agents in parallel. The packets agent needed one orchestrator resume (stalled on an 807-file HEAD
probe; index-only was already the certain call, so it finalized on partial sizes; validator PASS).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **A full RDA minutes layer (43 meetings 2018–2026) is recoverable via PMN** that the core repo lacks —
   candidate for promotion after review; 28 more are oversize-deferred.
2. **Ordinance 2021-12** genuinely adopted (signed PDF) but not cited by number in any vote row — vote-audit lead.
3. **2023 campaign-finance cycle unrecoverable** (purged) though `election_results` has the winners — a
   permanent source gap unless the city re-posts.

## Skill changes worth folding in
- **CivicClerk `$top` is a hard CAP** (silent truncation) — page from unbounded `Events`, never trust `$top=N`.
  Vineyard agendas are large (not thin outlines) — probe before assuming "Agenda = small."
- **PMN purges old attachment blobs** — verify file liveness (a notice-list diff overstates recoverable gaps
  ~3×; report 404s as honest source-gone). `--max-bytes` no-ops on PMN (no HEAD Content-Length) — use a
  ranged GET or stream-and-abort; recent packets reach 79 MB.
- **Ordinance number regex must tolerate whitespace** around the dash (`2021- 08`).
- **Wayback 1-MiB crawler-cap truncation** is a new failure mode — a CDX "200 + application/pdf" can be a
  truncated unreadable capture; `pdfinfo`-check after fetch and label rather than trust CDX status.
- **CivicPlus DocumentCenter enumeration** — CDX-enumerate `/DocumentCenter/View/<id>` + name-match; prefix
  saved files with the View id.

## Source index
`vineyard_city_council/sources.csv` regenerated: **1,692 documents indexed, 99% with recorded URLs**
(up from 286). Repo-root `sources_summary.md` refreshed.
