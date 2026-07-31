# pmn_backfill/ — availability & what was checked (Town of Alta)

**As-of:** 2026-07-13 · Source 4 (`expand-city-sources`), GET-only.

## What was checked

- **Utah Public Notice (`utah.gov/pmn`)**, the full notice history of **all four** Town of
  Alta public bodies (entity id **72**):
  - **1601** Alta Town Council · **1602** Alta Planning Commission ·
    **8621** Budget Committee · **1603** Land Use Appeal Authority.
- Each body's entire notice history pulled in one cumulative GET
  (`notices.html?id=<body>&page=300`). Every minutes attachment was matched by the
  **meeting date parsed from its filename** (not PMN's attachment label — Alta's harvest
  gap was precisely that some minutes are posted under a `Public Information Handout` label
  or filed under the wrong body) against the audited repo indexes, ±4 days.

## What exists / was recovered

- **5 genuinely-missing minutes documents recovered** into `raw/` (+ `text/` sidecars):
  - Town Council: **2020-05-06**, **2020-06-17** (born-digital), **2024-08-14** (scanned →
    OCR; a council meeting mis-filed under PC body 1602).
  - Planning Commission: **2023-11-28** (draft), **2024-04-24** (born-digital).
- All five verified against each PDF's own internal header (body name + date) before
  cataloguing. See `coverage.md` for the per-year tables and the per-file rationale.
- ✅ **PROMOTED 2026-07-16: 4 of the 5** merged into the vote layer
  (`provenance=pmn_minutes` via each dataset's `extract_backfill_votes.py`). **PC
  2023-11-28 was NOT promoted** — its only copy is a pre-approval DRAFT (watermark on
  every page; PDF authored 2024-02-23, before the pre-printed 2024-02-27 approval date);
  it stays a sidecar here and is logged in
  `planning_commission/minutes_unrecovered.csv` (its minutes were approved unamended at
  the audited 2024-02-27 meeting, but the approved version was never posted to PMN).

## What does NOT exist / honest gaps (verified, not filled)

- **PC 2020–2021:** no PC minutes — a real no-business / cancelled-meeting record, directly
  corroborated by PMN cancellation notice **626645** ("Alta Planning Commission – Cancelled
  due to weather", 2020-09-08). Not a harvest miss.
- **Specific cancelled PC meetings:** 2025-06-25 (notice 1005599), 2026-03-25 (notice
  1068103) — cancelled, no minutes, correctly absent.
- **2025 municipal election cancelled/uncontested** (council body notices 990593, 1022301)
  — consistent with the ~380-person electorate.
- **Pre-2020 minutes (2015–2018)** exist on PMN but are **below the 2020 data floor** —
  deliberately out of scope, not recovered.
- **No new still-missing council or PC meeting** remains after this pass (still-missing = 0).

## Not built (inventory only, per task scope)

- **Budget Committee** (body 8621 + council-attached items): ~11 fiscal-subcommittee
  meeting dates 2021→2026 — inventoried in `coverage.md`, **not** recovered as council/PC
  minutes and **not** built into a dataset.
- **Land Use Appeal Authority** (body 1603): its lone minutes attachment duplicates the
  2023-08-09 council meeting already in the repo — 0 net.

## Method / politeness

- All fetches via `scripts/polite_fetch.py` (≥1s/host, retrying, logged to
  `raw/_fetch_log.jsonl` with url/status/bytes/sha256/utc). GET-only; no POST, no CSRF
  search, no auth. Raw HTML + PDFs retained verbatim.
- Born-digital text via `pdftotext -layout`; the one image-only scan via `pdftoppm 300dpi
  + tesseract`, labeled `extraction_method=tesseract-ocr` / `format=scanned`.
- Extracted text corpus passed `screen_corpus.py` clean (no CID/mojibake/PUA/dup-body
  flags; the only hits are advisory `ends_mid` and a benign repeated page-header line).
