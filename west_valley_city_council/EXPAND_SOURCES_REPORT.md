# expand-city-sources — West Valley City expansion report

**Date:** 2026-07-06 · **City:** West Valley City (Salt Lake County) · **Skill:** `.claude/skills/expand-city-sources/`
**Thirteenth and final city.** Portal: **Hyland OnBase "Agenda Online"** (`ob.wvc-ut.gov`) + a **CivicPlus
Archive Center** (ordinances + campaign finance) + PMN + YouTube. A **case-number city** (`Z-`/`PUD-`/`GPZ-`)
with **separate RDA + MBA** bodies. All six datasets built; every one passes `validate_dataset.py`; no
existing dataset modified. Concurrency pre-flight clean.

## Per-source results (all PASS)

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**STORED**) | **965 agendas** (Council 521, PC 287, RDA 59, MBA 34, BoA 31, HousingAuth 27, StrategicPlanning 6), 126 MB | OnBase serves **thin born-digital agendas** (4–10 pp, ~56–199 KB), NOT bundled staff-report packets → stored all. **`documentType=3` (staff-report bundle) returns "unavailable"** — the agenda is the ceiling. **100% vote-date join** (Council/PC/RDA/MBA). Needs cookie-prime + browser UA (else 403); `DownloadFile`→`DownloadFileBytes` rewrite (like Provo OnBase) |
| 2 | Housing → `housing_plans/` | **7 docs (~26 MB)** | MIH = **standalone 2025 Moderate Income Housing Plan** (filed as a GP appendix); GP is web-chapter-delivered (no consolidated PDF); state 23/24/25 + SB 34. Careful West Valley / West Jordan / West Point / White City disambiguation (0 bleed) |
| 3 | Ordinances → `ordinances/` | **324 adopted** (**254 land-use, 78%** — highest share in the repo) | Minutes cite `YY-NN` numbers richly → **95 high** (CivicPlus **Archive Center** signed ordinance PDFs, 2024–26 modules) / 221 within_source / 8 none. **160 rows carry a land-use case number** (GPZ 94 / Z 53 / SMI 7 / PUD 6) feeding the referral layer. 8 ords missing from votes (motions often cite the *application* number, not the ordinance number) |
| 4 | PMN backfill → `pmn_backfill/` | **11 recovered** (8 Council + 2 RDA + 1 MBA; 3.6 MB) | Entity 307; Council 398 / RDA 399 / MBA 401 / PC 402 (no combined body). Off-cycle budget-retreat/strategic-planning work sessions OnBase never captured. **PC = honest zero** (PMN carries only PC agendas; the repo's 263 OnBase PC minutes are the superset) |
| 5 | Transcripts → `transcripts/` | **1,133 videos mapped / 10 ASR sampled** | WVCTV YouTube (`/streams` livestreams 2020+ and `/videos` pre-2020 meetings — fully disjoint tabs, both enumerated). 461 in-window council meetings, 96% minutes-matched. Whisper candidate: Res 25-156 (failed 3-3 Oct 2025 → reversed 4-3 Nov) |
| 6 | Campaign finance → `campaign_finance/` | **105 filings** (2019/21/23/25; 94 MB) | Self-hosted on the CivicPlus **Archive Center** (`Archive.aspx?AMID=…`→`ADID=…`; the AMID→year labels were REVERSED — assigned by roster). 73% filing join / 96% of modern general candidates filed. **2023 D3 winner Will Whetstone filed NO statement** (GRAMA-only gap). 2019 primaries referenced but never captured |

**Existing layer untouched:** `all_votes.csv` (case-number city; separate RDA + MBA bodies, populated), 550 council + 263 PC minutes, no published comments, `db/civic.db` unchanged.
**New footprint on disk:** ~344 MB raw (packets 126 + campaign-finance 94 + housing 26 + pmn/ordinances small; all stored — OnBase agendas + Archive Center PDFs are modest).

## Timing
Six agents in parallel; end-to-end ≈ slowest (campaign finance ~36 min — 63 scanned filings OCR'd). No packet-agent stall (inline probe found thin agendas → stored directly).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **2023 District 3 winner Will Whetstone filed no campaign-finance statement** anywhere — a genuine disclosure gap.
2. **8 adopted ordinances missing from `all_votes.csv`** (25-02/25-04/26-01/26-02/26-22/26-23/26-24/26-25) — the
   case-number quirk (motions cite the application `Z-`/`GPZ-` number, not the ordinance number).
3. **Off-cycle work sessions** (budget retreats, strategic planning) recovered via PMN that OnBase never carried.

## Skill changes worth folding in
- **OnBase "Agenda Online" is tenant-variable:** this tenant serves *thin agendas* (store-all), unlike Provo's
  GB-scale bundles — probe before assuming index-only. Search is a plain GET (`dropid&mtids&dropsv/dropev`),
  simpler than Provo's POST; `DownloadFile`→`DownloadFileBytes` for the real PDF; cookie-prime to beat 403.
- **CivicPlus Archive Center** (`Archive.aspx?AMID→ADID→ViewFile/Item`) is a reusable host family for both
  ordinances and campaign finance — and its year *labels can be reversed* vs the AMID; assign year by content.
- **Wayback "referenced but not captured"** — a linking page is archived while the linked PDF has 0 CDX
  captures; check the doc-ID CDX before declaring recoverable.

## Source index
`west_valley_city_council/sources.csv` regenerated: **2,690 documents indexed, 100% with recorded URLs**
(up from 817). Repo-root `sources_summary.md` refreshed.
