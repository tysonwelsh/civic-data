# Taylorsville PMN backfill — availability & what was checked

**As-of:** 2026-07-06

## What this dataset is
Utah Public Notice (`utah.gov/pmn`) is the statewide public-notice repository; every
Taylorsville public body mirrors its agendas/minutes there. This dataset is the **gap-log +
recovered files** from cross-checking PMN against the already-built `meeting_minutes/` and
`planning_commission/` layers. It is **purely additive** — the audited minutes layer was NOT
modified.

## What was checked
- **Body discovery** (not guessed): `/pmn/list/entities.html?id=3&limit=2000` (govType 3 =
  Municipality) → Taylorsville **entity id 284** → `/pmn/list/publicBodies.html?id=284` →
  8 public bodies. Confirmed council = **720**; discovered PC = **722**, RDA = **721**,
  CDRA = **2770** (+ inactive Board of Adjustment 2523, Canvassers 3379, Taxing Entity 2871,
  Recorder 6931).
- **Full history per body** via the cumulative GET `/pmn/list/notices.html?id=<body>&page=300`
  (the escape hatch around PMN's 6-month list / POST-only search): 864 council notices,
  481 PC, 131 RDA, 3 CDRA. Filtered to `(Meeting Minutes)` attachments.
- **Per-DATE set-difference** vs the repo indices, keyed on each attachment's **internal /
  filename meeting date** (PMN posting dates lag and PMN often attaches the *previous*
  meeting's minutes; filenames are also frequently mis-dated — so every set-difference hit
  was opened and its PDF header date read before a verdict).

## What exists / was recovered
- **2 genuinely-missing council meetings recovered** → `raw/` + `index.csv`: the
  **2020-01-29** and **2024-01-31** *Let's Talk Taylorsville* 5th-Wednesday town halls
  (NON-STANDARD informal sessions, no formal roll-call votes). Neither is on the city portal
  or in `meeting_minutes/minutes_index.csv`.
- **15 OCR-upgrade candidates** (`ocr_upgrade_candidates.csv`): PMN born-digital text PDFs
  for meetings the repo holds only as RICOH scans (`format=ocr`). Flagged, not merged.

## What does NOT exist / is not a gap
- **Planning Commission: 0 genuine gaps** vs PMN. The repo is complete.
- **RDA (721): no separate documents.** RDA minutes-dates all coincide with a council meeting
  already in the repo (RDA convenes in-recess mid-council-meeting; consistent with the repo's
  `body=RDA` in-record modeling). **CDRA (2770): 0 minutes attachments.**
- **4 other set-difference hits were false positives** — mislabeled PMN filenames whose
  internal dates (2021-01-06, 2023-09-06, 2020-09-16, 2020-05-12 PC) are already in the repo.
  See `coverage.md` for the per-file resolution table.
- The repo is otherwise a **superset** of PMN (the CivicEngage city portal is primary and
  additionally carries briefings, city-priorities, and truth-in-taxation docs PMN omits).

## Provenance
All fetches through `scripts/polite_fetch.py` (browser UA; PMN throttled GET-only);
`raw/_fetch_log.jsonl` records url/status/bytes/sha256/retrieved_utc for each recovered PDF.
