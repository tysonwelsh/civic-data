# pmn_backfill/ — availability (Town of Copperton, Source 4)

**As-of:** 2026-07-14 · **Verdict:** the audited repo is a **complete superset** of Utah
Public Notice for both Copperton bodies. **0 gap-fill minutes recovered.** The dataset's
only tangible artifact is **1 OCR-upgrade lead** (2025-10-15, born-digital, not swapped).

## What was checked

- **PMN entity discovery (GET-only):** Copperton = municipality **entity 1353** (govType 3).
  Its public bodies: **Council 5831** + **Planning Commission 1560** — the only two. All
  govTypes swept for Copperton-named entities: the sole extra is govType-5 **entity 482,
  Copperton Improvement District** (a water district — **DECOY, excluded**). No CRA/RDA/other
  body exists.
- **Full-history crawl** of bodies 5831 (207 notices) and 1560 (253 notices) via the
  cumulative `notices.html?id=<body>&page=500` GET trick; minutes detected by FILENAME +
  CONTENT (PMN type labels are unreliable), diffed per meeting-date (±4d) against the repo's
  `meeting_minutes/minutes_index.csv` (106 docs) and `planning_commission/minutes_index.csv`
  (17 docs).

## What exists / was recovered

- **0 council recoveries** — all 32 PMN council minutes dates already indexed.
- **0 PC recoveries** — all 17 PMN PC minutes dates already indexed; the lone "extra" PMN
  date (2025-07-02) is a FALSE POSITIVE (it is the May-13-2025 minutes copy, already held).
- **1 OCR-upgrade lead** — 2025-10-15 council DRAFT (PMN file 1353103), born-digital
  (16,436 chars), for a date the repo holds only as a GoDaddy RICOH scan. Retained in
  `raw/`, cataloged in `index.csv` (`recovery_source=pmn_ocr_upgrade_lead`), **NOT swapped**
  into the audited minutes. See `coverage.md` §angle (c) for the full 15-date evaluation.

## What does NOT exist (honest gaps — PMN cannot fill them)

- **2017-02-15 → 2018-06-20 council (29 meetings)** — a genuine PMN **retention purge**.
  RE-CONFIRMED 2026-07-14: 9 purge-era minutes file-IDs sampled across the whole window all
  return 315-byte HTTP-404 stubs; 3 live controls (459667/459671/522659) return real PDFs.
  Stays a gap; `meeting_minutes/minutes_unrecovered.csv` unchanged.
- **Sep-2025 (2025-09-17), Dec-2025 (2025-12-09/17), June-2026 (2026-06-17) council** — PMN
  has the agenda notices (meetings happened) but **no minutes document** was ever posted.
  RE-CONFIRMED unfillable from PMN.
- **2025-07-02 PC** — meeting held (agenda + staff report present) but its own minutes never
  posted (subsequent PC meetings cancelled). Nothing to recover.

## Rules honored

Additive/review-only; the audited `meeting_minutes/` / `planning_commission/` / `db/` /
`weeks/` layers were not touched; raws retained (`raw/` + `_fetch_log.jsonl`); nothing
fabricated (both the purge gap and the minor 2025/2026 gaps stay gaps; the OCR lead is a
lead, not a swap); polite GET-only. Parent `README.md`/`CLAUDE.md`, `sources.csv`,
`cities.db`, `coverage.json`, `TODO.md` are owned by the orchestrator — not edited here.
