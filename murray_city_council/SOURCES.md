# Sources — Murray civic data

Civic records of the Murray City Municipal Council and Planning Commission, 2020-present, plus municipal election results (2021/2023/2025 in scope). Minutes are published by the City Recorder on the city's CivicPlus Archive Center (murray.utah.gov). Murray publishes no written public-comment compilations (comment is in-person, submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py murray`.

## Council meeting minutes

- **Published by:** Murray City Recorder
- **Portal:** CivicPlus Archive Center (murray.utah.gov, Archive.aspx?AMID=31)
- **Documents indexed:** 170  ·  **Date range:** 2020-01-07 to 2026-06-16
- **Direct source URLs recorded:** 170/170 (100%)  ·  **Host(s):** www.murray.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (169), ocr (1)
- **Note:** Born-digital text PDFs (Archive/ViewFile/Item); named roll-call votes on legislative items, tally-only voice votes on routine items; mayor is executive and does not vote (max council roll = 5). 2023 council minutes are a portal gap (diverted to a Tyler Minutes Management SPA; only 5 of ~24 recovered).

## Planning Commission minutes

- **Published by:** Murray City Community Development
- **Portal:** CivicPlus Archive Center (murray.utah.gov, Archive.aspx?AMID=33)
- **Documents indexed:** 120  ·  **Date range:** 2020-01-02 to 2026-05-07
- **Direct source URLs recorded:** 120/120 (100%)  ·  **Host(s):** www.murray.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (116), ocr (4)
- **Note:** Murray runs its own Planning Commission; born-digital text PDFs, named roll calls. Portal archive ends 2022-11 - no PC minutes published 2023+ (acquisition gap).

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Murray publishes no written public comments - comment is in-person, submit-only and not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** filtered directly from the county canonical (clean_elections.py) (1)
- **Note:** Filtered from the canonical Salt Lake County results (salt_lake_county/elections/slco_municipal_results_long.csv); 2021 general recovered from the raw SOVC workbook due to method-split privacy suppression in the long file.

## Agenda packets / staff reports

- **Documents indexed:** 421  ·  **Date range:** 2020-01-02 to 2026-07-16
- **Direct source URLs recorded:** 421/421 (100%)  ·  **Host(s):** www.murray.utah.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand — pdftotext for born-digital staff-report text, vision/OCR for map/plat exhibits) (387), pdftotext -layout (34)

## Housing plans / general plan

- **Documents indexed:** 8  ·  **Date range:** 2017 to 2025
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** jobs.utah.gov, www.murray.utah.gov
- **How the text was obtained:** pdftotext -layout (7), tesseract OCR (pdftoppm 300dpi) (1)

## Ordinances (adoption record)

- **Documents indexed:** 172  ·  **Date range:** 2021-04-20 to 2026-06-16
- **Direct source URLs recorded:** 172/172 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** tesseract 5 OCR @300dpi (200dpi CCITT scanned PDF) (168), pdftotext -layout (born-digital PDF) (3), none (wrong attachment posted by the city - see linkage_note) (1)

## Utah Public Notice backfill

- **Documents indexed:** 80  ·  **Date range:** 2022-06-21 to 2026-05-07
- **Direct source URLs recorded:** 80/80 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (79), none (1)

## Meeting-video transcripts

- **Documents indexed:** 339  ·  **Date range:** 2019-10-01 to 2026-07-07
- **Direct source URLs recorded:** 339/339 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** mapped_not_fetched (329), yt-dlp --write-auto-sub (YouTube ASR auto-captions), cleaned to text/ (10)

## Campaign-finance disclosures

- **Documents indexed:** 131  ·  **Date range:** 2017-08-07 to 2025-12-04
- **Direct source URLs recorded:** 131/131 (100%)  ·  **Host(s):** www.murray.utah.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (130), claude_vision (docx-embedded images) (1)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
