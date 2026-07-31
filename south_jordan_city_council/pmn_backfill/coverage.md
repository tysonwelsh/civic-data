# PMN backfill — coverage

**Source:** Utah Public Notice (utah.gov/pmn), cumulative notice history per body via the
`notices.html?id=<body>&page=300` GET (returns a body's *entire* history in one page, unlike
the 6-month list view the base build used).
**As of:** 2026-07-06. **Cross-check tolerance:** ±4 days (meeting date vs posted/filename date).
**Repo data floor:** 2020 (per `south_jordan_city_council/CLAUDE.md`). This backfill targets
the 2020+ window; pre-2020 PMN holdings are catalogued below as an out-of-scope note, not recovered.

## PMN bodies discovered (entity id 269 → publicBodies)

| body | PMN id | role here |
|---|---|---|
| City Council | **1031** | primary — 515 Meeting-Minutes attachments (2014–2026) |
| Planning Commission | **1032** | 154 Meeting-Minutes attachments (2015–2025) |
| Redevelopment Agency | **3901** | 37 attachments — all 2020+ are *Combined CC & RDA* meetings (fold into Council) |
| Municipal Building Authority | **5015** | 5 attachments — all *Combined CC & MBA* (fold into Council); none 2020+ standalone |
| Board of Adjustments | 1033 | not crawled (out of scope — no BoA dataset in repo) |

(Full body list saved to `_disco/bodies.html`; all minutes attachments parsed to
`_disco/pmn_minutes_all.csv`.)

## Council — per-year coverage (in-scope window, 2020+)

| year | repo dates | PMN minutes dates | recovered here | still-missing |
|---|---|---|---|---|
| 2020 | 8 | 15 | **7** | 0 (Mar–Jun 2020: no minutes on any portal — see below) |
| 2021 | 26 | 26 | 0 | 0 |
| 2022 | 26 | 26 | 0 | 0 |
| 2023 | 23 | 25 | **1** | 0 |
| 2024 | 21 | 20 | 0 | 0 |
| 2025 | 20 | 20 | 0 | 0 |
| 2026 | 11 | 11 | 0 | 0 |

**8 council meeting dates / 13 documents recovered** (study + regular + budget/emergency
counted separately):

| date | docs recovered | note |
|---|---|---|
| 2020-01-07 | regular + study | |
| 2020-01-21 | combined CC&RDA + study | RDA body (3901) posted its own copy of the combined regular; same meeting |
| 2020-01-29 | budget #1 | |
| 2020-02-04 | regular + study | |
| 2020-02-18 | regular + study | 46 MB study PDF (embedded exhibits); text layer present |
| 2020-07-24 | emergency (closed-session) | |
| 2020-08-04 | regular + study | previously logged unrecoverable — see reconciliation |
| 2023-01-24 | budget | between existing 01-17 and 01-31 regular meetings |

## Planning Commission — per-year coverage (2020+)

| year | repo dates | PMN minutes dates | recovered here | still-missing |
|---|---|---|---|---|
| 2020 | 19 | 19 | 0 | 0 |
| 2021 | 21 | 20 | 0 | 0 |
| 2022 | 19 | 13 | 0 | 0 |
| 2023 | 18 | 2 | 0 | 0* |
| 2024 | 18 | 6 | 0 | 0* |
| 2025 | 20 | 1 | 0 | 0 |
| 2026 | 7 | 0 | 0 | 0 |

`*` Two PMN "PC-body" minutes fell outside PC repo dates but are **not** PC-only gaps —
both are combined meetings whose minutes are **already on disk under `meeting_minutes/`**:
- **2023-03-07** — "CC & Planning Commission Study Meeting" (in council index as
  `03-07-2023 City Council & Planning Commission Study Meeting Minutes`).
- **2024-09-17** — "Combined City Council & Planning Commission Meeting" (council index has
  the 2024-09-17 regular + study docs).

Not re-fetched (would duplicate content already retained). No genuine PC minutes gap 2020+.

## RDA / MBA (bodies 3901 / 5015)

Every 2020+ RDA and MBA minutes attachment is a **Combined City Council & RDA (or MBA)**
meeting — South Jordan holds these jointly and the minutes are the council minutes. These
dates already resolve to council dates in the repo (or were recovered here, e.g. 2020-01-21).
**No standalone RDA/MBA meeting 2020+ is missing from the repo.** Pre-2020 standalone RDA
meetings exist on PMN but are below the data floor (see next section).

## Out of scope — pre-2020 PMN holdings (NOT recovered)

PMN retains far more than the repo's 2020 floor. Catalogued for a future floor-extension
decision (all live, re-fetchable; ids in `_disco/pmn_minutes_all.csv`):

- **Council (1031):** ~158 meeting dates 2014–2019 (2014:14, 2015:24, 2016:48, 2017:28,
  2018:21, 2019:23).
- **Planning Commission (1032):** ~88 meeting dates 2015–2019.
- **RDA (3901) / MBA (5015):** scattered combined + standalone meetings 2016–2019.

These are a real, retrievable extension of the archive back to 2014 — not a defect. Left
untouched because extending the floor is a deliberate scope decision for the user, not a gap-fill.

## Reconciliation flag — existing minutes layer NOT modified (per instructions)

This backfill **contradicts two rows** in `meeting_minutes/minutes_unrecovered.csv`, which the
base build wrote off the PMN 6-month list view. The cumulative-page crawl found the minutes:

1. Row `2020-01-01/2020-07-31 … Council` ("No portal retains pre-Aug-2020 SJ council minutes …
   Utah PMN retains SJ City Council notices only from 2020-08-04 onward"): **partially
   superseded.** Recovered: 2020-01-07, 01-21, 01-29, 02-04, 02-18, 07-24. **Still genuinely
   unrecovered: March–June 2020** — those meetings WERE noticed and held as electronic
   meetings (PMN notices exist for 03-03, 04-07, 04-21, 05-05, 05-19, 06-02, 06-16, plus a
   canceled 03-17 / 07-07), but **only agendas/"Public Information Handout" were attached —
   no minutes PDF was ever posted** to PMN, and CivicPlus/Municode don't reach back that far.
   Meeting exists, minutes don't = honest gap.
2. Row `2020-08-04 … only agenda+packet attached; minutes PDF was never posted`: **fully
   superseded** — the 08-04-2020 regular + study minutes ARE on PMN (files 630549 / 630547).

**Action left to the user/orchestrator:** deliberately merge these 13 recovered docs into the
audited `meeting_minutes/` layer and update `minutes_unrecovered.csv` accordingly. This dataset
does not edit the existing layer.
