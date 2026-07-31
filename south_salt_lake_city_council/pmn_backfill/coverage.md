# South Salt Lake pmn_backfill — coverage (as built 2026-07-13)

> **2026-07-16 update:** the promotion this file anticipated has HAPPENED — 119 of the 130
> recoveries were verified and promoted into the audited layer (11 rejected: 2 agenda packets,
> 9 duplicates of audited meetings; portal-label kinds corrected from content). The audited
> residual is now **214** agenda-only meetings, counted from disk. The tables below are the
> AS-BUILT 2026-07-13 estimate (slot-label kinds, predicted residual 216) and are retained as
> the recovery record — current truth lives in `../COVERAGE.md`.

This dataset re-verifies South Salt Lake's documented **coverage cliff** and records what an
independent-source probe recovered. Read `south_salt_lake_city_council/COVERAGE.md` and
`meeting_minutes/CLAUDE.md` first for the cliff's origin.

## The two findings

**(1) The PMN cliff is REAL — the core build missed nothing recoverable on Utah Public Notice.**
A full re-sweep of *every* SSL PMN body (entity **271**: council **1295**, RDA **1296**, PC
**1297**, plus MBA 2821, Civilian Review Board 7603, Ordinances 7441, Arts Council 5067,
Community-Development 4109/4247, Police/Public-Works/Purchasing/Taxing bodies) by **filename +
content** confirms:
- The only genuine PMN minutes the core did not take are **2014–2017** council/RDA files
  (`Minutes.pdf`, `2015.x.xRCMinutes.pdf`, …) — **before the 2020 data floor**, correctly out
  of scope.
- The **21 council + 2 RDA** `>22 MB` files the core skipped under its size cap were fetched and
  content-checked here: **all are agenda packets** (0 roll-call grammar). The **18 PC `>22 MB`**
  files *do* bundle real minutes, but **all were already recovered** by the core.
- MBA (2 notices, 2010), Taxing-Entity, Police, Public-Works bodies carry no in-scope minutes.
  Civilian Review Board (27 "Approved Minutes") and Arts Council (4) publish real minutes but are
  **non-governance bodies** (police oversight / arts board), outside the council/RDA/PC scope.

**(2) The cliff is PARTLY FILLABLE from an INDEPENDENT source the core never swept — the city's
own CivicPlus AgendaCenter.** The AgendaCenter's visible *Minutes* slot serves the agenda packet
(as the recon documented), **but the hidden `ArchivedMinutes` slot** — reached via each Minutes
doc's `…/AgendaCenter/PreviousVersions/_<date>-<id>` page — **holds the genuine recorded roll-call
minutes**, and for many **2022–2023 Planning-Commission** dates the *Minutes* slot itself is the
real minutes. These were content-detected (roll-call grammar / recorded-vote lines) and
recovered. **130 recorded minutes (2022–2026) the core had logged as agenda-only are recovered
here.** Source = `agendacenter` (NOT PMN); `pmn_body_id`/`pmn_file_id` are blank; `recovery_source`
distinguishes `agendacenter_archivedminutes` (113) vs `agendacenter_minutes` (17).

## Quantified cliff and fill (by body)

| Body | Core recorded (PMN) | Core agenda-only gaps | **Recovered here** | Gaps filled | Still agenda-only |
|---|---|---|---|---|---|
| **City Council** | 20 | 253 | **79** | 67 | 186 |
| **RDA** | 14 | 48 | **30** | 30 | 18 |
| **Planning Commission** | 45 | 19 | **21** | 7 | 12 |
| **Total** | 79 | 320 | **130** | 104 | 216 |

- **104** recoveries fill dates the core explicitly logged in `minutes_unrecovered.csv`; **26**
  are dates the core did not even list — chiefly **9 Planning-Commission minutes from 2022**
  (`2022-01-20 … 2022-11-17`), which **refute the core note "PC minutes begin 2023-01-19; 2020–2022
  never published."** 2022 PC minutes *were* published — on the AgendaCenter, not PMN. (2020–2021
  PC remain absent: the AgendaCenter PC listing itself starts 2022.)

## Recovered, by year × body

| Year | Council | RDA | PC | total |
|---|---|---|---|---|
| 2022 | 4 | 0 | 9 | 13 |
| 2023 | 16 | 7 | 5 | 28 |
| 2024 | 27 | 12 | 2 | 41 |
| 2025 | 19 | 8 | 3 | 30 |
| 2026 | 13 | 3 | 2 | 18 |
| **total** | **79** | **30** | **21** | **130** |

## The residual (still-honest) gap
**216** council/RDA/PC agenda-only dates remain with **no recorded minutes anywhere** (neither
PMN nor the AgendaCenter published a roll-call minutes doc). This is the genuine, now-smaller
residual publication cliff — mostly council work-meetings and mid-2021→2022 council regular
meetings. It is data, not a scraper miss. One acquisition cap remains documented: **87**
current-*Minutes*-slot files `>12 MB` (agenda packets) were HEAD-skipped rather than downloaded
in full; the recorded minutes for those dates, where they exist, were recovered instead from the
small `ArchivedMinutes` previous-version, so the cap did not cost a recovery in the sampled cases.

## Regenerate
```
python3 pmn_backfill/work/ssl_pmn_crawl.py            # full PMN body sweep -> ssl_pmn_all_attachments.json
python3 pmn_backfill/work/ssl_check_capped.py         # content-check the >22MB PMN files the core capped
python3 pmn_backfill/work/ssl_agendacenter_sweep.py --enumerate --check   # AgendaCenter ArchivedMinutes sweep
python3 pmn_backfill/build_backfill.py                # consolidate hits -> raw/ + text/ + index.csv
```
