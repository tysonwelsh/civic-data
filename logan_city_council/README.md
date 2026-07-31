# Logan City Council — data repository

A Salt Lake City-style civic-data repository for the **Logan Municipal Council** (Cache County,
Utah) — the largest city in northern Utah (~52k, USU college town) — built 2026-06 by the
`build-city-data-repo` skill. Council + RDA minutes, extracted roll-call votes, election results,
and an in-city-limits geo tool — all as markdown/CSV, covering **2020–present**. See `CLAUDE.md`
for analysis guidance; independent QA in `VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 198 meetings (149 Council + 49 RDA) | Revize CMS (`loganutah.gov`), born-digital | ✅ complete, no OCR |
| Roll-call votes | 2020–2026 | 789 motions · 2,820 rows · 28 contested | extracted from minutes | ✅ verified |
| — by body | | Council 754 motions / 2,714 rows · **RDA 35 / 106** | separate RDA recess meetings | ✅ `body` column |
| Planning Commission | 2020–2026 | 130 meetings · 549 motions · 15 commissioners | Revize CMS, **52 of 130 OCR** | ✅ `planning_commission/` |
| Relational database | 2020–2026 | 3 bodies · 1,341 motions · 5,187 votes (SQLite) | derived (`db/build_db.py`) | ✅ canonical — start at `db/SCHEMA.md` |
| Public comments (genuine written) | — | **0 published** | n/a | ⚠️ in-minutes-only (see below) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 633 in-person speakers | clerk paraphrases | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 11 races · 55 candidates · 1,596 precinct rows | Cache County / city / Enhanced Voting | ✅ verified (winners confirmed) |
| Geo (in-city-limits) | current | city polygon + 25 precincts | UGRC (CountyID 3) | ✅ at-large — no districts |
| Weekly bundles | 2020–2026 | 149 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Mayor + 5 all-at-large councilmembers (0 districts).** The separately-elected **Mayor does NOT
vote** (holds a veto). Council meets **1st & 3rd Tuesdays, 5:30 PM**. **Two distinct Andersons** in
the record: **Amy Z. Anderson** (council 2021) and **Mark A. Anderson** (council 2019/2023, then
**Mayor from Jan 2026** — so he votes 2019–2025 but not 2026+). The extractor keys members on
initial+surname to keep them separate.

## RDA (separate meetings — "follow the money")
Logan's council adjourns into the **Logan Redevelopment Agency** the same night; the RDA has its own
roll-call votes inside the same minutes PDF. Those segments are split into `redevelopment-agency-meeting`
files and tagged **`body=RDA`** (35 motions / 106 rows across 49 RDA sessions) — TIF / project-area /
developer-subsidy votes. Filter `body=Council` for council-only analysis.

## Public comments — in-minutes-only (honest finding)
Logan publishes **no written-comment dataset** — no comment/correspondence page, no eComment portal
(custom Revize CMS), no packet correspondence attachments; GRAMA is records-access only. Public
comment is in-person (name + city, 3-min) and survives as clerk paraphrase in the minutes. So
`all_comments_clean.csv` is empty; the 633 in-person speakers live in `minutes_speaker_log.csv`
(NOT comments). Full audit: `public_comments/AVAILABILITY.md`.

## Elections (Cache County, at-large)
11 races for 2019/2021/2023/2025. At-large, **no RCV** (neighbor RCV cities filtered out). Winners:
2019 Council = Mark A. Anderson, Jeannie Simmonds, Tom Jensen; 2021 Mayor = Holly Daines, Council =
Ernesto Lopez, Amy Z. Anderson; 2023 Council = Mark A. Anderson, Mike Johnson, Jeannie Simmonds;
2025 Mayor = Mark A. Anderson, Council = Ernesto Lopez, Katie Lee-Koven. **Notes:** Logan
*self-administered* its 2019 & 2021 elections (county took over 2023); the **2023 election ran under
a Cache County integrity investigation + recount** — certified canvass figures used (recount did not
change winners). See `election_results/CLAUDE.md`.

## Planning Commission + relational database
The **Logan Planning Commission** — the appointed technical land-use body (15 commissioners,
no election) — is captured in `planning_commission/` on the same vote schema as council:
**130 meetings · 549 motions · 15 commissioners**, with `body=PlanningCommission`. The `result`
string encodes the **recommendation-vs-final-action** taxonomy: **112 recommendations** (86 Positive /
26 Negative — forwarded to the Municipal Council) vs **437 final actions** (design review / conditional
use / subdivision — never reach Council). **52 of the 130 PC minutes are scanned OCR**, so a fraction
of PC parsing is noisier than the born-digital council set.

`db/civic.db` (SQLite) is the **canonical, queryable** form joining **Council ↔ Planning Commission ↔
RDA** votes by real keys (the flat CSVs have none). **Start at `db/SCHEMA.md`.** Built in two stages:
```
python3 db/build_db.py          # 1. EXACT within-body core (body/person/meeting/application/motion/vote/role)
python3 db/build_referrals.py   # 2. reconstructed, scored, generalized cross-body referral layer (run AFTER)
```
Two layers, never conflated: the within-body core is exact (project keys **resolved from prose**,
**body-scoped** — 0 applications span >1 body); the `referral` table is RECONSTRUCTED + GENERALIZED
(Council←PC, Council←RDA, PC←RDA, with `primary_application_id`/`primary_body`/`related_application_id`/
`related_body`). **Logan's referral layer is honestly empty (0 substantiated links):** council/RDA
motion text is bare ("adopt Ordinance NN-NN as presented"), so the only candidate links were
boilerplate-only false positives (all suppressed in `db/referral_overrides.csv`); addresses are grid
intersections (co-location only). See `db/SCHEMA.md` → Known limitations.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Weekly bundles: `python3 build_weeks.py`
  (`CITY="Logan"`, `MEETING_WEEKDAY=Tuesday`). Canonical truth = the dataset CSVs (+ each file's
  Revize `source_url`); raw PDFs not retained; `weeks/` is derived.

## Expansion datasets (additive, 2026-07-05)
Six additional source layers (Revize CMS + Utah Public Notice + YouTube), each documented in
its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 1,124 agenda + staff-report documents catalogued with live URLs (index-only),
  incl. 867 individual staff reports — the analysis behind each agenda item. doc_class + fetch→extract→discard
  (2026-07-16): 213 classified (207 staff_report / 6 plan_amendment), 48 ok / 165 needs_ocr (vision pass queued).
- **`housing_plans/`** — the Logan 2045 General Plan, the 2022 Moderate-Income-Housing Plan, and
  state housing compilations.
- **`ordinances/`** — 496 adopted ordinances & resolutions (143 land-use), 461 matched to the
  council vote that passed them via the City Recorder's signed-PDF archive.
- **`pmn_backfill/`** — an honest zero: the minutes layer already covers everything on Utah
  Public Notice.
- **`transcripts/`** — 10 sampled ASR caption tracks + a full 155-video map (YouTube). Not an
  official record.
- **`campaign_finance/`** — 45 candidate disclosure filings (2021 partial / 2025 complete),
  joined 100% to election results.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
