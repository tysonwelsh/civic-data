# pmn_backfill coverage — Murray City (as of 2026-07-13)

Per-year × body reconciliation of the repo's audited minutes indexes against the Utah
Public Notice Website (PMN) inventory, and what this backfill recovered. "PMN minutes
dates" counts distinct meeting dates carrying a `(Meeting Minutes)` attachment on the
body's cumulative PMN notice list. Cross-checks were done **by meeting date (±4 days)**,
not by per-year counts.

## City Council — PMN body 735 "Municipal Council" (regular + special meeting series)

| Year | Repo (minutes_index) | PMN council-series minutes | Recovered here | Cancelled (no minutes exist) | Still missing |
|---|---|---|---|---|---|
| 2020 | 23 | all repo dates duplicated on PMN | 0 | — | 0 |
| 2021 | 20 | all repo dates duplicated on PMN | 0 | — | 0 |
| 2022 | 25 | all repo dates duplicated on PMN | 1 fetched (2022-06-21, tested as a born-digital upgrade for the repo's only OCR council file — the PMN copy is ALSO image-only; upgrade REJECTED, retained for the record) | — | 0 |
| **2023** | **5** | **23** (17 regular + 1 special + 5 repo-held) | **18** (17 regular + 1 net-new special 2023-08-21) | **1** (2023-07-11, PMN cancellation notice retained) | **0** |
| 2024 | 25 | all repo dates duplicated on PMN | 0 | — | 0 |
| 2025 | 24 | all repo dates duplicated on PMN | 0 | — | 0 |
| 2026 YTD | 10 | all repo dates duplicated on PMN | 0 | — | 0 |

**The 2023 council gap is fully resolved.** All 18 rows of
`meeting_minutes/minutes_unrecovered.csv` are accounted for: 17 meetings' official
approved minutes recovered from PMN, and 2023-07-11 was **cancelled** (PMN notice 844267
posts the official cancellation notice — that meeting never occurred, so no minutes
exist). One additional 2023 council meeting the repo did not know about was discovered
and recovered: the **2023-08-21 Special Council Meeting** (Millcreek/Murray North
Station), absent from both the index and the unrecovered log.

Note: PMN body 735 also carries **Committee of the Whole, council workshop, Budget &
Finance, City School Coordinating Council, town-hall and walking-tour minutes** (2020–2026)
that belong to no repo dataset — inventoried in `AVAILABILITY.md`, deliberately NOT
fetched here (out of the council-regular-series scope).

## Planning Commission — PMN body 983 "Planning and Zoning Commission"

Repo PC minutes end **2022-11-17** (the CivicPlus archive stops there). PMN carries the
PC minutes series continuously from 2023-01-05.

| Year | Repo (minutes_index) | PMN minutes dates | Recovered here | Cancelled meetings (PMN-noticed) | Still missing (held, no PMN minutes) |
|---|---|---|---|---|---|
| 2020 | 22 | 4 | 0 (7 dates 2020–21 noted as possible born-digital upgrades for repo OCR files — unfetched) | — | 0 |
| 2021 | 21 | 3 | 0 | — | 0 |
| 2022 | 18 | 15 | 0 | — | 0 |
| **2023** | **0** | **17** | **17** | 7 (02-16, 03-16, 05-04, 05-18, 07-06, 11-02, 12-21) | **0** |
| **2024** | **0** | **19** | **19** | 4 (01-18, 02-01, 02-15, 04-18); 07-04 holiday, never noticed | **0** |
| **2025** | **0** | 18 labeled (**17 real**) | **17** (+1 retained agenda) | 4 (02-06, 04-03, 09-18, 12-18); 06-19 never noticed on PMN | **2** (2025-04-17 — agenda posted, no minutes on PMN; **2025-07-17** — the PMN attachment labeled "Meeting Minutes" is actually the 2-page AGENDA, verified 2026-07-13 and retained honestly labeled) |
| **2026 YTD** | **0** | **6** | **6** | 2 (04-16, 06-04) | 4 agenda-only as of 2026-07-13 (02-05, 05-21, 06-18, 07-02) + 07-16 future |

**The PC 2023+ gap is essentially fully resolved**: **59 PC minutes recovered**
(2023-01-05 → 2026-05-07), plus one honestly-labeled agenda (2025-07-17, PMN-mislabeled
"Meeting Minutes"). Every no-minutes PC date 2023–2025 except 2025-04-17 and 2025-07-17
is an officially-noticed **cancellation**, not a publication gap. The four 2026
agenda-only dates are recent meetings whose minutes had not been posted as of retrieval
(PC minutes post after approval, one–two meetings later).

## Other Murray PMN bodies (no repo dataset exists — inventoried, not fetched)

| Body | PMN id | Minutes attachments on PMN (by year) |
|---|---|---|
| Redevelopment Agency | 987 | 2017:10 · 2018:8 · 2019:11 · 2020:12 · 2021:6 · 2022:8 · 2023:12 · 2024:13 · 2025:10 · 2026:4 |
| Municipal Building Authority of Murray City | 6863 | 2019:1 · 2020:1 · 2021:2 · 2022:4 · 2023:5 · 2024:6 · 2025:5 · 2026:2 |
| Murray City Center District (MCCD) Design Review Committee | 977 | 2022:3 · 2023:1 · 2024:4 · 2025:3 |

These are candidate future datasets (the CivicPlus archive also holds them: RDA AMID=61,
MBA AMID=46, MCCD AMID=64); recovering them was out of this backfill's scope (the repo
has no audited layer for these bodies to backfill against).
