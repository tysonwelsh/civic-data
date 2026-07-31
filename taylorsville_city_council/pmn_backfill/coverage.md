# Taylorsville — Utah Public Notice (PMN) backfill coverage

**As-of:** 2026-07-06 · **Method:** per-meeting-DATE set-difference (repo `minutes_index.csv`
dates vs PMN `(Meeting Minutes)` attachment dates), matched on the **filename/internal
meeting date** (not the PMN posting date), ±1-day tolerance. Floor 2020.

PMN body ids for Taylorsville (discovered via `/pmn/list/entities.html?id=3` → entity **284**
→ `/pmn/list/publicBodies.html?id=284`):

| PMN body id | Body | Used |
|---|---|---|
| **720** | Taylorsville City Council | cross-checked vs `meeting_minutes/` |
| **722** | Taylorsville Planning Commission | cross-checked vs `planning_commission/` |
| **721** | Redevelopment Agency of Taylorsville City Board | cross-checked (RDA folds into council meetings — 0 gaps) |
| 2770 | Community Development and Renewal Agency of Taylorsville | 3 notices, **0** minutes attachments |
| 2523 | Taylorsville Board of Adjustment (Inactive) | not a repo body |
| 3379 | Taylorsville Board of Canvassers | not a repo body |
| 2871 | Taxing Entity Committee | not a repo body |
| 6931 | Taylorsville City Recorder's Office | not a repo body |

The repo is a near-perfect **superset** of PMN (the city portal is the primary source and
carries briefings/priorities/truth-in-taxation docs PMN often omits). PMN adds only **2**
genuinely-missing meetings, both **Let's Talk Taylorsville** 5th-Wednesday town halls.

## Council (PMN body 720) vs `meeting_minutes/`

| Year | Repo minutes | PMN minutes-dates | Genuine gap | Recovered |
|---|---|---|---|---|
| 2020 | 23 | 25 | 1 (2020-01-29) | 1 |
| 2021 | 25 | 23 | 0 | 0 |
| 2022 | 25 | 23 | 0 | 0 |
| 2023 | 21 | 20 | 0 | 0 |
| 2024 | 23 | 24 | 1 (2024-01-31) | 1 |
| 2025 | 22 | 16 | 0 | 0 |
| 2026 | 11 | 9 | 0 | 0 |

## Planning Commission (PMN body 722) vs `planning_commission/`

| Year | Repo minutes | PMN minutes-dates | Genuine gap | Recovered |
|---|---|---|---|---|
| 2020 | 11 | 12 | 0 | 0 |
| 2021 | 12 | 10 | 0 | 0 |
| 2022 | 15 | 15 | 0 | 0 |
| 2023 | 15 | 16 | 0 | 0 |
| 2024 | 15 | 14 | 0 | 0 |
| 2025 | 16 | 13 | 0 | 0 |
| 2026 | 7 | 6 | 0 | 0 |

**Planning Commission: 0 genuine gaps.** RDA body 721: 25 minutes-dates 2020+, all coincide
(±1d) with a council meeting already in the repo (the RDA convenes in-recess during council
meetings) — 0 separate documents to recover.

## Flagged candidates — resolution (every set-difference hit, verified at source)

The raw date set-difference surfaced 6 council + 1 PC candidates. Reading each PDF's
**internal** header date (PMN filenames are frequently mislabeled) resolved all but two as
duplicates of meetings already in the repo:

| Flagged as | PMN file | Internal header date | Verdict |
|---|---|---|---|
| Council 2020-01-06 | 676899 (`...1-6-20.pdf`) | **January 6, 2021** | already in repo (2021-01-06) — filename year typo |
| Council 2020-01-29 | 569847 (`...01_29_20.pdf`) | January 29, 2020 (Town Hall) | **RECOVERED** — genuinely missing |
| Council 2020-09-06 | 1022115 (`...9-6-20.pdf`) | **September 6, 2023** | already in repo (2023-09-06) — scanned; filename year typo |
| Council 2020-10-16 | 644559 (`...10-16-20.pdf`) | **September 16, 2020** | already in repo (2020-09-16) — filename typo |
| Council 2024-01-31 | 1086765 (`...1-31-24.pdf`) | January 31, 2024 (Town Hall) | **RECOVERED** — genuinely missing |
| PC 2020-02-12 | 620783 (`02-12-2020.pdf`) | **May 12, 2020** | already in repo (2020-05-12) — filename typo |

## Recovered files (see `index.csv`)

| Date | Title | Body | Format | PMN file |
|---|---|---|---|---|
| 2020-01-29 | Let's Talk Taylorsville Town Hall | Council | born-digital text | 569847 |
| 2024-01-31 | Let's Talk Taylorsville Town Hall | Council | scanned (OCR) | 1086765 |

Both are **5th-Wednesday informal constituent town halls** (`Let's Talk Taylorsville`) —
NON-STANDARD sessions with no formal roll-call voting. A third town hall (2024-07-31) exists
on PMN but is **already in the repo**, so it was not recovered.

## Still-missing / not recovered

None beyond the resolved false-positives above. The two town halls are recovered here as a
**separate, review-before-merge dataset** — the audited `meeting_minutes/` layer was not
modified.

## OCR-upgrade candidates (born-digital replacements for RICOH scans)

See `ocr_upgrade_candidates.csv`. Taylorsville switched to RICOH-scanned minutes production
(repo `format=ocr`: 24 council + 31 PC files). For **15** of those meetings (5 council, 10
PC), PMN hosts a **born-digital text-layer PDF of the same meeting** (internal date verified
to match). These are flagged as OCR-upgrade candidates — a cleaner text source than the
scanned copy in the repo. **Do NOT replace in place**; a human reviews. Note 7 of the 10 PC
candidates are DRAFT minutes (the repo has the APPROVED scan), so a reviewer may prefer them
only as a searchable text sidecar. The remaining scanned repo meetings have either no PMN
copy or a PMN copy that is itself scanned (no upgrade available).
