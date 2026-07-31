# Vineyard PMN backfill — coverage & gap analysis (as-of 2026-07-05)

Window 2014–2026. Diffed against `meeting_minutes/minutes_index.csv` (CC) and
`planning_commission/minutes_index.csv` (PC). RDA (body 2598) has no repo layer, so
every recovered RDA row is net-new. Candidate = a PMN notice carrying a
`(Meeting Minutes)` attachment for that body, deduped by the meeting date read INSIDE
each PDF. **`source-gone` = PMN lists the notice but the attachment file 404s (blob
purged) — an honest, unrecoverable gap.** `oversize` = attachment >8 MB (scanned
packet mislabeled as minutes), logged but body not stored.

## CC (PMN body 530)

| Year | Repo minutes | PMN minutes-notices | Recovered | Dup(in repo) | Source-gone(404) | Oversize |
|------|-------------:|--------------------:|----------:|-------------:|-----------------:|---------:|
| 2015 | 0 | 28 | 0 | 0 | 28 | 0 |
| 2016 | 0 | 24 | 0 | 0 | 24 | 0 |
| 2017 | 0 | 23 | 0 | 0 | 23 | 0 |
| 2018 | 0 | 19 | 1 | 0 | 18 | 0 |
| 2019 | 0 | 21 | 13 | 1 | 0 | 7 |
| 2020 | 23 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 25 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 25 | 0 | 0 | 0 | 0 | 0 |
| 2023 | 27 | 0 | 0 | 0 | 0 | 0 |
| 2024 | 24 | 0 | 0 | 0 | 0 | 0 |
| 2025 | 32 | 1 | 0 | 0 | 0 | 1 |
| 2026 | 16 | 3 | 1 | 0 | 0 | 2 |
| **all** | **172** | **119** | **15** | **1** | **93** | **10** |

## PC (PMN body 531)

| Year | Repo minutes | PMN minutes-notices | Recovered | Dup(in repo) | Source-gone(404) | Oversize |
|------|-------------:|--------------------:|----------:|-------------:|-----------------:|---------:|
| 2015 | 0 | 17 | 0 | 0 | 17 | 0 |
| 2016 | 0 | 14 | 0 | 0 | 14 | 0 |
| 2017 | 0 | 16 | 0 | 0 | 16 | 0 |
| 2018 | 0 | 10 | 0 | 0 | 10 | 0 |
| 2020 | 16 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 18 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 17 | 0 | 0 | 0 | 0 | 0 |
| 2023 | 21 | 0 | 0 | 0 | 0 | 0 |
| 2024 | 13 | 1 | 1 | 0 | 0 | 0 |
| 2025 | 15 | 0 | 0 | 0 | 0 | 0 |
| 2026 | 2 | 0 | 0 | 0 | 0 | 0 |
| **all** | **102** | **58** | **1** | **0** | **57** | **0** |

## RDA (PMN body 2598)

| Year | Repo minutes | PMN minutes-notices | Recovered | Dup(in repo) | Source-gone(404) | Oversize |
|------|-------------:|--------------------:|----------:|-------------:|-----------------:|---------:|
| 2015 | 0 | 8 | 0 | 0 | 8 | 0 |
| 2016 | 0 | 18 | 0 | 0 | 18 | 0 |
| 2017 | 0 | 12 | 0 | 0 | 12 | 0 |
| 2018 | 0 | 12 | 2 | 0 | 10 | 0 |
| 2019 | 0 | 8 | 8 | 0 | 0 | 0 |
| 2020 | 0 | 5 | 5 | 0 | 0 | 0 |
| 2021 | 0 | 12 | 6 | 0 | 0 | 6 |
| 2022 | 0 | 13 | 7 | 0 | 0 | 6 |
| 2023 | 0 | 12 | 8 | 0 | 0 | 4 |
| 2024 | 0 | 9 | 3 | 0 | 0 | 6 |
| 2025 | 0 | 8 | 2 | 0 | 0 | 6 |
| 2026 | 0 | 2 | 2 | 0 | 0 | 0 |
| **all** | **0** | **119** | **43** | **0** | **48** | **28** |

## Totals

- **Recovered (new meeting dates added): 59** — CC 15, PC 1, RDA 43.
- Source-gone (notice present, file 404 / purged from PMN): 198.
- Oversize (>8 MB, not stored; scanned packets mislabeled minutes): 38.

### Reading
- **CC/PC 2020–2026 is a repo superset** — near-zero recoveries there (the few hits
  are genuine within-window gaps: CC 2026-05-12, PC 2024-02-07, each verified against
  the repo index).
- The **pre-2020 tail (CC/RDA 2018–2019)** is where PMN still had live files; earlier
  years (2015–2017) are almost entirely `source-gone` — PMN has purged those blobs, so
  the notices survive but the minutes PDFs are unrecoverable from this source.
- **RDA is entirely new** to the repo: 43 board-meeting minutes 2018–2026 recovered.
