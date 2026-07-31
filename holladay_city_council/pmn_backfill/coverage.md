# pmn_backfill/coverage.md — Holladay PMN sweep + PC-gap recovery

**As-of:** 2026-07-14. **Data floor:** 2020 (Holladay incorporated 1999; 2020 is a normal
floor, not an incorporation edge). All PMN body ids are for entity **Holladay = 160**.

## Part A — PMN full-history sweep (all 16 bodies)

Every Holladay PMN public body's cumulative notice list
(`/pmn/list/notices.html?id=<body>&page=300`, one GET = whole history) was swept and every
attachment parsed (1,165 attachments across 16 bodies). **Minutes** (attachment label
`Meeting Minutes`) appear under only **three** bodies; the other 13 bodies attach agendas /
packets (`Public Information Handout`) and 3 audio recordings only — **no hidden minutes**.
Cross-check is by the **meeting date embedded in each filename**, not the notice label.

| PMN body | id | minutes attachments | distinct dates | pre-2020 (below floor) | 2020+ | 2020+ already in repo? |
|---|---|---|---|---|---|---|
| City Council | 388 | 275 | 263 | 120 (2014–2019) | 143 | **YES — repo is a complete superset** |
| Planning Commission | 389 | 49 | 48 | 4 (2018-01) | 44 (2022:11, 2024:17, 2025:11, 2026:5) | **YES — repo superset; PMN has NO 2020/2021/2023 minutes** |
| Redevelopment Agency (RDA) | 791 | 15 | 15 | 10 (2017–2018) | 5 (2022×3, 2024×2) | **YES — all 5 already ingested as body=RDA docs** |
| Board of Adjustments | 390 | 0 | — | — | — | (agendas/notices only) |
| Design Review Board | 392 | 0 | — | — | — | (agendas/notices only) |
| Administrative Appeals | 4813 | 0 | — | — | — | (agendas/notices only) |
| Arts Council | 4823 | 0 | — | — | — | (agendas/notices only) |
| Historical Commission | 6055 | 0 | — | — | — | (agendas/notices only) |
| Tree Committee | 6211 | 0 | — | — | — | (agendas/notices only) |
| Housing Task Force | 2398 | 0 | — | — | — | (agendas/notices only) |
| Education Task Force | 391 | 0 | — | — | — | (agendas/notices only) |
| Adopted Ordinances | 7341 | 0 | — | — | — | (ordinance PDFs, not minutes) |
| Bids & RFPs | 6605 | 0 | — | — | — | (RFP docs only) |
| Elections | 8423 | 0 | — | — | — | (notices only) |
| Elections/Board of Canvassers | 9191 | 0 | — | — | — | (notices only) |
| Local Building Authority (LBA) | 9331 | 0 | — | — | — | (no minutes on PMN; repo LBA rows are in-session, tagged from council docs) |

**Conclusions of the sweep**
1. **Council (388): the repo is a complete PMN superset for the 2020+ analysis window.**
   PMN offers no 2020+ council minutes the repo lacks. PMN additionally holds **120 pre-2020
   council minutes (2014–2019)** below the data floor — available if the floor is ever
   lowered, out of current scope.
2. **PC (389): the documented gap is CONFIRMED at source.** PMN body 389 has minutes for
   **2022 and 2024–2026 only**; it published **zero Meeting-Minutes attachments for 2020,
   2021, or 2023** (only agendas/packets). The repo already holds all 44 of PMN 389's 2020+
   minutes. So the 2020/2021/2023 PC gap is a real upstream PMN gap, not an ingest miss.
3. **RDA (791): no gap.** All 5 in-floor standalone RDA minutes (2022-04-21/05-05/06-02,
   2024-01-04/06-06) are already in the repo as `body=RDA` docs. 10 pre-floor (2017–2018).
4. **No other body holds minutes** — the "sweep every body" check surfaced no minutes hiding
   under a sibling body's notices.

## Part B — Planning Commission gap recovery (2020 / 2021 / 2023)

The 62 PC meetings PMN lacks minutes for were pursued on the independent city channels:
**SuiteOne** (`holladayut.suiteonemedia.com`), the **live Revize Document Center**
(`holladayut.gov`), and the **city's former WordPress site** (`cityofholladay.com`) via the
**Wayback Machine**. SuiteOne holds **2025+ only** (every body `data-yearFrom="2025"`; its
history search is POST/CSRF, out of the polite-GET rule). The live Revize Document Center
`Planning Commission/2020|2021/` folders exist (HTTP 403, listing forbidden) but `2022|2023/`
do not (404), and individual filenames are not enumerable. **The Wayback capture of the
WordPress `/file/<yr>/<mo>/<MMDDYY>-PC-Mtg.pdf` uploads is what carried the recoverable
minutes.**

| Year | PC meetings missing minutes on PMN | recovered here | still missing | recovery source |
|---|---|---|---|---|
| 2020 | 23 | **16** | 7 | Wayback → cityofholladay.com `/file/2020/12/` |
| 2021 | 20 | **11** | 9 | Wayback → cityofholladay.com `/file/2021/05,07/` |
| 2023 | 19 | **0** | 19 | none — never published to any channel |
| **Total** | **62** | **27** | **35** | |

**Recovered (27):** all of **2020 H1 (Jan–Sep, less 04-07)** and **2021 H1 (Jan–Jun)**.
Every file is born-digital (`pdftotext -layout` clean, 11k–47k chars), header-verified
`MINUTES OF THE CITY OF HOLLADAY … Planning Commission`, and keyed on its **internal meeting
date**, not the filename. See `index.csv`.

**Still missing (35) — honest gaps, logged in `unrecovered.csv`:**
- **2020-04-07 (1):** source published the **wrong file** — `040720-PC-Mtg.pdf` actually
  contains the **2020-06-16** minutes (a city upload error, faithfully preserved in Wayback).
  The true 04-07 minutes were not found on any channel. (This is why the raw fetch of 28 PDFs
  yields only 27 distinct meetings.)
- **Late 2020 (6):** 10-06, 10-20, 11-10, 11-17, 12-01, 12-15 — Wayback holds only the
  *packets* for these; minutes were uploaded after the last WordPress crawl and are not on the
  live Document Center under probed names.
- **2021 H2 (9):** 07-13 … 12-14 — same pattern (packets captured, minutes not).
- **All 2023 (19):** no PC minutes on PMN 389, none in Wayback (packets only), no live
  `Planning Commission/2023/` folder. Appears never published in a recoverable form.

These 35 remain recoverable in principle only from the city's internal Revize Document Center
(needs a folder listing the public site does not expose) or a future PMN backfill by the city.
