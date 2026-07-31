# Draper — PMN backfill coverage (as of 2026-07-13)

Cross-check of the audited repo minutes layers against the Utah Public Notice
repository (`utah.gov/pmn`), per-DATE (not per-year counts), floor **2020**
(the repo's data floor). PMN entity id **114** (govType 3 = Municipality).

**Headline: 6 meetings recovered (7 raw files — one byte-identical duplicate
posting), all verified against internal PDF headers.**

- **3 of the repo's logged unrecoverable meetings are now recovered from PMN**
  (council 2021-07-20; PC 2020-12-10, 2024-10-10 — all three were broken
  ~299-byte Granicus stubs).
- **3 council meetings the repo never knew existed** — August **Truth-in-Taxation
  special sessions** (2022-08-24 TRSSD certified tax rate; 2024-08-14; 2025-08-13)
  that Granicus's ViewPublisher listing does not carry at all. Draper apparently
  posts its TnT hearings to PMN only.

## Bodies crawled (cumulative `notices.html?id=<body>&page=200`, GET-only)

| PMN body id | Body | Notices | Notice dates w/ minutes-type attachment |
|---|---|---|---|
| 5555 | City Council (current) | 1,050 | 226 (2016-07 → 2026-06-09) |
| 379 | City Council (defunct label) | 627 | 97 (2013-04 → 2018-09) |
| 383 | Planning Commission | 1,058 | 198 (2013-04 → 2026-05-28) |
| 382 | CRA formerly Redevelopment Agency | 157 | 45 (2013 → 2021-06) |
| 7261 | Community Reinvestment Agency (current) | 34 | 18 (2021-11 → 2026-05) |
| 381 | Municipal Building Authority | 55 | 23 (2013 → 2023-01) |
| 380 | Historic Preservation Commission | 203 | 76 (2014 → 2026-05) |
| 6647 | Zoning Administrator | 26 | 19 (2020-04 → 2023-07) |
| 378 | Board of Adjustments | 5 | 0 |

Minutes detection = attachment label `(Meeting Minutes)` **OR** "minutes" in the
attachment filename (the herriman lesson — labels under-count; here it also
OVER-counts: a handful of PC public-hearing handouts, e.g. `PC 12.11 Butler
Zoning Map Amendment Request.pdf`, carry a mislabeled `Meeting Minutes` tag —
each non-match was filename/date-verified before being counted a gap).

## City Council — per year (floor 2020)

Repo = `meeting_minutes/minutes_index.csv` docs; PMN = distinct notice dates with
a minutes attachment (bodies 5555 + 379). The sets overlap but neither contains
the other — the diff below is per-date.

| Year | Repo docs | PMN minutes dates | Recovered | Still missing from repo |
|---|---|---|---|---|
| 2020 | 24 | 20 | 0 | — |
| 2021 | 23 | 23 | **1** (2021-07-20) | — |
| 2022 | 22 | 19 | **1** (2022-08-24 TnT/TRSSD) | — |
| 2023 | 22 | 17 | 0 | — |
| 2024 | 24 | 23 | **1** (2024-08-14 TnT; + 1 duplicate posting) | — |
| 2025 | 24 | 24 | **1** (2025-08-13 TnT) | — |
| 2026 | 12 | 12 | 0 | 2026-07-07 (recap-only; adopted minutes on neither Granicus nor PMN yet — PMN notice 2026-07-07 carries agenda/packet/Recap only) |

After recovery, **every PMN council minutes date ≥ 2020 is accounted for in
repo + this dataset**; the repo remains a superset of PMN for all remaining dates
(PMN misses some meetings the repo has, e.g. 4 of 24 in 2020).

## Planning Commission — per year (floor 2020)

| Year | Repo docs | PMN minutes dates | Recovered | Still missing from repo |
|---|---|---|---|---|
| 2020 | 23 | 18 | **1** (2020-12-10) | — |
| 2021 | 22 | 21 | 0 | — |
| 2022 | 21 | 21 | 0 | — |
| 2023 | 22 | 21 | 0 | — |
| 2024 | 20 | 20 | **1** (2024-10-10) | 2024-03-14 — see note below |
| 2025 | 24 | 18 | 0 | — |
| 2026 | 9 | 8 | 0 | 2026-06-11, 2026-06-25, 2026-07-09 (pending adoption; not on PMN either) |

## Cross-check of the repo's `minutes_unrecovered.csv` logs

| Logged gap | PMN result |
|---|---|
| Council 2021-07-20 (broken Granicus stub) | **RECOVERED** — file 745327, full 24-page adopted minutes |
| Council 2023-10-15 (`no_minutes_posted`) | **No 2023-10-15 doc on PMN.** PMN + repo both hold **2023-10-17** (Tuesday) minutes; the 10-15 Granicus listing appears to be a phantom/duplicate row for the 10-17 meeting. Left as-is (audited layer untouched). |
| Council 2026-07-07 (recap-only, pending adoption) | **Not yet on PMN** either (agenda/packet/Recap only, checked 2026-07-13). Re-check after adoption. |
| PC 2020-12-10 (broken Granicus stub) | **RECOVERED** — file 683931, approved 2021-01-14 |
| PC 2024-03-14 (`no_minutes_posted`) | **STALE LOG ROW** — the repo's own `minutes_index.csv` line 93 has this meeting (Granicus doc, fetched later). PMN also holds it (`DC PC Final Meeting Minutes 031424 - APPROVED.pdf`, file 1133863, not re-fetched). Flag for the maintainer to drop the stale unrecovered row. |
| PC 2024-10-10 (broken Granicus stub) | **RECOVERED** — file 1196659 |
| PC 2026-06-11 / 06-25 / 07-09 (pending adoption) | **Not on PMN** (PC minutes max = 2026-05-28) |

Also observed: council 2026-06-16 meeting was **cancelled** (PMN agenda
"City Council Agenda - Cancelled") — a real non-meeting, not a gap.

## Separate Granicus bodies the core repo does NOT acquire — PMN inventory

The core repo = Council + PC only. Granicus `view_id=1` also lists RDA (60 minutes
docs), MBA (29), CRA (25), HPC (152), Zoning Administrator (57) as separate bodies
(recon.md). PMN holds a THINNER mirror of each — **Granicus, not PMN, is the right
acquisition source if these bodies are ever built as core datasets**:

| Body | PMN minutes dates by year |
|---|---|
| RDA→CRA (382, old) | 2013:3 2014:5 2015:8 2016:3 2017:6 2018:9 2019:3 2020:3 2021:5 — renamed/re-registered mid-2021 |
| CRA (7261, current) | 2021:1 2022:3 2023:4 2024:4 2025:5 2026:1 |
| MBA (381) | 2013:2 2014:3 2015:3 2016:3 2017:3 2018:3 2019:2 2020:2 2021:1 2023:1 — PMN minutes stop 2023-01 |
| HPC (380) | 2014:2 2015:3 2016:1 2017:2 2018:1 2019:11 2020:6 2021:8 2022:11 2023:10 2024:8 2025:8 2026:5 |
| Zoning Administrator (6647) | 2020:7 2021:6 2022:3 2023:3 — body appears inactive on PMN after 2023-07 |
| Board of Adjustments (378) | none (5 notices, 0 minutes) |

None of these documents were fetched (inventory only, per task scope).

## Pre-floor inventory (below the repo's 2020 floor — NOT gaps)

PMN holds Draper council minutes back to **2013-04** (defunct body 379; incl.
paired "Action Taken" tally sheets 2013–2016) and PC minutes back to **2013-04**
(with a 2018 PC hole on PMN). Out of scope for the 2020-floor repo; recoverable
if the floor is ever lowered.
