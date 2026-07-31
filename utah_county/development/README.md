# utah_county / development — the development-applications pipeline

`applications.csv` — one row per substantive **land-use development action** that came before
the Utah County Planning Commission (rezone / general-plan-and-zone-map amendment /
conditional-use permit / subdivision-plat / UCLUO ordinance text amendment / agriculture
protection area), reconstructed from the PC minutes. Modeled on
`salt_lake_county/development/applications.csv` (same base columns) with land-use extensions.

## Columns

`date, body, dev_type, title, matter, location, outcome, names_recorded, motion_id,
minutes_path, applicant, from_zone, to_zone, motion_no`

- `dev_type` — `rezone | general_plan_amendment | conditional_use | subdivision |
  ordinance_text_amendment | plat | other_land_use` (`other_land_use` = agriculture
  protection areas etc.).
- `matter` — the county file/case number where printed (e.g. `CU2025-05`, a Board of
  Adjustment appeal number); blank when the source printed none.
- `outcome` — the PC's action, verbatim-ish: `Recommend approval` / `Recommend denial` /
  `Approved` / `Denied` / `Continued to <date>` / `Withdrawn by applicant` / `Decision
  withheld …`. (The PC *recommends* on rezones/GP/text amendments — the Commission decides —
  but *approves/denies* conditional-use permits directly.)
- `from_zone` / `to_zone` — printed zoning where the item is a map amendment; blank otherwise.
- `applicant` — applicant/agent name(s) as printed.
- `motion_no` — the deciding motion within that meeting's `motions_tally.csv`
  (`(date, motion_no)` join). `motion_id` is left blank for the closing db pass to resolve to
  a global motion id at ingest.
- `minutes_path` — the source minutes markdown (relative to `utah_county/`); every row cites
  its source meeting.

## Provenance & scope

Built entirely from the **11 vision-extracted PC minutes, 2025-01 → 2026-05** (see
`../land_use/SOURCES.md`). **32 actions**: 15 ordinance text amendments, 11 conditional-use
permits, 3 general-plan/zone-map amendments, 1 rezone, 2 agriculture protection areas.
Outcomes: 15 recommend-approval, 9 approved (CUPs), 4 continued, 2 withdrawn, 1
decision-withheld, 1 application-withdrawn.

**Not yet covered**: the pre-2025 pipeline. The 2020–2024 PC minutes are catalogued in the
county CMS but its media host is offline (NXDOMAIN 2026-07-20), and 2015–2019 is PMN
agenda-only. When those minutes become retrievable, extend this file the same way. There is
**no online case log** for Utah County land-use applications — the county publishes the
application *forms* as blank templates only — so the minutes are the authoritative pipeline
source. Honest blanks (`matter`, `from_zone`/`to_zone` where the source printed none) are data.
