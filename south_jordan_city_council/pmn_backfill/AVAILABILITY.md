# PMN backfill — availability record

**As-of:** 2026-07-06. **Method:** Utah Public Notice (utah.gov/pmn) cumulative crawl.

## What was checked
- Entity discovery: `list/entities.html?id=3` → South Jordan **entity id 269** →
  `list/publicBodies.html?id=269` (saved `_disco/entities.html`, `_disco/bodies.html`).
- Cumulative notice history (`notices.html?id=<body>&page=300`, one GET = full history) for
  **City Council (1031)**, **Planning Commission (1032)**, **Redevelopment Agency (3901)**,
  **Municipal Building Authority (5015)**. Saved `_disco/notices_<id>.html`.
- Parsed every `(Meeting Minutes)` attachment → `_disco/pmn_minutes_all.csv` (711 rows,
  2014–2026).
- Date set-difference (±4 days) against `meeting_minutes/minutes_index.csv` (135 dates) and
  `planning_commission/minutes_index.csv` (122 dates).

## What exists and was recovered
- **13 City Council minutes documents / 8 meeting dates** missing from the repo, all fetched
  to `raw/` and text-extracted (`text/`). See `coverage.md` and `index.csv`. These fill the
  Jan–Feb + Jul 2020 gap and one 2023-01-24 budget meeting.

## What exists but was NOT recovered (deliberate)
- **Pre-2020 minutes** (Council ~158 dates 2014–2019; PC ~88 dates 2015–2019; scattered
  RDA/MBA). Below the repo's 2020 data floor — out of scope for a gap-fill; catalogued in
  `coverage.md` for a future floor-extension decision. All ids in `_disco/pmn_minutes_all.csv`.
- **2 combined-meeting minutes** filed under the PC body (2023-03-07, 2024-09-17) — already on
  disk under `meeting_minutes/` (combined CC&PC meetings). Not duplicated.

## What genuinely does not exist (honest gaps, unrecovered)
- **South Jordan council March–June 2020** — meetings held as electronic meetings (PMN
  notices present) but **no minutes were ever posted** (agenda/handout only). Not on CivicPlus
  (starts 2021) or Municode (starts 2022). Logged in `unrecovered.csv`.
- **PC 2020-04-14, 2020-04-28, 2020-08-11** — already logged in the repo's
  `planning_commission/minutes_unrecovered.csv` (agenda-only electronic meetings); PMN crawl
  confirms no minutes attachment. Not re-logged here.

## Reconciliation note (existing layer untouched, per instructions)
The 13 recoveries contradict `meeting_minutes/minutes_unrecovered.csv` (which was built off the
PMN 6-month list view and missed the cumulative history). The existing minutes layer was **not
modified**. See `coverage.md` §Reconciliation for the exact rows and the merge action left to
the user.
