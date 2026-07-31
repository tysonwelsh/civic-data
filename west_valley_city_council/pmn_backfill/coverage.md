# PMN backfill coverage — West Valley City (window 2020–2026)

Per-year set-difference of **PMN meeting dates** (bodies 398/399/401/402) against the
repo's audited minutes layer (`meeting_minutes/minutes_index.csv` for CC/RDA/MBA;
`planning_commission/minutes_index.csv` for PC). Additive only — nothing here edits the
minutes layer.

Method: parsed every notice on each body's cumulative `notices.html` page, kept those
carrying a `(Meeting Minutes)` attachment, resolved each to its **true meeting date**
(read from the notice title / PDF, not the PMN `event_date` field — see the two data-entry
quirks below), then subtracted repo dates for the same body (±1 day). Every genuine
gap's PDF was opened and its internal date + minutes heading verified before promotion.

Legend: `repo_dates` = distinct meeting dates already in the repo (Regular+Study on one
day collapse to one date); `pmn_min_notices` = PMN notices bearing a minutes attachment
(Regular and Study file as separate notices, so this runs ~2× the CC date count — the two
layers are in fact well-aligned); `recovered` = new minutes added by this dataset.

## City Council (body 398)

| Year | repo_dates | pmn_min_notices | recovered |
|-----:|-----------:|----------------:|----------:|
| 2020 | 43 | 84 | 1 |
| 2021 | 43 | 85 | 1 |
| 2022 | 44 | 72 | 0 |
| 2023 | 43 | 66 | 1 |
| 2024 | 40 | 76 | 0 |
| 2025 | 27 | 52 | 1 |
| 2026 | 11 | 25 | 4 |
| **Total** | | | **8** |

## Redevelopment Agency (body 399)

| Year | repo_dates | pmn_min_notices | recovered |
|-----:|-----------:|----------------:|----------:|
| 2020 | 14 | 12 | 0 |
| 2021 | 10 | 10 | 0 |
| 2022 | 7 | 5 | 0 |
| 2023 | 6 | 5 | 0 |
| 2024 | 6 | 7 | 1 |
| 2025 | 9 | 9 | 0 |
| 2026 | 4 | 4 | 1 |
| **Total** | | | **2** |

## Municipal Building Authority (body 401)

| Year | repo_dates | pmn_min_notices | recovered |
|-----:|-----------:|----------------:|----------:|
| 2020 | 3 | 3 | 0 |
| 2021 | 3 | 3 | 0 |
| 2022 | 6 | 5 | 0 |
| 2023 | 7 | 6 | 0 |
| 2024 | 3 | 3 | 0 |
| 2025 | 5 | 5 | 0 |
| 2026 | 2 | 3 | 1 |
| **Total** | | | **1** |

## Planning Commission (body 402)

| Year | repo_dates | pmn_min_notices | recovered |
|-----:|-----------:|----------------:|----------:|
| 2020–2026 | 263 | **0** | **0** |

PMN publishes **agendas only** for the PC — no minutes attachment exists on any of the
450 PC notices. Honest zero: the repo's 263 OnBase-sourced PC minutes are the superset.

## Total recovered: **11 minutes documents** (8 CC + 2 RDA + 1 MBA)

All 11 are genuinely absent from the repo and were recovered as clean extractable text
(no OCR needed). Two classes:

1. **Recent tail (post the repo's 2026-07-02 refresh):** 2026-06-09 CC Regular + Study,
   2026-06-09 (repo had only the RDA meeting that day), 2026-02-19/20 CC Budget Retreat,
   2026-01-27 RDA Special, 2026-01-13 MBA Annual.
2. **Off-cycle work sessions the OnBase minutes layer never captured:** the annual
   Strategic Planning / Budget Retreat meetings for 2020-01-17, 2021-01-15, 2025-02-21
   (repo held only the 2024-02-23 retreat), and the 2023-08-29 CC Special Study Meeting.

### Two PMN quirks that would have hidden gaps under a naive date match
- **`event_date` ≠ meeting date:** the 2026-02-20 Budget Retreat (Day 2) is filed with
  `event_date=2026-02-12`; the true date (2026-02-20) comes from the title/PDF. A ±4-day
  tolerance would have falsely absorbed it against the repo's 2026-02-10 meeting.
- **Near-adjacent real meetings:** the 2025-02-21 retreat sits 4 days from the repo's
  2025-02-25 meeting; only exact/±1-day matching on the true date surfaces it as a gap.
