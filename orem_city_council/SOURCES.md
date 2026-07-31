# Sources — Orem civic data

Civic records of the Orem City Council and Planning Commission, 2020–present. The city's official minutes archive is a public Google Drive folder linked from orem.gov/meetings; newer meetings are on the CivicClerk portal (oremut.api.civicclerk.com). Written public comments appear only inside council minutes. Election results are produced by the Utah County Clerk (vote.utahcounty.gov).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py orem`.

## Council meeting minutes

- **Published by:** Orem City Recorder
- **Portal:** Google Drive archive (drive.google.com) + CivicClerk (oremut)
- **Documents indexed:** 135  ·  **Date range:** 2020-01-14 to 2026-06-23
- **Direct source URLs recorded:** 135/135 (100%)  ·  **Host(s):** drive.google.com, oremut.api.civicclerk.com
- **How the text was obtained:** ocr (73), text (62)
- **Note:** Mix of born-digital and scanned (OCR) documents.

## Planning Commission minutes

- **Published by:** Orem Development Services / Planning Commission
- **Portal:** Google Drive archive + CivicClerk (oremut)
- **Documents indexed:** 114  ·  **Date range:** 2020-01-15 to 2026-05-06
- **Direct source URLs recorded:** 114/114 (100%)  ·  **Host(s):** drive.google.com, oremut.api.civicclerk.com
- **How the text was obtained:** text (91), docx (17), ocr (6)
- **Note:** Mix of born-digital, .docx and OCR documents.

## Public comments

- **Published by:** Orem City Recorder (via council minutes)
- **Portal:** Google Drive archive + CivicClerk
- **Documents indexed:** 9  ·  **Date range:** 2020-07-14 to 2021-03-23
- **Direct source URLs recorded:** 9/9 (100%)  ·  **Host(s):** drive.google.com
- **How the text was obtained:** transcribed from minutes text (9)
- **Note:** Orem publishes no separate comment compilations; written comments read into the record live inside the cited minutes documents.

## Municipal election results

- **Published by:** Utah County Clerk
- **Portal:** vote.utahcounty.gov
- **Documents indexed:** 9  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 9/9 (100%)  ·  **Host(s):** vote.utahcounty.gov
- **How the text was obtained:** pdf (raw retained verbatim) (5), csv (raw retained verbatim) (4)
- **Note:** County SOVC CSVs / results PDFs mirrored verbatim in election_results/raw/; live URLs recorded in election_results/CLAUDE.md for 6 of 9 files.

## Agenda packets / staff reports

- **Documents indexed:** 429  ·  **Date range:** 2021-07-13 to 2026-07-15
- **Direct source URLs recorded:** 429/429 (100%)  ·  **Host(s):** oremut.api.civicclerk.com
- **How the text was obtained:** civicclerk_odata (429)

## Housing plans / general plan

- **Documents indexed:** 14  ·  **Date range:** 2018-09-12 to 2026-07-05
- **Direct source URLs recorded:** 14/14 (100%)  ·  **Host(s):** jobs.utah.gov, orem.gov
- **How the text was obtained:** pdftotext-layout (7), ocr-tesseract (6), none (1)

## Ordinances (adoption record)

- **Documents indexed:** 100  ·  **Date range:** 2020-01-14 to 2026-07-14
- **Direct source URLs recorded:** 100/100 (100%)  ·  **Host(s):** drive.google.com, orem.gov, oremut.api.civicclerk.com
- **How the text was obtained:** reconstructed from meeting_minutes/all_votes.csv motion text (Orem minutes assign no ordinance number) (via minutes document) (92), extracted from orem.gov WordPress 'City Council Ordinance' post (born-digital HTML) (4), orem.gov WordPress ordinance post (independent, number-bearing) cross-matched to the council adoption motion by meeting date + distinctive code-section/subject tokens (4)

## Utah Public Notice backfill

- **Documents indexed:** 38  ·  **Date range:** 2020-03-10 to 2026-05-26
- **Direct source URLs recorded:** 38/38 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (19), ocr-tesseract (15), docx-xml (4)

## Meeting-video transcripts

- **Documents indexed:** 108  ·  **Date range:** 2016-01-12 to 2025-06-24
- **Direct source URLs recorded:** 108/108 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** mapped_not_downloaded_sample_only (98), yt-dlp --write-auto-sub (en-orig vtt) (10)

## Campaign-finance disclosures

- **Documents indexed:** 91  ·  **Date range:** 2023-01-10 to 2026-01-10
- **Direct source URLs recorded:** 91/91 (100%)  ·  **Host(s):** orem.gov
- **How the text was obtained:** ocr:tesseract (50), pdftotext -layout (41)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
