# Sources — Ogden civic data

Civic records of the Ogden City Council (with RDA/MBA sessions) and Planning Commission, 2020–present. Minutes are published on the city's CivicPlus site (ogdencity.gov DocumentCenter) — 2020–2023 as annual compilation PDFs, 2024+ per meeting. Ogden publishes no written public-comment compilations. Election results come from Weber County Elections (weberelections.gov) and, for gaps, the Utah state Enhanced Voting portal.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py ogden`.

## Council meeting minutes

- **Published by:** Ogden City Recorder
- **Portal:** CivicPlus DocumentCenter (ogdencity.gov)
- **Documents indexed:** 505  ·  **Date range:** 2020-01-07 to 2026-06-30
- **Direct source URLs recorded:** 505/505 (100%)  ·  **Host(s):** www.ogdencity.gov
- **How the text was obtained:** compilation (304), per-meeting (201)
- **Note:** 2020–2023 meetings extracted from annual compilation PDFs (source_url points at the year compilation); 2024+ per-meeting PDFs.

## Planning Commission minutes

- **Published by:** Ogden Planning Division
- **Portal:** CivicPlus (ogdencity.gov)
- **Documents indexed:** 140  ·  **Date range:** 2020-01-08 to 2026-06-17
- **Direct source URLs recorded:** 140/140 (100%)  ·  **Host(s):** brand.ogdencity.com, www.ogdencity.gov
- **How the text was obtained:** text (89), ocr (51)
- **Note:** Mix of born-digital and scanned (OCR) PDFs.

## Public comments

- **Published by:** —
- **Portal:** —
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Ogden publishes no written public comments (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Weber County Elections; Utah Enhanced Voting portal (2023 general, 2025)
- **Portal:** weberelections.gov / electionresults.utah.gov
- **Documents indexed:** 27  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 4/27 (15%)  ·  **Host(s):** www.weberelections.gov
- **How the text was obtained:** json (raw retained verbatim) (16), pdf (raw retained verbatim) (11)
- **Note:** Raw PDFs/JSON mirrored in election_results/raw/; per-file URLs were not recorded (the Weber site serves files from a CDN bucket).

## Agenda packets / staff reports

- **Documents indexed:** 166  ·  **Date range:** 2020-01-08 to 2026-07-15
- **Direct source URLs recorded:** 166/166 (100%)  ·  **Host(s):** www.ogdencity.gov
- **How the text was obtained:** none (raw retained) (166)

## Housing plans / general plan

- **Documents indexed:** 6  ·  **Date range:** 2020 to 2025
- **Direct source URLs recorded:** 6/6 (100%)  ·  **Host(s):** jobs.utah.gov, www.ogdencity.gov
- **How the text was obtained:** pdftotext-layout (6)

## Ordinances (adoption record)

- **Documents indexed:** 308  ·  **Date range:** 2020-01-07 to 2026-06-16
- **Direct source URLs recorded:** 308/308 (100%)  ·  **Host(s):** www.ogdencity.gov, www.utah.gov
- **How the text was obtained:** reconstructed from meeting_minutes motion text (minutes-derived; NOT independently corroborated) (via minutes document) (276), reconstructed from meeting_minutes motion text; number corroborated by Recorder Synopsis-of-Ordinance PDF (raw/) (27), Recorder Synopsis-of-Ordinance PDF (raw/); pdftotext -layout (5)

## Utah Public Notice backfill

- **Documents indexed:** 19  ·  **Date range:** 2020-05-12 to 2025-01-07
- **Direct source URLs recorded:** 19/19 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (18), textutil (.doc->txt) (1)

## Meeting-video transcripts

- **Documents indexed:** 11  ·  **Date range:** 2026-01-06 to 2026-05-19
- **Direct source URLs recorded:** 11/11 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp --write-auto-sub (YouTube ASR) (10), yt-dlp probe: no auto-captions available (1)

## Campaign-finance disclosures

- **Documents indexed:** 38  ·  **Date range:** 2019-01-01 to 2023-01-01
- **Direct source URLs recorded:** 38/38 (100%)  ·  **Host(s):** www.ogdencity.com
- **How the text was obtained:** tesseract OCR (pdftoppm 300dpi) (24), pdftotext -layout (14)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
