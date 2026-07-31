# PMN backfill — St. George coverage cross-check (SOURCE 4)

**As-of:** 2026-07-02 · **Method:** per-DATE set-difference (±3-day tolerance), repo
`minutes_index.csv` dates vs Utah PMN "Meeting Minutes"-labeled attachments, for both the
City Council and Planning Commission bodies. Data floor = 2020 (repo floor).

## PMN body ids (discovered via GET chain, NOT guessed)

`entities.html?id=3` (govType 3 = Municipality) → **St. George entity id = 277** →
`publicBodies.html?id=277` enumerated every body. Correcting the recon's assumption that
241 & 242 were two *council* bodies:

| Body | PMN id | notice history |
|---|---|---|
| **City Council** | **241** | 2015-02 → 2026-07 (cumulative `notices.html?id=241&page=300`) |
| **Planning Commission** | **242** | 2014-03 → 2026-07 (cumulative `notices.html?id=242&page=300`) |

(241 = Council, 242 = Planning Commission — they are *different bodies*, not work-vs-regular
splits of one council. The full 30-body list for entity 277 is in `CLAUDE.md`.)

## Per-year coverage (2020+)

`repo` = distinct meeting dates already in the audited minutes layer.
`pmn_min` = distinct dates with a PMN "Meeting Minutes" attachment.
`recovered` = genuine date-level gaps this backfill added.

### City Council (body 241)
| year | repo | pmn_min | recovered | note |
|---|---|---|---|---|
| 2020 | 38 | 39 | 0 | the +1 PMN date (2020-08-27) is a **false positive** — its file is `09.03.2020 minutes.pdf`, and 2020-09-03 is already in the repo |
| 2021 | 44 | 44 | 0 | complete |
| 2022 | 44 | 48 | **4** | 03-03, 03-31, 04-28, 09-22 all recovered |
| 2023 | 44 | 48 | **2** | 06-08, 11-09 recovered |
| 2024 | 33 | 35 | **2** | 01-18, 04-11 recovered |
| 2025 | 39 | 40 | 0 | the +1 PMN date (2025-07-31) is an **Arts Commission** meeting mis-posted under the Council body — excluded (wrong body) |
| 2026 | 12 | 12 | 0 | complete |

**Council recovered: 8 meeting dates / 11 documents** (2022-09-22 = work + regular + joint
CC/PC = 3 docs; 2023-06-08 = council work + joint CC/RDA = 2 docs). All confirmed
`ST. GEORGE CITY COUNCIL MINUTES` in the text.

### Planning Commission (body 242)
| year | repo | pmn_min | recovered | note |
|---|---|---|---|---|
| 2020 | 18 | 17 | **1** | 06-23 (a .docx) recovered |
| 2021 | 21 | 23 | **2** | 02-09, 02-23 recovered (PMN filenames mis-year as "2020"; internal dates confirm 2021) |
| 2022 | 19 | 19 | 0 | complete |
| 2023 | 18 | 23 | **4** | 07-25, 09-26, 10-10, 10-24 recovered as minutes; **05-23 minutes were never posted to PMN** — only a 178-page agenda packet exists (it embeds the *prior* 05-09 minutes, already in repo). Agenda packet retained + logged; the 05-23 minutes remain genuinely unavailable. |
| 2024 | 25 | 23 | 0 | repo is a superset of PMN here |
| 2025 | 20 | 21 | **1** | 01-14 recovered (PMN filename mis-year as "2024.01.14"; internal date confirms JANUARY 14, 2025) |
| 2026 | 10 | 10 | 0 | complete |

**PC recovered: 8 minutes dates + 1 agenda-only date = 9 documents.**

## Totals
- **Recovered into this dataset: 20 documents across 17 distinct meeting dates**
  (16 minutes dates + 1 agenda-only date). Council 8 dates/11 docs · PC 9 dates/9 docs.
- **Excluded (correctly, not gaps):** 2020-08-27 council (dup of 09-03), 2025-07-31 council
  (Arts Commission, wrong body), one byte-identical duplicate of 2023-11-09.
- **Still genuinely missing:** the **2023-05-23 Planning Commission minutes** — never posted
  to PMN in any form (only the agenda packet). No other date-level minutes gap remains.

## Caveats
- Cross-check is PMN-directional: it recovers PMN minutes absent from the repo. The repo is a
  broad superset elsewhere (e.g. PC 2024 repo 25 > PMN 23), which is expected and not a defect.
- ±3-day tolerance handles meeting-date vs posted-date offset; St. George meetings are ≥7 days
  apart so no adjacent-meeting collisions were possible.
- Recon's note that "2020–21 minutes were already backfilled from PMN" is confirmed: only ONE
  2020–21 date-level gap surfaced across BOTH bodies for those years (PC 2020-06-23), plus the
  two PC 2021-02 files — the rest of the recovered gaps are 2022–2025 (Revize-era) where PMN
  happened to hold work-meetings / joint meetings the city site did not surface.
