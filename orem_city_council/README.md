# Orem City Council — data repository

A Salt Lake City-style civic-data repository for the **Orem City Council** (Utah County),
built 2026-06 by the `build-city-data-repo` skill. Council minutes, extracted roll-call
votes, genuine public comments, municipal election results, and an in-city-limits geo tool —
all as markdown/CSV, covering **2020–present**. See `CLAUDE.md` for analysis guidance; QA in
`VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 130 meetings (markdown) | Google Drive archive + CivicClerk (68 OCR'd) | ✅ Apr–Jun 2021 absent (predates sources) |
| Roll-call votes | 2020–2026 | 566 motions · 3,749 rows · 49 contested | extracted from minutes | ✅ verified (mayor votes; OCR defects repaired) |
| Public comments (genuine written) | 2020–2021 | **95** residents' submissions | published as attachments to electronic-meeting minutes | ✅ (2020–21 only; see caveat) |
| Minutes speaker log (NOT public comments) | 2021–2024 | 122 in-person speakers | clerk paraphrases in minutes | ℹ️ undercounts 2022–26 (built pre-OCR-repair) |
| Election results | 2019, 2021, 2023, 2025 | 11 races · 75 candidates · 2,063 precinct rows | Utah County (`vote.utahcounty.gov`) | ✅ verified (winners cross-checked) |
| Geo (in-city-limits) | current | city polygon + 57 precincts | UGRC (NAME=OREM / CountyID 25) | ✅ at-large — no districts |
| Planning Commission | 2020–2026 | 114 meetings · 562 motions · 25 commissioners | CivicClerk + Drive (6 OCR'd) | ✅ recommendations vs final actions |
| Relational database | 2020–2026 | `db/civic.db`: 5 bodies · 1,067 motions · 6,746 votes · 29 cross-body referrals | derived (`db/build_*.py`) | ✅ INTEGRITY OK; idempotent |
| Weekly bundles | 2020–2026 | 128 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Mayor + 6 council members, ALL AT-LARGE (no districts)**, nonpartisan, staggered 4-yr terms
(3 council seats up each odd year). The **Mayor is a full voting member** (7-member rosters).
Because there are no districts, the geo tool resolves an address to in/out of city limits.

## Known gaps / caveats
- **68 of 130 minutes were image-only scans recovered via OCR** (slightly lower fidelity,
  flagged `format=ocr`). **Apr–Jun 2021** meetings are genuinely absent (predate both the
  Google Drive archive and CivicClerk's launch).
- **Genuine written comments are 2020–2021 only** — verbatim resident comments that Orem
  published as attachments to its COVID-era electronic-meeting minutes. From 2022 on, the
  city's CivicClerk eComment feature is disabled and packets carry no correspondence, so no
  published written-comment archive exists (verdict in `public_comments/AVAILABILITY.md`).
- The **in-person speaker log undercounts 2022–2026** — it was built before the 68 empty
  minutes were OCR-repaired; regenerate over the full minutes for complete coverage.
- Elections: 2019 & 2023 are citywide-only (no precinct SOVC published); at-large vote-for-3.

## Planning Commission + relational database
- **`planning_commission/`** — the appointed technical land-use body, identical vote schema to the
  Council (every row `body=PlanningCommission`). **114 meetings · 562 motions · 25 commissioners**
  (`planning_commission/roster.csv`; appointed, not elected). The `result` string encodes the
  **recommendation-vs-final-action taxonomy**: `Positive/Negative recommendation A:N` (forwarded to the
  City Council) vs `A:N Approved/Denied (Final Action)` (CUP/site-plan/plat the PC disposes itself —
  never reaches Council). 6 of the 114 minutes were OCR'd. The city never published real minutes for
  the 2025-10-15 PC meeting (its CivicClerk "Approved Minutes" is a mis-upload of the 2025-11-05
  document — see `planning_commission/minutes_unrecovered.csv`). See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** — the **canonical, queryable** form: a normalized relational DB joining all five
  bodies' votes (Council / PlanningCommission / RDA / MBA / SSLD) by real keys, plus a **generalized,
  reconstructed cross-body referral layer** (PC→Council here). **Prefer it for any cross-body or
  project-level question** — the flat CSVs have no keys. Start with **`db/SCHEMA.md`**.
  ```
  python3 db/build_db.py          # within-body EXACT core (idempotent)
  python3 db/build_referrals.py   # cross-body scored referral layer (run AFTER)
  ```
  Two layers, never conflated: the within-body project key is **resolved from prose** and body-scoped
  (0 applications span >1 body); the cross-body `referral` table is **reconstructed + scored + auditable**
  (29 links: 10 high / 17 medium / 2 low, all Council←PlanningCommission). `db/tables/` are CSV exports.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · PC votes:
  `python3 planning_commission/extract_votes.py` · Elections:
  `python3 election_results/clean_elections.py` · Weekly bundles: `python3 build_weeks.py` · Database:
  `python3 db/build_db.py && python3 db/build_referrals.py`.
  Raw minutes PDFs are not retained (regenerable from `minutes_index.csv`); `weeks/` and `db/` are derived.

## Expansion datasets (additive, 2026-07-05)
Six additional source layers (CivicClerk API + Google Drive archive + Utah Public Notice),
each documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 221 agenda PDFs + 204 full agenda-packets catalogued with live URLs
  (index-only, ~5.8 GB on the portal). The staff analysis behind each agenda item.
- **`housing_plans/`** — General Plan (2023) with its Moderate-Income-Housing element
  (Chapter 4), the 2018 housing study, FrontRunner station-area plan, and state compilations.
- **`ordinances/`** — 95 adopted ordinances (47 land-use); Orem's minutes don't print
  ordinance numbers, so the index is reconstructed from the adopting motions.
- **`pmn_backfill/`** — 39 meetings recovered from Utah Public Notice, incl. the Apr–Jun
  2021 Council gap and new Redevelopment Agency + Municipal Building Authority minutes.
- **`transcripts/`** — 10 sampled ASR caption tracks + a full 111-video map (YouTube).
  Not an official record.
- **`campaign_finance/`** — 91 candidate disclosure filings (2021 annuals / 2023 / 2025),
  self-hosted by the city, joined 100% to election results.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
