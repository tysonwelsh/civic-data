# ordinances/ — availability, gaps, and defects

As-of **2026-07-06**. Method + confidence semantics: `CLAUDE.md`.

## What South Jordan publishes
- **Codified code:** `southjordan.municipalcodeonline.com` (Municipal Code Online), mirrored at
  `library.municode.com/ut/south_jordan`. Current consolidated text only.
- **Adopted-ordinance back-catalog:** YES, and unusually complete — the code host's S3 bucket
  (`s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/southjordan/ordinances/documents/`)
  is **publicly listable** and holds **213 distinct adopted-ordinance PDFs spanning 1997-2026**.
  Enumerated in full → `archive_backcatalog.csv`. Most 2016+ files are signed image scans.

## What it does NOT publish (honest gaps — GAPS ARE DATA)
1. **The zoning/rezone series (`YYYY-NN-Z`) is not posted to the code host.** The S3 bucket
   carries only the **general** series. All **35** `-Z` rezone ordinances cited in council
   motions are therefore `within_source` (motion-derived, not independently corroborated). Their
   text exists only inside the meeting minutes / (potentially) agenda packets. Flag, not a miss.
2. **43 general ordinances cited in motions are not (yet) in the S3 archive** (upload lag —
   heaviest for 2025-2026 and a cluster of 2022-2023). Also `within_source`.
3. **"Recent Council Action / Notice of Ordinance Adoption & Summary" PDFs** — the city posts
   these annually (e.g. DocumentCenter `View/7002` "2024 Recent Council Action", `View/8099`
   "2025..."), but **all bare `DocumentCenter/View/<id>` IDs returned 404 on 2026-07-06**
   (CivicPlus renumbers doc IDs; the current slugged URLs were not surfaced from the City Code
   page, which only links the code host). Not used — the S3 adopted PDFs are a stronger
   independent corroboration source anyway. Retrievable later if the current IDs are found.

## Coverage seams
- **`index.csv` is 2020+ only** (the repo's minutes floor). The 161 pre-2020 archived
  ordinances are in `archive_backcatalog.csv` (`in_minutes_window=no`), index-only.
- **5 `none` rows** (`2020-01, 2020-02, 2020-07, 2020-08, 2020-11`) are real adopted ordinances
  whose signed-PDF adoption dates (2020-01-07 … 2020-08-04) **predate the first minutes document
  on disk (2020-08-18).** They cannot link to a vote because the meeting isn't in the repo — a
  coverage seam at the minutes floor, consistent with recon (2020 backfill was time-boxed).
- **7 `low` rows** (`2021-09, 2024-01, 2024-08, 2024-10, 2024-12, 2024-17, 2024-24`) were adopted
  on dates that DO match a recorded council meeting, but no motion prints the ordinance number
  (adopted via consent / non-numbered motion). Date-only linkage; `matched_motion_no` left blank.

## Data-quality defects found in the source (recorded, not corrected)
- **Ordinance 2026-15 EXCLUDED from `index.csv`.** The S3 file named `..._ORDINANCE 2026-15_FINAL.pdf`
  is internally inconsistent: page-1 title reads "AMENDING SECTION 16.04.320 … WATER SHARE
  EXACTIONS" while the signature-page footer reads **"Ordinance 2026-12."** The city mis-labeled
  the upload; the true 2026-15 text is not confirmed. Retained in `archive_backcatalog.csv` only.
- **Duplicate S3 objects** (same bytes, different upload timestamps): `2021-13` (×2), `2020-15`,
  `2026-11` (×3), `2026-12` (×2), `2026-04` (×3), `2026-13`… Deduped by ordinance number when
  building `archive_backcatalog.csv` (226 raw keys → 213 distinct); first key retained.
- Older filenames use `97-1` / `98-17` / `1999-9` forms and embedded adoption dates
  (`01-07-1997 Ordinance 97-1.pdf`); normalized to `1997-01` etc. in `ordinance_no`.

## Verification performed
- S3 prefix fully paginated (continuation tokens) → 226 keys, 213 distinct ordinances.
- All 52 in-window (2020+) general PDFs fetched via `polite_fetch.py` (all HTTP 200; logged in
  `raw/ordinances_archive/_fetch_log.jsonl`).
- Handwritten adoption dates for the 12 archived-but-uncited in-window ordinances read by vision
  from signature pages (OCR could not resolve the handwriting).
- Text corpus (`text/`, 18 files) screened with `audit-city-data/scripts/screen_corpus.py`:
  0 read errors, 0 dict_ratio / split_word / weird_char outliers.
- `validate_dataset.py ordinances` → **PASS**.
