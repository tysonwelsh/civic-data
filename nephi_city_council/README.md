# Nephi City Council — data repository

A Salt Lake City-style civic-data repository for the **Nephi City Council** (Juab County, Utah) —
a small rural county seat (~6,500 residents) — built 2026-06 by the `build-city-data-repo` skill.
Council minutes, extracted motions, election results, and an in-city-limits geo tool — all as
markdown/CSV, covering **2020–present**. See `CLAUDE.md` for analysis guidance; independent QA in
`VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 243 meetings (markdown) | CivicPlus AgendaCenter (`nephi.utah.gov`) + 1 Utah PMN recovery, born-digital | ✅ complete, no OCR (226 PDF + 17 .docx) |
| Recorded motions | 2020–2026 | 918 motions · 1,090 rows · 22 contested | extracted from minutes | ✅ verified |
| Planning Commission | 2020–2026 | 70 meetings · 331 motions · 13 commissioners | CivicPlus, same pipeline | ✅ recommendation-vs-final-action |
| Relational database | 2020–2026 | 3 bodies · 1,249 motions · 18 referrals | derived (`db/build_*.py`) | ✅ canonical — see `db/SCHEMA.md` |
| Public comments (genuine written) | — | **0 published** | n/a | ⚠️ in-minutes-only (see below) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 116 in-person speakers | clerk paraphrases | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 7 races · 26 candidates · 80 precinct rows | Juab County / Enhanced Voting | ✅ verified (2019/21 unofficial — see gaps) |
| Geo (in-city-limits) | current | city polygon + 5 precincts | UGRC (CountyID 12) | ✅ at-large — no districts |
| Weekly bundles | 2020–2026 | 241 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Mayor + 5 all-at-large councilmembers (0 districts).** The **Mayor does NOT vote** except to break
a tie. 4-year staggered terms (Mayor + 2 seats in 2021/2025; 3 seats in 2019/2023). Council meets
**1st & 3rd Tuesdays, 7 PM**. Current mayor: Justin Seely.

## Votes are narrative, not a roll-call grid (read this)
Nephi's minutes record motions as prose ("Councilor X moved… Councilor Y seconded… the motion
passed unanimously") with **no per-member Aye/Nay grid** on routine business. So every motion
captures mover + seconder + result, but **only 46 of 918 motions name individual voters**; the rest
are tally-only (`names_recorded:false` — we never guess who voted). Named dissents are captured when
the clerk states them. **97.6% of motions pass with no recorded dissent — the highest consensus rate
of any city in this collection** (interpret "unanimous" as "no dissent recorded," not a verified
member tally). `body=CRA` tags the one Community Reinvestment Agency meeting (2021-07-27); Nephi has
no separate RDA.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/`** — the appointed technical land-use body, same minutes/vote pipeline as
  council. `planning_commission/all_votes.csv` (identical 13-col schema, `body=PlanningCommission`):
  **331 motions across 70 recovered meetings (63 with a motion)**, a **13-commissioner roster**
  (`planning_commission/roster.csv`, from attendee headers — appointed, no election). The `result`
  string encodes the **recommendation-vs-final-action taxonomy**: forwarded recommendations to Council
  (**93 Positive / 2 Negative**) vs final actions (CUP/site-plan/concept — **236**, never reach
  Council). Same **narrative-vote caveat** as council — only 12 of 331 PC motions name individual
  voters; the rest are tally-only. See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** — the **NORMALIZED RELATIONAL DATABASE** (SQLite + `db/tables/` CSV exports) that
  joins **all three bodies' votes by real keys** (Council ↔ PlanningCommission ↔ CRA) plus a
  reconstructed **PC→Council referral** layer. **Prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). **Start with `db/SCHEMA.md`.** Two layers, never conflated:
  the *within-body core is EXACT* (project keys resolved from prose, **body-scoped → 0 apps span >1
  body**), and the *cross-body `referral` is RECONSTRUCTED + SCORED* — **18 links, all medium/subject,
  all Council←PlanningCommission** (9% of council land-use apps; small city → few links is honest;
  CRA carries none). `high`≈exact, `medium` spot-check before quoting. Build (idempotent):
  ```
  python3 db/build_db.py          # 1. exact within-body core
  python3 db/build_referrals.py   # 2. reconstructed cross-body referral layer (run AFTER)
  ```

## Public comments — in-minutes-only (honest finding)
Nephi publishes **no written-comment dataset** — no comment/correspondence page, no eComment portal,
and agenda packets carry no correspondence attachments. Public comment is in-person only and survives
as clerk paraphrase in the minutes; most meetings record "NO PUBLIC COMMENT." So
`all_comments_clean.csv` is intentionally empty; the 116 in-person speakers live in
`minutes_speaker_log.csv` (NOT comments). Full audit: `public_comments/AVAILABILITY.md`.

## Elections (Juab County, at-large)
7 races for 2019/2021/2023/2025 (no mayor race in 2019/2023). At-large, **no RCV**. Winners: 2019
Council = Seely, Ostler, Memmott; 2021 Mayor = Seely, Council = Skip F. Worwood, Callaway; 2023
Council = Travis L. Worwood, Cowan, Parady; 2025 Mayor = Seely (unopposed), Council = Douglas,
Callaway. **Honest gap:** Juab's results portal only goes back to **2023** — 2019 & 2021 totals come
from news archives (Deseret News / Mid-Utah Radio) and are flagged **unofficial** (winners/seat-counts
solid; exact totals carry the caveat); no per-precinct data for those two years.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Weekly bundles: `python3 build_weeks.py`
  (`CITY="Nephi"`, `MEETING_WEEKDAY=Tuesday`). Canonical truth = the dataset CSVs (+ each file's
  `source_url`); raw PDFs not retained (regenerable from `minutes_index.csv`) — EXCEPT the recovered
  2021-02-23 PMN work-session .docx, kept in `meeting_minutes/raw/2021/` because the city's own
  AgendaCenter link for that date serves the wrong document (see `VERIFICATION.md` 2026-07-02
  addendum); `weeks/` is derived.

## Expansion datasets (additive, 2026-07-05)
Six additional source layers (CivicPlus AgendaCenter + Utah Public Notice + YouTube), each
documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 328 meeting agendas (Council/PC/CRA), all stored locally (the city is small).
- **`housing_plans/`** — the 2023 General Plan with its housing element (Nephi is exempt from the
  state's annual moderate-income-housing reporting, so it has no state filings — a verified gap).
- **`ordinances/`** — 103 adopted ordinances (71 land-use); Nephi numbers ordinances by adoption date.
- **`pmn_backfill/`** — 9 meetings recovered from Utah Public Notice (late-2025/early-2026 gaps).
- **`transcripts/`** — 4 ASR caption tracks from the new city YouTube channel (streaming began May 2026;
  no earlier video exists). Not an official record.
- **`campaign_finance/`** — 27 candidate disclosure filings (2019–2025), handwritten scans self-hosted
  by the city, joined 92% to election results.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
