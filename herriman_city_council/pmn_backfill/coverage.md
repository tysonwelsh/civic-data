# Herriman — Utah Public Notice (PMN) minutes cross-check & backfill coverage

> **STATUS 2026-07-16 — PROMOTED.** 66 of the recovered docs are merged into the
> audited vote layer (`provenance=pmn_minutes`; see `CLAUDE.md` §PROMOTED for the
> per-body split and the 5 withheld docs), and one further doc was fetched during
> promotion (2021-01-13 RCCM minutes, file 690779) → **71 recovered minutes** now
> indexed. The tables below are the original 2026-07-13 crawl record.

**As-of:** 2026-07-13 · **Method:** Source 4 of `expand-city-sources` (GET-only PMN
crawl → per-date, per-body set-difference against the repo minutes indexes).
**Result: 70 minutes documents recovered** (repo is NOT a superset here — unlike
Bluffdale) **+ 9 proof-of-cancellation notices for the 2020 gap dates.** PMN also
proved the repo's `meeting_minutes/CLAUDE.md` claim that the in-session agency
captures are "complete" is WRONG for the later era — PMN holds standalone
CDRA/HCSEA/HCFSA minutes whose content is absent from the repo's combined council
docs (verified: the 2024-05-08 / 2025-06-11 / 2025-08-13 combined docs contain zero
agency-section text).

## PMN discovery (GET-only)

- **Municipality entity:** Herriman = **entity id 155**
  (`utah.gov/pmn/list/entities.html?id=3` → `.../publicBodies.html?id=155`).
- **Herriman public bodies** (17 listed; 8 crawled via cumulative
  `notices.html?id=<body>&page=200` — full history in one GET each):

  | pmn_body_id | Body | Notices | Minutes attachments (all-time) | Range |
  |---|---|---|---|---|
  | **1155** | City Council | 866 | 325 | 2008-07 → 2026-07 |
  | **1151** | Planning Commission | 426 | 279 | 2008-07 → 2026-07 |
  | **2256** | Community Development and Renewal Agency (CDRA) | 106 | 49 | 2009-03 → 2026-07 |
  | **6239** | Herriman City Safety Enforcement Area (HCSEA) | 40 | 20 | 2018-01 → 2026-08 |
  | **7553** | Herriman City Fire Service Area (HCFSA) | 23 | 7 | 2022-01 → 2026-08 |
  | **1171** | Appeals Authority Board | 16 | 1 | 2008-07 → 2025-02 |
  | **1251** | Joint City Council and Planning Commission Work Meetings | 66 | 22 | 2008-07 → 2025-10 |
  | 1287 | Public Hearings and Notices | 764 | 0 | (no minutes — not a minutes body) |
  | — | Arts Council, Youth Council, Trails/OHV, Healthy Herriman, Economic Dev, Historical Society, Be Ready, Veterans Cmte | — | — | out of scope (non-council/PC boards) |

  PMN history reaches back to **2008** — far below the repo's 2020 data floor. Only
  2020+ was cross-checked and recovered; the 2008–2019 PMN holdings are a documented
  future-backfill option if the floor ever moves (noted in `AVAILABILITY.md`).

## Cross-check method

Per-date set-difference (±4-day posted-vs-meeting tolerance; exact-date for the joint
body), with each attachment classified to its TRUE body from its filename (RCCM/SCCM/
SCCW/BOC = council; PC/PCM = planning commission; CDA/CDRA, HCSEA, HCFSA = agencies;
"Joint"/"CCPC" = joint; "Appeal" = appeal authority) — PMN's own body filing is not
trusted (e.g. a council RCCM minutes doc filed under the PC body id, and Appeal
Authority minutes filed under PC). Two PMN label errors found and handled: the
2025-09-10 RCCM minutes PDF and the 2022-06-29 Joint minutes PDF are both labeled
`(Audio Recording)`; filename scan caught them. A per-date **doc-count** comparison
was then run to catch body-level shadowing (it caught 2020-09-09, where the repo's
one doc that day is the CDA minutes and the council RCCM minutes were absent).

## Coverage — 2020+ per year × body

"PMN docs" = unique PMN minutes attachments for that body-year. "Recovered" = fetched
into this dataset because absent from the repo. "In repo" = date-verified present in
`meeting_minutes/` / `planning_commission/` (for agencies: as a standalone repo doc
or — 2020–2022 era only — as an in-session section of the combined council doc).

