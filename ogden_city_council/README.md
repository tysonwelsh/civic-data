# Ogden City Council — data repository

A Salt Lake City-style civic-data repository for the **Ogden City Council** (Weber County,
Utah), built 2026-06 by the `build-city-data-repo` skill. Council minutes, extracted roll-call
votes (incl. RDA & MBA), public-comment availability, municipal election results, and an
address→district tool — all as markdown/CSV, covering **2020–present**. See `CLAUDE.md` for
analysis guidance; independent QA in `VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 504 meetings (markdown) | Ogden city minutes (text PDFs; 2022 is a scan, re-OCR'd 2026-07-02) | ✅ complete |
| Roll-call votes | 2020–2026 | 1,506 motions · 4,992 rows · 87 contested | extracted from minutes | ✅ verified |
| — by body | | Council 1,377 · **RDA 111** · **MBA 18** | separate RDA/MBA meetings | ✅ `body` column |
| Planning Commission | 2020–2026 | **138 meetings · 988 motions · 19 commissioners** | PC minutes (51 OCR'd; 2020-23 gap closed 2026-07-19) | ✅ verified |
| Relational database | 2020–2026 | `db/civic.db` — 4 bodies, 259 apps, 1,923 motions, 1 referral | derived (joins all bodies) | ✅ `db/SCHEMA.md` |
| Public comments (genuine written) | — | **0 published** | n/a — submit-only city | ⚠️ verdict SUBMIT-ONLY (see below) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 635 in-person speakers | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 16 races · 28 candidates · 411 precinct rows | Weber County | ✅ verified |
| Geo (address→district) | current map | precincts → Districts 1–4 | UGRC + city council districts | ✅ tested |
| Weekly bundles | 2020–2026 | 255 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Council–Mayor (strong-mayor) form. 4 District + 3 At-Large = 7 council members.** The
**Mayor does NOT vote** (executive branch): Caldwell (Mayor 2020–2023) and Nadolski (Mayor from
2024-01-02) are excluded as voters **for the years they hold the mayoralty** — but Nadolski
voted as council chair 2020–2023, so he is correctly a voter then. Geo maps addresses to
Districts 1–4; at-large + mayor are city-wide.

## RDA & MBA included (the "follow the money" subset)
Unlike most cities here, Ogden holds its **Redevelopment Agency (RDA)** and **Municipal
Building Authority (MBA)** as **separate meetings with their own minutes** (slugs
`redevelopment-agency` / `municipal-building-authority`). The same 7 members sit as the board.
`all_votes.csv` tags these `body=RDA` (111 motions) / `body=MBA` (18) vs `body=Council` (1,377).
Filter `body=RDA` for TIF / project-area / developer-subsidy votes. NB the 2021 RDA motions
come from in-meeting "acting as the Redevelopment Agency" transitions; 2022–2023 have **0** RDA/MBA
motions because those years' separate RDA/MBA meeting minutes were not acquired (see Known gaps).

## Planning Commission + relational database
Two additions extend the Council vote data into **cross-body land-use analysis**:

- **`planning_commission/`** — the appointed technical land-use body that **recommends** rezones /
  zoning & general-plan amendments / subdivisions / annexations / street vacations to the Council and
  takes **final action** on its own delegated approvals (conditional-use permits, design review, site
  plans). **138 meetings · 988 motions · 19 commissioners** (2020–2026), identical 13-column
  `all_votes.csv` schema (`body=PlanningCommission`); `result` encodes the
  **recommendation-vs-final-action** taxonomy. Caveats: **51 of 138 minutes are OCR'd**, and
  the old "2020–2023 PC coverage is sparse" gap was **CLOSED 2026-07-19** — 63 meetings recovered
  from standalone DocumentCenter draft-minutes documents (+2 packet carves), each verified against
  the following meeting's approval item. See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** — a normalized SQLite database (the **canonical, queryable** form: PKs/FKs, typed
  columns, provenance) joining **Council ↔ Planning Commission ↔ RDA ↔ MBA** votes by real keys, plus
  a **reconstructed, scored cross-body `referral`** layer (generalized — includes Council←RDA where
  present). **Start with `db/SCHEMA.md`.** Two layers, never conflated: the within-body core is *exact*
  (project keys resolved from prose, **body-scoped — 0 apps span >1 body**); the `referral` layer is
  *reconstructed inference* (`high`≈exact, `low` flagged). Because Ogden's Council motions are terse
  ordinance-adoption roll-calls that omit the subject, only ~20 Council land-use applications resolve
  and just **1 referral link** survives (precision over recall — see SCHEMA). Build:
  ```
  python3 db/build_db.py          # 1. exact within-body core
  python3 db/build_referrals.py   # 2. reconstructed cross-body referral layer (run AFTER)
  ```

## Public comments — SUBMIT-ONLY (honest gap)
Ogden publishes **no archive of genuine written/online public comments** (verdict
SUBMIT-ONLY / NOT PUBLISHED): comments are forwarded to the Council and entered into the record
but the submitted text is not published anywhere public. So `all_comments_clean.csv` is
intentionally **empty**. In-person speaker paraphrases (635) live in `minutes_speaker_log.csv`
and are **not** public-submitted comments. Full audit: `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **Votes are recorded roll-calls only.** Ogden names individual votes mainly for substantive
  items (many pass on a tally / "ALL VOTING AYE" with no per-member names → `names_recorded:false`).
  **87 motions draw a Nay/Abstain/Recuse** (genuine named dissents — see
  `votes/_validation_report.txt`). The contested *rate* is "among recorded roll-calls," not
  directly comparable to councils that roll-call every motion.
