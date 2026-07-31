# PMN backfill coverage — Logan (2020–2026)

**As-of 2026-07-05.** Per-year, per-body: repo audited-minutes count vs PMN notices carrying a
`Meeting Minutes` attachment, recovered (net-new) and still-missing. Window = repo data floor 2020
through 2026.

Legend: `repo` = minutes in the audited layer; `pmn(min)` = PMN in-window notices with a Meeting-Minutes
attachment; `net-new` = PMN minutes for a meeting date the repo lacked, after document-level
verification; `missing` = in-window meetings with neither repo nor recoverable minutes.

## Municipal Council — PMN body 494 (repo `slug=city-council-meeting`)
| year | repo | pmn(min) | net-new recovered | still-missing |
|-----:|-----:|---------:|------------------:|--------------:|
| 2020 | 22 | 23 | 0 | 0 |
| 2021 | 22 | 22 | 0 | 0 |
| 2022 | 22 | 22 | 0 | 0 |
| 2023 | 22 | 23 | 0 | 0 |
| 2024 | 22 | 22 | 0 | 0 |
| 2025 | 26 | 25 | 0 | 0 |
| 2026 | 13 | 14 | 0 | 0 |
| **Σ** | **149** | **151** | **0** | **0** |

The three per-year PMN excesses (2020, 2023, 2026 all +1) are notice-date-vs-content-date artifacts,
not gaps (see AVAILABILITY.md). Two of them (2020-03-17 CANCELLED → 2020-03-03 minutes; 2026-06-16 →
2026-05-26 minutes) were downloaded and verified as already-held; the 2023 excess resolved inside the
±4-day tolerance.

## Planning Commission — PMN body 487 (repo `planning_commission/minutes_index.csv`)
| year | repo | pmn(min) | net-new recovered | still-missing |
|-----:|-----:|---------:|------------------:|--------------:|
| 2020 | 21 | 19 | 0 | 0 |
| 2021 | 21 | 4 | 0 | 0 |
| 2022 | 22 | 0 | 0 | 0 |
| 2023 | 21 | 0 | 0 | 0 |
| 2024 | 18 | 0 | 0 | 0 |
| 2025 | 17 | 0 | 0 | 0 |
| 2026 | 10 | 0 | 0 | 0 |
| **Σ** | **130** | **23** | **0** | **0** |

PMN stops attaching PC minutes after 2021; the repo (Revize/Community Development) is the authoritative
superset every year.

## Redevelopment Agency — PMN body 495 (repo `slug=redevelopment-agency-meeting`)
| year | repo | pmn(min) | net-new recovered | still-missing |
|-----:|-----:|---------:|------------------:|--------------:|
| 2020 | 10 | 10 | 0 | 0 |
| 2021 | 14 | 12 | 0 | 0 |
| 2022 | 6 | 6 | 0 | 0 |
| 2023 | 10 | 10 | 0 | 0 |
| 2024 | 3 | 2 | 0 | 0 |
| 2025 | 5 | 3 | 0 | 0 |
| 2026 | 1 | 0 | 0 | 0 |
| **Σ** | **49** | **43** | **0** | **0** |

The single flagged 2020-03-17 RDA candidate (file 584229) is byte-identical to the Council file and is
the already-held March 3 2020 combined minutes.

## Totals
| body | repo | pmn(min) | net-new recovered | still-missing |
|------|-----:|---------:|------------------:|--------------:|
| Council (494) | 149 | 151 | 0 | 0 |
| PC (487) | 130 | 23 | 0 | 0 |
| RDA (495) | 49 | 43 | 0 | 0 |
| **all** | **328** | **217** | **0** | **0** |

**Recovered net-new: 0 documents.** 3 PMN minutes PDFs were downloaded and verified (0.9 MB in `raw/`),
all confirmed duplicates of already-held minutes and logged in `index.csv` with
`status=duplicate-not-promoted`. **0 in-scope minutes remain unrecovered.**