| Year | Body | Repo docs | PMN docs | Already in repo | Recovered |
|---|---|---|---|---|---|
| 2020 | Council | 26 | 28 | 17 | **11** |
| 2020 | PC | 19 | 19 | 18 | **1** |
| 2020 | CDRA | (5 standalone in repo) | 3 | 3 | 0 |
| 2020 | HCSEA | 0 standalone | 2 | 0 | **2** |
| 2020 | Joint | (in repo as council/PC docs) | 3 | 3 | 0 |
| 2021 | Council | 45 | 43 | 39 | **4** |
| 2021 | PC | 23 | 17 | 15 | **2** |
| 2021 | CDRA | 0 standalone | 5 | 0 | **5** |
| 2021 | Joint | — | 1 | 1 | 0 |
| 2022 | Council | 30 | 26 | 23 | **3** |
| 2022 | PC | 19 | 22 | 18 | **4** |
| 2022 | CDRA | 0 standalone | 2 | 0 | **2** |
| 2022 | HCSEA | 0 standalone | 1 | 0 | **1** |
| 2022 | HCFSA | 1 standalone (2022-01-26) | 1 | 1 | 0 |
| 2022 | Joint | — | 3 | 1 | **2** |
| 2023 | Council | 22 | 24 | 22 | **2** |
| 2023 | PC | 19 | 24 | 19 | **5** |
| 2023 | Joint | — | 2 | 0 | **2** |
| 2024 | Council | 23 | 22 | 22 | 0 |
| 2024 | PC | 21 | 20 | 20 | 0 |
| 2024 | CDRA | 0 standalone | 4 | 0 | **4** |
| 2024 | HCSEA | 0 standalone | 3 | 0 | **3** |
| 2024 | HCFSA | 0 standalone | 2 | 0 | **2** |
| 2024 | Joint | — | 1 | 0 | **1** |
| 2025 | Council | 27 | 26 | 26 | 0 |
| 2025 | PC | 19 | 20 | 19 | **1** |
| 2025 | CDRA | 0 standalone | 3 | 0 | **3** |
| 2025 | HCSEA | 0 standalone | 4 | 0 | **4** |
| 2025 | HCFSA | 0 standalone | 3 | 0 | **3** |
| 2025 | Appeal Authority | 0 | 1 | 0 | **1** |
| 2026 | Council | 9 | 9 | 9 | 0 |
| 2026 | PC | 10 | 10 | 10 | 0 |
| 2026 | HCFSA | 0 standalone | 1 | 0 | **1** |
| 2026 | Appeal Authority | 0 | 1 | 0 | **1** |
| **Total** | | | **356** | **286** | **70** |

### The 70 recovered documents (by family)