- **2022–2023 RDA/MBA undercounted.** The separate RDA and MBA meeting sets for 2022 and 2023
  were not acquired (Ogden Document Center ids **29548** = 2023 RDA, **29549** = 2023 MBA; a
  2022 RDA/MBA set is referenced in the 2022 council minutes — "Special Redevelopment Agency
  meetings scheduled to begin at 6:00 p.m." — but was likewise never harvested). Estimated
  ~20–25 RDA + ~5–8 MBA meetings missing per year. The 111/18 RDA/MBA counts therefore cover
  2021 (in-meeting transitions) and 2024–26 only. Tracked as the separate-RDA follow-up.
  See `meeting_minutes/CLAUDE.md`.
- **2022 minutes are OCR'd** (the yearly compilation PDF is a scan). Repaired 2026-07-02:
  the scan was re-OCR'd with tesseract at 300 dpi and re-carved into 73 per-meeting files
  covering all 38 meeting dates in the compilation — the earlier extraction had used the
  scan's garbled embedded OCR layer and mis-carved the meeting boundaries (8+ meeting dates
  missing, 47% of 2022 named roll calls undercaptured, ~33 Council motions mis-tagged RDA).
  An earlier version of this README claimed 2023 was the OCR'd year and that Council coverage
  was complete — both wrong; 2023 was re-OCR'd cleanly at build time and was always fine.
  Two clerk typos in the 2022 source are preserved verbatim in the text (the 2022-03-01
  regular meeting opening says "March 1, 2021"; the 2022-06-07 work-session opening says
  "June 2, 2022"; both meetings are dated per their running headers + stated weekday).
- Elections: Weber County-administered; only Ogden council + mayor races included.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Validation:
  `python3 meeting_minutes/validate_votes.py` · Weekly bundles: `python3 build_weeks.py`
  (`CITY="Ogden"`, `MEETING_WEEKDAY=Tuesday`). Canonical truth = the dataset CSVs (+ each file's
  `source_url`); `weeks/` is derived.

## Expansion datasets (additive, 2026-07-06)
Six additional source layers (CivicPlus DocumentCenter/AgendaCenter + Utah Public Notice + YouTube),
each documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 166 meeting agendas (mostly Planning Commission, whose agendas cover 71 meetings
  the repo has no minutes for); Ogden posts no bundled staff-report packets.
- **`housing_plans/`** — the General Plan with its housing element (Chapter 7) and the state
  moderate-income-housing compilations.
- **`ordinances/`** — 308 adopted ordinances (107 land-use), most matched to the adopting motion, some
  corroborated by the Recorder's signed ordinance-synopsis affidavits.
- **`pmn_backfill/`** — 10 meetings recovered from Utah Public Notice, including 7 of the previously
  never-acquired 2023 Redevelopment Agency minutes.
- **`transcripts/`** — a 683-video map of meeting recordings + 10 sampled ASR caption tracks (YouTube).
  Not an official record.
- **`campaign_finance/`** — 38 candidate disclosure filings (2019/2021/2023), self-hosted by the city,
  joined 100% to election results (2025 not yet published).

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
