# pmn_backfill/ — coverage (Riverton City)

**As-of:** 2026-07-13. **Data floor:** 2020-01-01 (repo convention; PMN/Granicus hold
pre-2020 material that is out of scope and is NOT counted as a gap).

Two independent minutes sources were diffed against the audited repo, by meeting **date**
(±4-day tolerance), for the two core bodies the repo covers (City Council, Planning
Commission):

- **PMN** — Utah Public Notice, body 889 (Council) / 5473 (PC). This is the source the
  repo's audited minutes were originally harvested from, so it is a completeness re-check.
- **Granicus** — `rivertoncity.granicus.com` ViewPublisher `view_id=1`, the **independent**
  archive. Enumerated from the full server-rendered `ViewPublisher.php` table (599 minutes
  links, 2015–2026) — the `ViewPublisherRSS.php?mode=minutes` feed caps at the most recent
  100 items and was used only as a cross-check.

Per year × body × source (minutes documents, within the 2020 floor). "Union" = distinct
meeting-dates carried by any source; "Recovered" = added to `pmn_backfill/` this run;
"Still-missing" = union dates absent from both the audited repo and the recovery set.

### City Council
| Year | Repo | PMN-min | Granicus-min | Recovered | Union | Still-missing |
|---|---|---|---|---|---|---|
| 2020 | 19 | 22 | 22 | 3 | 22 | 0 |
| 2021 | 20 | 20 | 20 | 0 | 20 | 0 |
| 2022 | 21 | 21 | 21 | 0 | 21 | 0 |
| 2023 | 19 | 19 | 21 | 2 | 21 | 0 |
| 2024 | 19 | 19 | 19 | 0 | 19 | 0 |
| 2025 | 20 | 20 | 20 | 0 | 20 | 0 |
| 2026 | 10 | 10 | 10 | 0 | 10 | 0 |

### Planning Commission
| Year | Repo | PMN-min | Granicus-min | Recovered | Union | Still-missing |
|---|---|---|---|---|---|---|
| 2020 | 18 | 18 | 18 | 0 | 18 | 0 |
| 2021 | 21 | 21 | 21 | 0 | 21 | 0 |
| 2022 | 18 | 18 | 18 | 0 | 18 | 0 |
| 2023 | 17 | 17 | 18 | 1 | 18 | 0 |
| 2024 | 17 | 17 | 17 | 0 | 17 | 0 |
| 2025 | 20 | 20 | 20 | 0 | 20 | 0 |
| 2026 | 8 | 9 | 9 | 1 | 9 | 0 |

**Result: complete superset OF PUBLISHED MINUTES.** After recovering 7 meetings, every
year × body has **0 still-missing** against both sources — the repo (audited minutes + this
backfill) now equals the union of every minutes DOCUMENT either PMN or Granicus publishes
for Council and PC within the 2020 floor.

> **CORRECTION (2026-07-17, wave2) — the tables above count minutes-DOCUMENTS, which is the
> blind spot the bluffdale-pilot lesson names.** A 2026-07-17 PMN agenda-vs-repo crosscheck
> (see `crosscheck_flags.csv` + CLAUDE.md verification section) surfaced **6 meetings that
> were HELD** (agenda on PMN) **but for which NO minutes document was ever published on
> either source** — so they never entered a "min" column or the "Union" count, yet they are
> genuine held meetings absent from the repo. Each was re-probed against the independent
> Granicus ViewPublisher this wave: **3 have an AgendaViewer but no MinutesViewer link**
> (PC 2022-05-26 clip523, PC 2023-07-27 clip601, PC 2023-08-24 clip608) and **3 do not appear
> in the Granicus archive at all** (Council 2023-05-02, Council 2026-01-06, PC 2026-01-08).
> All 6 are DEAD ends for minutes recovery and are now logged honestly in the core datasets'
> `minutes_unrecovered.csv` (`planning_commission/` 4 rows, `meeting_minutes/` 2 rows) with a
> drafted GRAMA request in the wave report. So: complete superset of *published minutes*, but
> **6 held meetings have no minutes anywhere** — the honest, corrected coverage claim.

## What each diff found

**PMN full-history sweep (body 889 / 5473).** The cumulative `notices.html?id=<body>&page=200`
GET returned each body's entire notice history in one request; attachment **filenames** (not
just the `(Meeting Minutes)` label) were scanned, so `.CC.Min.docx` / `PC.Min.pdf` files
attached under a generic `(Other)`/blank label were still caught. Within the 2020 floor the
sweep surfaced **3 Council** meetings the repo lacks — 2020-01-07, 2020-01-21, 2020-02-04 (the
repo's audited council series starts 2020-02-18; these three January/early-February 2020
meetings sit above the floor but below the repo's first minutes) — and **1 PC** meeting,
2026-06-25 (posted after the repo's last PC harvest of 2026-06-11). All four are recovered
from PMN here.

**Granicus-vs-repo independent diff.** The full ViewPublisher table surfaced **3 additional**
meetings that **PMN never carried minutes for** (PMN has the notice pages, but no minutes
attachment): **Council 2023-09-05, Council 2023-11-07, PC 2023-11-09**. These are exactly the
class of gap the independent-source diff exists to catch — the repo's own PMN-derived harvest
could never have found them because PMN has no minutes file on those dates. Recovered from
Granicus `DocumentViewer.php`.

The two diffs are consistent: neither reported a still-missing core-body date the other
contradicted.
