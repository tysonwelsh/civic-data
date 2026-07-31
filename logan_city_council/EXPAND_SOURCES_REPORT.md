# expand-city-sources — Logan expansion report

**Date:** 2026-07-05 · **City:** Logan (Cache County) · **Skill:** `.claude/skills/expand-city-sources/`
**Seventh city** (after Lehi/Granicus, St. George/Revize, West Jordan/PrimeGov, Provo/OnBase,
Sandy/Legistar, Orem/CivicClerk). Purpose: a **second Revize static-CMS city** (no API — after
St. George) + Cache County. All six datasets built; every one passes `validate_dataset.py`; no
existing dataset modified; parent docs written once by the orchestrator. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**INDEX-ONLY**) | **1,124 rows** (Council 1,096, RDA 28): 222 agendas, **867 staff reports**, 11 proclamations, 24 notices | Unlike St. George's bundles, Logan Revize serves **separated staff-report PDFs** (richer granularity). 1,124 docs → index-only w/ live URLs; 288 size-probed |
| 2 | Housing → `housing_plans/` | **7 docs (~97 MB)** | **Logan 2045 General Plan (2026)** + a **standalone 2022 MIH Plan (Res 22-46)** AND the GP-embedded element (both retrieved); 2018 biennial; state 23/24/25 + SB 34 |
| 3 | Ordinances → `ordinances/` | **496 items** (167 ord + 329 res; 143 land-use); 162 signed PDFs (497 MB) | **Independent number-bearing archive exists** — City Recorder `ordinances.php`/`resolutions.php`. Linkage: **461 high** (two-source) / 11 within_source / 24 none. 3 land-use ords flagged missing from votes |
| 4 | PMN backfill → `pmn_backfill/` | **0 net-new** (honest zero — repo is a complete superset) | Entity 189; Council 494 / PC 487 / RDA 495. **Caught a recon error** (recon said RDA=1277, which is actually Salt Lake City's RDA) via the mandated entity→body chain |
| 5 | Transcripts → `transcripts/` | **10 ASR sampled / 155 videos mapped** (~6 MB) | YouTube "City of Logan" — videos on the **`/streams`** tab, not `/videos`. Sample-only per owner policy. Hard 2020 video gap (channel starts Jan 2021) |
| 6 | Campaign finance → `campaign_finance/` | **45 filings** (~69 MB; 13 candidates) | City recorder election page (Revize). **100% election join.** 2025 complete; 2021 via Wayback; **2023 provably unrecoverable** (Wayback captured only 302→CDN redirects, target 404); 2019 never published |

**Existing layer untouched:** `all_votes.csv` (5 at-large council; Mayor doesn't vote), 198 council + 130 PC minutes, separate RDA body, `db/civic.db` unchanged.
**New footprint on disk:** ~670 MB raw (packets index-only; ordinances signed PDFs + housing + campaign-finance are the bulk).

## Timing
Six agents in parallel. The packets agent needed one orchestrator resume (it stalled waiting on a
full 1,124-file HEAD size-probe; the storage decision — index-only — was already determined, so it
finalized on partial sizes; validator PASS).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **3 adopted land-use ordinances missing from `all_votes.csv`:** Ord 22-13 (LDC Amendment), 23-15
   (Tempki Subdivision Easement), 26-12 (Data-Center Moratorium) — vote-extraction leads.
2. **Campaign finance vs elections:** 2021 Council winner **Ernesto López** never published a finance
   statement (city publishing gap — flagged, `election_results` untouched).
3. **Logan 2023 campaign-finance cycle** (21 filings) is provably unrecoverable online — a raw-PDF
   backfill target if the city re-posts (see TODO).

## Skill changes worth folding in
- **Revize Recorder document-center** (`city_recorder/ordinances.php`+`resolutions.php`) is the
  canonical independent adopted-ordinance archive for Revize cities — superior to the codified-code
  hosts (American Legal 403/current-only; Municode SPA shell). Add to the Source-3 Revize playbook.
- **PMN Source 4:** never trust a hand-noted body id (recon's 1277 was another city) — resolve via
  entity→publicBodies every run; **notice date ≠ minutes date** is the central false-positive trap
  (read the meeting date printed inside the PDF); Logan PMN has no `(Agenda)` attachment type.
- **Transcripts:** meetings live on the channel `/streams` tab, not `/videos`; `yt-dlp` was already
  installed (the Lehi "absent" blocker doesn't generalize) — check `--version` first.
- **Campaign finance:** filings are named `<Candidate> <Month D, YYYY>.pdf` (keyword CDX filters miss
  them — enumerate the directory and pattern-match); **Wayback 302→CDN captures are a distinct failure
  mode** (a CDX "200" can `id_`-fetch to 404 because the capture is a redirect whose target was never
  archived — verify the CDN host separately).
- **`polite_fetch.py --batch`** splits on `[\t,]` and keeps quotes → batch files must be headerless +
  unquoted (bit the ordinances agent once).

## Source index
`logan_city_council/sources.csv` regenerated: **2,173 documents indexed, 99% with recorded URLs**
(up from 345). Repo-root `sources_summary.md` refreshed.
