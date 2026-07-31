# pmn_backfill — what was checked, what exists, what doesn't (as-of 2026-07-13)

## Source and method
- **Source:** Utah Public Notice Website, `https://www.utah.gov/pmn/` — the statewide
  statutory notice repository. GET-only, throttled via `polite_fetch.py` (provenance in
  `raw/_fetch_log.jsonl`: url, status, bytes, sha256, retrieved_utc for every file).
- **Body-id discovery:** `/pmn/list/entities.html?id=3&limit=2000` (govType 3 =
  Municipality) → **Murray = entity 213** → `/pmn/list/publicBodies.html?id=213&limit=2000`.
  Murray public bodies found (ids are global, never guessed):

  | PMN body | id | used |
  |---|---|---|
  | **Municipal Council** | **735** | yes — council backfill |
  | **Planning and Zoning Commission** | **983** | yes — PC backfill |
  | Redevelopment Agency | 987 | inventoried only |
  | Municipal Building Authority of Murray City | 6863 | inventoried only |
  | Murray City Center District (MCCD) Design Review Committee | 977 | inventoried only |
  | Board of Canvassers / Elections | 2482 | no |
  | Budget and Finance Committee | 8653 | no (its minutes also appear under 735) |
  | City School Coordinating Council | 8101 | no (minutes also appear under 735) |
  | Public Notices & Ordinances | 7321 | no (ordinance-notice archive — a lead for a future `ordinances/` dataset) |
  | City Recorder | 2442; plus ~15 advisory boards/committees | no |

- **Crawl:** the cumulative list GET `/pmn/list/notices.html?id=<body>&page=200`
  (one request per body returns the entire notice history; the "past 6 months" banner
  applies to page 1 only). Attachment-type labels (`(Meeting Minutes)`, `(Other)`,
  `(Audio Recording)`, …) parsed from the list HTML — notice pages were not crawled
  individually. Inventory: 1,045 council notices (2013→2026, minutes attachments from
  2014), 468 PC notices (2008→2026), 263 RDA, 44 MBA, 134 MCCD.
- **Cross-check:** per-meeting-date set difference (±4 days) against
  `meeting_minutes/minutes_index.csv` and `planning_commission/minutes_index.csv`,
  plus every row of `meeting_minutes/minutes_unrecovered.csv`.

## What exists on PMN (and what this dataset recovered)
- **2023 council minutes — the Tyler-TMM gap is FULLY recoverable on PMN.** All 18
  `minutes_unrecovered.csv` dates resolve: 17 approved council-meeting minutes recovered;
  **2023-07-11 was cancelled** (official cancellation notice retained,
  `raw/council_2023-07-11_996949.pdf`) — no minutes ever existed for it. PMN also
  surfaced a **net-new 2023-08-21 Special Council Meeting** (joint with Millcreek City
  re: Murray North Station) absent from the repo index and the unrecovered log — recovered.
- **PC minutes 2023-01-05 → 2026-05-07 — the "PC ends 2022-11" gap is essentially fully
  recoverable on PMN.** 59 PC minutes recovered (17 × 2023, 19 × 2024, 17 × 2025,
  6 × 2026). All other 1st/3rd-Thursday dates 2023–2025 are officially-noticed
  cancellations (see `coverage.md`), except the two honest gaps below.
- All repo-held council dates 2020–2026 are duplicated on PMN (not re-fetched — the repo
  copies are born-digital already).

## What does NOT exist (honest gaps — verified, not fabricated)
- **2025-04-17 PC minutes** — agenda noticed on PMN, no minutes attachment anywhere
  (checked the full body-983 history). The meeting apparently occurred; its minutes are
  simply not on PMN (nor on the CivicPlus archive, which ends 2022-11-17).
- **2025-07-17 PC minutes** — PMN's attachment named "2025.07.17 Planning Commission
  Meeting Minutes.pdf" is **actually the 2-page agenda** (content-verified 2026-07-13).
  Retained honestly labeled (`status=pmn-mislabeled-agenda`); the minutes themselves are
  not on PMN.
- **2026 PC minutes after 2026-05-07** — 2026-02-05, 2026-05-21, 2026-06-18, 2026-07-02
  are agenda-only as of retrieval (recent meetings; Murray posts PC minutes after
  approval, one–two meetings later). 2026-02-05 is old enough that it may be a genuine
  publication miss — re-probe on the next refresh.
- **2022-06-21 council born-digital upgrade** — the repo's single OCR council file was
  tested against PMN's copy of the same minutes (`raw/council_2022-06-21_872275.pdf`):
  the PMN copy is **also an image-only scan** (0 extractable chars). No born-digital
  copy exists on PMN; the repo's Tesseract OCR remains the best text. Upgrade rejected.
- **2025-06-19 PC** — never noticed on PMN at all (likely no meeting scheduled);
  2024-07-04 likewise (holiday).

## Noted but deliberately NOT fetched (out of scope)
- **PC OCR-upgrade candidates:** the repo's 2020–2021 PC minutes are OCR; PMN carries PC
  minutes attachments for 7 of those dates (2020-10-15, 2020-11-05, 2020-11-19,
  2020-12-17, 2021-07-15, 2021-10-07, 2021-12-16) whose format is **unverified** (the
  2022-06-21 council test above suggests Murray uploaded scans in that era). Candidates
  for a future OCR-upgrade pass.
- **Committee of the Whole minutes** (posted under council body 735): PMN holds COW
  minutes for essentially every 2023 council date plus scattered 2022/2025/2026 dates.
  The repo has no COW dataset (CivicPlus AMID=45 also holds them) — a future new-body
  dataset, not a backfill of an existing one.
- **Council workshops / town halls / Budget & Finance / City School Coordinating
  Council minutes** under body 735 (2020–2026): e.g. 2020 Legislative Breakfast &
  budget meetings, 2021 Mixed-Use Workshop & MCCD Walking Tour, 2022 Property-Tax Town
  Hall, 2023-02-15 Council Initiatives Workshop, 2023 budget-review minutes,
  2024-08-27 Short-Term-Rentals Workshop, 2025-07-28 and 2026-02-05 workshops,
  2026 COW minutes. Inventoried in the crawl; none belong to the audited
  council-regular-meeting series.
- **RDA (987), MBA (6863), MCCD Design Review (977) minutes** — see `coverage.md` for
  per-year counts; the repo has no datasets for these bodies.

## Reproducibility
Raw list-HTML snapshots and the parsed inventory live in the session scratchpad only;
re-run discovery with the three GETs above (entity 213). Every fetched file's provenance
is in `raw/_fetch_log.jsonl`; the selection logic and content-verification results are
described in `CLAUDE.md`.
