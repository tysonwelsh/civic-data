# PMN backfill — availability & method (Midvale City)

**Dataset:** `midvale_city_council/pmn_backfill/` · **As-of:** 2026-07-13 · Source:
**Utah Public Notice** (`https://www.utah.gov/pmn/`), polite GET-only.

> ✅ **PROMOTED 2026-07-16** — 24/25 docs merged into `meeting_minutes/all_votes.csv` (`provenance=pmn_minutes`, 179 motions) via `meeting_minutes/extract_backfill_votes.py`; the 2023-03-30 budget retreat has no motions (honest zero). One label lie corrected at merge: the "RDA Minutes 1-17-2023" doc holds the **2022-12-06** RDA minutes (promoted under the true date; the 2023-01-17 RDA session's own minutes are logged in `meeting_minutes/minutes_unrecovered.csv`). See `CLAUDE.md` (this dir) and the repo `VERIFICATION.md` 2026-07-16 addendum.

## What was checked
- **Entity discovery:** `list/entities.html?id=3&limit=2000` (govType 3 = Municipality) →
  **Midvale entity id = 201** → `list/publicBodies.html?id=201&limit=2000` → **9 public bodies**.
- **Full-history crawl:** cumulative `list/notices.html?id=<body>&page=200` for **every** body
  (the escape hatch around PMN's 6-month list window / POST-only search). 2,124 attachments
  across all bodies parsed from the list HTML.
- **Minutes detection by FILENAME** (not PMN type labels — labels mislabel/under-count):
  341 minutes-like attachments across City Council (183), RDA (91), MBA (19), P&Z (48).
- **Diff by meeting DATE + document count** (±4 days) against the repo's audited indexes for
  Council session and Planning Commission.

## What exists / was recovered
- **14 genuine council-session meeting dates missing from the repo were recovered** (25
  documents: 13 Council/CC, 11 RDA, 1 MBA). Coverage window 2020-2021 (2 dates) and 2022-2025
  (12 dates). The 2024 cluster (Feb, May, mid-March, mid-June, Aug) is the largest real gap.
- Raw PDFs retained verbatim in `raw/` (+ `raw/_fetch_log.jsonl` provenance: url, status,
  bytes, sha256, retrieved_utc). Text sidecars in `text/` (`pdftotext -layout` for born-digital;
  `pdftoppm 300dpi + tesseract` OCR for the 4 scanned 2020-2021 docs, labeled per row in
  `index.csv extraction_method`). Corpus passed `screen_corpus.py` with 0 outliers.

## What does NOT exist / was NOT recovered (honest gaps)
- **Planning Commission: no recoverable gaps.** PC is fully covered in the repo's 2020+ window;
  PMN's PC holdings are essentially all pre-2020. The repo's one PC gap (2024-08-28, corrupt
  scan) is **not on PMN** — remains unrecovered.
- **No born-digital OCR-upgrade for the 2020-2021 seam.** PMN's 2020-2021 Midvale minutes are
  the **same scanned images** (verified: zero text layer on 5 sampled files). Documented in
  `coverage.md`.
- **Pre-2020 record (below floor):** PMN holds ~47 council + ~44 P&Z dates for 2015-2019.
  **Deliberately not recovered** — the repo's data floor is 2020 by design; extending below it
  is a user scope decision, not a gap. Catalogued in `coverage.md`.
- **Harvest Days Committee** minutes (6 docs) are cross-filed under the City Council PMN body
  but are a festival committee, **not** the City Council — not recovered.
- Board of Adjustments, Appeal Authority, and the community councils publish agendas/notices
  only — no minutes.

## Merge status
This is a **separate, review-before-merge** dataset. The audited `meeting_minutes/` and
`planning_commission/` layers were **not modified**. Promoting these 14 dates into the audited
council layer (convert → markdown → `extract_votes.py` → rebuild db/weeks) is a deliberate
follow-up left to the user.