- **Council (20):** 2020-03-25, 2020-05-13, **2020-09-09** (the repo's only doc that
  day is the CDA minutes — the RCCM council minutes were absent), 2020-09-23,
  2020-09-30 SCCW + 2020-09-30 SCCM (two additional distinct sessions beside the
  repo's Joint doc), 2020-10-05, 2020-10-08, 2020-10-14, 2020-11-05, 2020-12-09;
  2021-03-18, 2021-08-09, 2021-08-11, 2021-08-25; 2022-03-23, 2022-05-11,
  2022-06-13; 2023-12-05 (**Special Board of Canvassers** — election canvass),
  2023-12-15 SCCW (distinct from the repo's 2023-12-13 regular meeting).
- **Planning Commission (13):** 2020-12-03; 2021-06-17, 2021-10-07; 2022-03-17,
  2022-04-21, 2022-06-02, 2022-06-16; 2023-01-04, 2023-01-18, 2023-02-01,
  2023-10-18, 2023-11-01; 2025-05-21. (Four are scanned → `tesseract-ocr`,
  labeled: 2022-06-16, 2023-01-04, 2023-01-18, 2023-02-01.)
- **Joint CC/PC (5):** 2022-06-29 (verified DISTINCT from the repo's same-day 4:30 PM
  Special Council meeting — this is the 6:00 PM joint session; PMN label was "Audio
  Recording"), 2022-11-30, 2023-05-31, 2023-08-30, 2024-05-29.
- **CDRA (14):** 2021-01-13, 2021-01-27, 2021-03-24, 2021-06-09, 2021-11-10,
  2022-01-26, 2022-05-11, 2024-05-08, 2024-06-12, 2024-09-11, 2024-12-11,
  2025-02-12, 2025-04-09, 2025-06-25.
- **HCSEA (10):** 2020-05-27, 2020-06-10, 2022-05-11, 2024-05-08, 2024-06-12,
  2024-12-11, 2025-06-11, 2025-06-25, 2025-08-13, 2025-08-27.
- **HCFSA (6):** 2024-05-08, 2024-06-12, 2025-06-11, 2025-08-13, 2025-08-27,
  2026-03-25.
- **Appeal Authority (2):** 2025-02-20 (variance V2024-139 hearing; header says
  "AGENDA" but the body is narrative minutes — verified), 2026-06-09 (V2026-080).

**2022-05-11 was an entire meeting-day absent from the repo** (Council RCCM + CDRA +
HCSEA minutes all recovered). All recovered docs' internal headers/dates were
spot-verified; recovered council minutes carry the standard named roll-call vote
grammar (e.g. 2020-05-13 has six "The vote was recorded as follows:" rolls).

## 2020 gap dates — proven cancellations vs recovered meetings

The repo (`meeting_minutes/CLAUDE.md`) believed all 2020 interior gaps were COVID
cancellations. PMN splits that belief in two:

**Real meetings the repo was missing (now recovered here):** 2020-03-25, 05-13,
09-09 (council doc), 09-23, 09-30 (×2 extra sessions), 10-05, 10-08, 10-14, 11-05,
12-09 — plus PC 2020-12-03 and HCSEA 05-27 / 06-10.

**Proven cancellations (notice pages + one posted cancellation PDF retained in
`raw/cancel_*`):**

| Date | Body | Proof (notice) | What it says |
|---|---|---|---|
| 2020-01-16 | PC | 581069 | meeting CANCELLED |
| 2020-03-19 | PC | 594463 | meeting CANCELLED (COVID onset) |
| 2020-04-29 | Joint CC/PC | 601099 (+ posted PDF 594755) | work meeting CANCELLED |
| 2020-09-16 | Council (work) | 628319 | work meeting CANCELLED |
| 2020-10-21 | Council (work) | 634903 | work meeting CANCELLED |
| 2020-11-11 | Council | 639075 | **RESCHEDULED to 2020-11-18** (Veterans Day; the repo's 11-18 doc is that rescheduled meeting) |
| 2020-12-16 | Council (work) | 646095 | work meeting CANCELLED |
| 2020-12-17 | PC | 645781 | meeting CANCELLED |
| 2020-12-30 | Joint CC/PC | 647621 | work meeting CANCELLED |

**Dates with NO PMN trace at all** (no notice, agenda, minutes, or cancellation):
expected 2nd/4th-Wednesday slots 2020-07-22, 2020-11-25, 2020-12-23. Absence of any
posted notice is consistent with no meeting having been scheduled (summer/holiday
single-meeting months) — recorded as a finding, not stubbed.

**One honest, unrecoverable minutes gap:** the **2020-07-29 Joint CC/PC work
meeting** was HELD (PMN notice 618815 carries the meeting audio + packet) but no
minutes were ever posted, on PMN or anywhere found. The audio
(`2020 07 29 Joint CC PC.mp3`) remains on the notice if deliberation content is ever
needed.

## The agency (CDRA/HCSEA/HCFSA) finding — standalone minutes the repo lacks

The repo treats CDRA/HCSEA/HCFSA as in-session bodies captured inside the combined
council minutes (`body` column). That is true for the 2020–2022 era (verified: the
repo's combined docs and vote rows cover those sections, and 2020 standalone CDA
docs from the S3 era are already in `meeting_minutes/`). **From 2024 on it is
false:** PMN posts separate approved agency minutes and the repo's combined council
docs for those dates contain NO agency-section text (grep-verified 2024-05-08,
2024-06-12, 2025-06-11, 2025-08-13). All standalone agency minutes absent from the
repo (30 docs) are recovered here. **Follow-up (for TODO, not this dataset):** the
audited `meeting_minutes/` layer under-covers agency actions from ~2024 on; merging
these standalone agency minutes (and extracting their votes) needs a deliberate
promotion pass.

## Bottom line

- **Recovered: 70 minutes docs (33 MB) + 10 cancellation proofs.** The repo is NOT a
  PMN superset for Herriman — the opposite of the Bluffdale result.
- 2020 "COVID gap" belief: **partly right** (9 proven cancellations) and **partly
  wrong** (11 council-family docs recovered for 2020 alone).
- Still missing after this pass: only the 2020-07-29 joint minutes (never existed on
  PMN; audio survives) and the un-noticed 2020-07-22 / 11-25 / 12-23 slots (no
  evidence a meeting was ever scheduled).
- Do **not** merge into `meeting_minutes/` / `planning_commission/` in place — this
  is a review dataset; promotion into the audited layer is a separate, deliberate
  task (queued in the parent repo's TODO by the orchestrator, not this dataset).
