# PMN backfill — availability & gap record

As-of **2026-07-03**. Source: Utah Public Notice website (PMN), `https://www.utah.gov/pmn/`.

## What was checked
Cumulative notice history (single GET, `/pmn/list/notices.html?id=<body>&page=500`) for
every Provo public body relevant to meeting minutes:

| body | PMN id | notices | minutes-equivalent attachments |
|---|---|---|---|
| Provo Municipal Council | **1600** | 1,589 (…→2026-06-23) | 468 `Minutes` + 268 `Summary` |
| Provo City Planning Commission | **1662** | 365 (2008-10-08→2026-07-08) | 569 per-item `Report of Action` (ROA) |
| Redevelopment Agency Governing Board | **2318** | 174 (2009→2026) | duplicates Council content (same body) |

Body ids discovered via the GET chain `entities.html?id=3` (govType 3 = Municipality) →
Provo **entity id 244** → `publicBodies.html?id=244` (lists all 28 Provo bodies + ids).
Body ids are assigned globally, confirmed by lookup, not guessed.

## What exists on PMN and was RECOVERED (see index.csv, coverage.md)
- **Council: 8 special-meeting minutes** (retreats + joint meetings) absent from the repo's
  OnBase regular-meeting archive — all content-verified genuine Municipal Council minutes.
- **Planning Commission: 92 meeting dates** (382 per-item ROA PDFs) — the repo's PC record
  is 2025+ only, so this backfills the entire **2020–2024** PC backlog (70 dates) + 4 extra
  2025–2026 dates. Each ROA is a structured, vote-bearing action record.
- Total **390 files, 111 MB, all born-digital text** (0 scanned).

## What is NOT recovered / NOT missing (honest gaps)
- **Recent-year Council minutes on PMN are FEWER than the repo** (e.g. 2024: PMN 23 vs repo
  27; 2025: PMN 19 vs repo 26). That is a **PMN publishing lag**, not a repo gap — the repo
  already holds those regular Council meetings from OnBase. Nothing to recover; noted so the
  per-year counts aren't misread.
- **RDA (body 2318)** was crawled but NOT separately recovered: the RDA Governing Board is the
  Municipal Council sitting as the RDA, so its posted minutes/summaries duplicate council
  content already in the repo. No unique RDA minutes gap found.
- **PC agendas / agenda packets on PMN** (153 agenda + 19 packet attachments) were catalogued
  but not indexed as recoveries — agendas are a weaker record than the ROA minutes-equivalent,
  and every PC date we recovered already carries its ROA action record. No PC date had an
  agenda-only gap requiring agenda fallback.
- **Pre-2020 history** exists on PMN (PC back to 2008, council/RDA to ~2009/2014) but is
  **out of repo scope** (data floor = 2020) and was not recovered.

## After backfill
**0 minutes-bearing dates on PMN remain missing** from this repo (council or PC), within the
2020-present scope. Still-missing = 0 in every year (coverage.md).

## Caveats on the recovered PC ROA docs
- PMN PC minutes take the form of **per-item "Report of Action" PDFs**, not one consolidated
  minutes document per meeting (unlike the repo's 2025+ AgendaCenter PC minutes). One meeting
  date = several ROA files. The index has one row per file.
- 1 file (`pc_2020-02-26_item4_580761.pdf`) is a **code-section exhibit** bundled under an
  "Item 4 ROA" label, not an action record (`doc_kind=roa_supporting`); the real Item-4 action
  record for that date (fid 580771) is also present.
- 2 files are **byte-identical source re-posts** (`doc_kind=roa_duplicate`): 580757 (=580755),
  1147261 (=1147257). Retained (both were posted) but flagged so downstream doesn't double-count.
