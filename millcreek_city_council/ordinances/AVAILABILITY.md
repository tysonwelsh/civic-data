# ordinances/ — availability & gap record (as-of 2026-07-06)

## What exists and was retrieved
- **550 distinct adopted Millcreek ordinances, ORD 2016-01 → 2026**, from the
  **municipalcodeonline.com** publicly-listable S3 back-catalog (bucket
  `municipalcodeonline.com-new`, us-west-2). This is the city's codified-code host and a
  source **independent of the council minutes**.
- **525 raw PDFs retained** on disk (`raw/`, 857 MB, sha256-logged in
  `raw/_fetch_log.jsonl`). **25** oversize (>8 MB) exhibit-bundle ordinances are catalogued
  **index-only** (live `source_url`, not stored) — documented exception, re-fetchable.
- Per-ordinance adoption date + title extracted (text layer / OCR / 6 vision reads) and each
  ordinance joined to the council vote that adopted it (`index.csv`).

Coverage matches the city's real history: Millcreek incorporated Dec 2016, so 2016 is the
floor (9 ordinances) — not a gap. Per-year counts: 2016[9] 2017[57] 2018[72] 2019[57]
2020[56] 2021[53] 2022[49] 2023[46] 2024[59] 2025[50] 2026[42].

## What was checked and is a genuine gap (not fabricated)
- **13 ordinance numbers cited in council motions have NO adopted PDF on the code host**
  (`citations_without_document.csv`): 18-67, 19-09, 21-04, 21-47, 22-35, 22-39, 23-47, 25-20,
  25-23, 25-24, 26-27, 26-32, 26-36. Mostly recent (2025-26) adoptions not yet uploaded by the
  publisher. Recorded, not invented as document rows.
- **120 ordinances are not cited in the vote layer** (`match_confidence=none`) — chiefly
  2016-18 procedural ordinances (budgets, franchises, seals, fee schedules) adopted before the
  ~2022 named-roll-call seam and often referenced in minutes by title rather than number. Their
  dates come from the ordinance PDF itself.
- **28 ordinances are dated to month precision only** (`date_precision=month`) — the day was
  handwritten/illegible on the scan and the month+year printed cleanly; no day was invented.
- **`17-99`** on the host is an **apparent test/template document** ("John Doe/Jane Doe/Betsy
  Ross" voters, a "(joke)" clause, fictitious code cite), not an authentic adopted ordinance —
  flagged in `index.csv` `note`.

## What was NOT collected (scope)
- Full-text sidecars of each ordinance body were **not** produced — only adoption date + title
  were extracted; the raw PDFs are retained for on-demand full-text/vision reading.
- The current consolidated municipal code (Title-by-Title) was not mirrored; this dataset is the
  **adopted-ordinance** layer (number → date → subject → adopting vote), which is what links a
  council "Ordinance YY-NN" vote to what the ordinance did.

## Method integrity
Polite GET-only S3 listing + `polite_fetch.py` (≥1 s/host, logged). No fabrication: unmatched
ordinances keep empty match fields + `match_confidence=none`; citations without a document are
listed, never back-filled.
