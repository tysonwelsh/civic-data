# PMN backfill — coverage (Midvale City)

> ✅ **PROMOTED 2026-07-16** (see `CLAUDE.md`). Correction to this doc's recovered-dates list: the "2023-01-17" RDA doc actually contains the **2022-12-06 RDA minutes** (merged under that date); the 2023-01-17 RDA session's own minutes remain unrecovered (`meeting_minutes/minutes_unrecovered.csv`).

**As of 2026-07-13.** Utah Public Notice (utah.gov/pmn) sweep of **every** Midvale public
body, cross-checked by **meeting DATE** (±4-day tolerance) and **document count** against the
repo's audited `meeting_minutes/minutes_index.csv` (Council session) and
`planning_commission/minutes_index.csv`. Minutes were detected by scanning attachment
**FILENAMES**, not the PMN type labels (labels mislabel/under-count).

Midvale's core minutes came from the city's **own Revize Document Center** — so PMN here is an
**independent cross-check**, not a superset source. It found **genuine gaps** in the repo's
2020+ window.

## PMN entity + body ids (Midvale entity id = 201)

| body id | body | minutes-like attachments | role |
|---|---|---|---|
| 753 | City Council | 183 | primary — Council session |
| 754 | Planning Commission (Midvale) | 48 | primary — P&Z |
| 756 | Redevelopment Agency | 91 | in-session RDA (companion docs) |
| 757 | Municipal Building Authority | 19 | in-session MBA (companion docs) |
| 755 | Board of Adjustments | 0 | agendas/notices only — no minutes |
| 9155 | Appeal Authority | 0 | 1 variance notice — no minutes |
| 758 | Midvale Community Council | 0 | 1 festival agenda — no minutes |
| 760 | Union Community Council | 0 | empty |
| 9179 | White City Council | 0 | empty (own entity elsewhere) |

Every body was swept. No council/PC minutes were found cross-filed under a *different* body
(the alta/murray failure mode does not occur here) **except** the RDA/MBA companion docs, which
are the same Council-session dates split out by body, and 6 **Harvest Days Committee** minutes
cross-filed under the City Council body (a festival committee — NOT a council meeting; see
below).

## Council session (CC + in-session RDA + MBA) — per year

`repo` = distinct dates in `meeting_minutes/minutes_index.csv`; `PMN` = distinct meeting-dates
PMN holds minutes for (across bodies 753/756/757); `recovered` = new dates fetched here;
`still-missing` = genuine council-session dates PMN has that the repo lacks, after recovery;
`ocr-upgrade` = repo OCR-era dates for which a **born-digital** PMN copy exists.

| year | repo | PMN | recovered | still-missing | ocr-upgrade |
|---|---|---|---|---|---|
| 2015 | 0 | 1 | 0 | — below floor — | 0 |
| 2016 | 0 | 7 | 0 | — below floor — | 0 |
| 2017 | 0 | 11 | 0 | — below floor — | 0 |
| 2018 | 0 | 14 | 0 | — below floor — | 0 |
| 2019 | 0 | 14 | 0 | — below floor — | 0 |
| 2020 | 26 | 19 | 1 | 0 | 0 |
| 2021 | 25 | 21 | 1 | 0 | 0 |
| 2022 | 26 | 23 | 1 | 0 (2 Harvest Days, non-council) | 0 |
| 2023 | 21 | 21 | 3 | 0 (1 Harvest Days, non-council) | 0 |
| 2024 | 18 | 29 | 7 | 0 (3 Harvest Days, non-council) | 0 |
| 2025 | 22 | 22 | 1 | 0 | 0 |
| 2026 | 12 | 12 | 0 | 0 | 0 |

**Recovered council-session dates (14 dates / 25 docs):**
2020-01-21, 2021-01-19, 2022-01-18, 2023-01-17, 2023-03-30 (budget retreat), 2023-06-20,
2024-02-20, 2024-02-27 (special mtg), 2024-03-12, 2024-05-07, 2024-05-21, 2024-06-18,
2024-08-06 (RDA-only doc), 2025-06-03. Each keeps its CC doc plus the distinct RDA/MBA
companion doc(s) PMN filed for the same session (indexed with `body` = Council / RDA / MBA).
The 2024 cluster is the most consequential: the repo's 2024 council coverage had real holes
(no Feb, no May, mid-March, mid-June) that PMN fills.

## Planning Commission — per year

| year | repo | PMN | recovered | still-missing |
|---|---|---|---|---|
| 2017 | 0 | 13 | 0 | — below floor — |
| 2018 | 0 | 17 | 0 | — below floor — |
| 2019 | 0 | 14 | 0 | — below floor — |
| 2020 | 18 | 1 | 0 | 0 |
| 2021 | 16 | 0 | 0 | 0 |
| 2022 | 15 | 0 | 0 | 0 |
| 2023 | 13 | 0 | 0 | 0 |
| 2024 | 14 | 0 | 0 | 0 |
| 2025 | 18 | 2 | 0 | 0 |
| 2026 | 9 | 0 | 0 | 0 |

**PC is fully covered within the repo's 2020+ window — zero recoverable PMN gaps.** PMN's PC
holdings are almost entirely pre-2020 (2017-2019) and are below the data floor. (The repo's
one known PC gap, 2024-08-28, is a corrupt/blank scan logged in
`planning_commission/minutes_unrecovered.csv`; PMN does **not** hold a copy — still unrecovered.)

## OCR-upgrade candidates for the 2020-2021 seam — NONE AVAILABLE

The repo's 2020-2021 council minutes are scanned image PDFs recovered via OCR (`format=ocr`).
PMN was checked as a potential born-digital upgrade source for that seam. **Verified negative:**
the two recovered seam dates (2020-01-21, 2021-01-19) and three additional probed PMN files for
existing repo-OCR dates (CC 2020-06-02, 2020-10-06, 2021-05-04) all have a **zero-character text
layer** — they are the **same scanned images** as the repo. Midvale scanned that entire era;
no born-digital copy exists on PMN. **OCR-upgrade candidates = 0.** (The two recovered
seam-date docs are therefore themselves `format=scanned`/`extraction_method=ocr`, not upgrades.)

## Below-floor availability (catalogued, deliberately NOT recovered)

PMN holds a substantial **pre-2020** Midvale record — roughly **47 council-session dates
(2015-2019)** and **44 P&Z dates (2017-2019)** — below the repo's documented **2020 analysis
floor** (Midvale incorporated 1909; 2020 is a deliberate floor, not an incorporation edge).
These are left unrecovered so the backfill does not silently move the floor; extending Midvale
below 2020 is a scope decision for the user. Full list is derivable from
`_work/attachments_all.csv` (minutes-like rows with `mdate < 2020`).

## Out-of-scope items identified during the sweep

- **Harvest Days Committee minutes (6 docs)** cross-filed under the City Council PMN body:
  2022-04-28, 2022-06-30, 2023-12-13, 2024-02-07, 2024-03-06, 2024-06-12. These are a
  **festival committee**, not the City Council — not recovered (recording them as council
  coverage would be fabrication). Listed here as an honest find.
- Board of Adjustments / Appeal Authority / community-council bodies publish agendas and
  hearing notices only — **no minutes** on PMN.
