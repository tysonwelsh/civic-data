# Sources — West Jordan civic data

Civic records of the West Jordan City Council and Planning Commission, 2020–present. Minutes are published on the city's PrimeGov portal (westjordan.primegov.com). Written public comments were harvested from council agenda packets on the same portal. Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py west_jordan`.

## Council meeting minutes

- **Published by:** West Jordan City Recorder
- **Portal:** PrimeGov (westjordan.primegov.com)
- **Documents indexed:** 323  ·  **Date range:** 2020-01-08 to 2026-06-23
- **Direct source URLs recorded:** 323/323 (100%)  ·  **Host(s):** westjordan.primegov.com
- **How the text was obtained:** pdf-text (322), docx-text (1)
- **Note:** PDF minutes (born-digital text; some OCR'd signature pages).

## Planning Commission minutes

- **Published by:** West Jordan Planning Division
- **Portal:** PrimeGov (westjordan.primegov.com)
- **Documents indexed:** 86  ·  **Date range:** 2020-09-29 to 2026-06-16
- **Direct source URLs recorded:** 86/86 (100%)  ·  **Host(s):** westjordan.primegov.com
- **How the text was obtained:** text (50), ocr (36)
- **Note:** 36 of 84 documents are OCR.

## Public comments

- **Published by:** West Jordan City Council Office
- **Portal:** PrimeGov (westjordan.primegov.com) — compiled agenda packets
- **Documents indexed:** 2  ·  **Date range:** 2022-08-10 to 2022-09-14
- **Direct source URLs recorded:** 2/2 (100%)  ·  **Host(s):** westjordan.primegov.com
- **How the text was obtained:** pdf text extraction (2)
- **Note:** 120 packets scanned (record: public_comments/packets_scanned.csv; 15 contained comments, mostly duplicates of one another); the 2 packets contributing the deduplicated dataset are indexed here with raw PDFs retained.

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** filtered directly from the county canonical (build_wjordan_elections.py) (1)
- **Note:** County SOVC workbooks copied verbatim from a local mirror of the county results site; per-file URLs were not recorded.

## Agenda packets / staff reports

- **Documents indexed:** 222  ·  **Date range:** 2022-07-13 to 2026-01-06
- **Direct source URLs recorded:** 222/222 (100%)  ·  **Host(s):** westjordan.primegov.com
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand, use vision/OCR) (222)

## Housing plans / general plan

- **Documents indexed:** 11  ·  **Date range:** 2020-09-30 to 2026-04-01
- **Direct source URLs recorded:** 11/11 (100%)  ·  **Host(s):** assets.westjordan.utah.gov, jobs.utah.gov, www.westjordan.utah.gov
- **How the text was obtained:** pdftotext -layout (5), pdftotext -layout (designed layout inserts letter-spacing artifacts; raw PDF is authoritative) (1), none (60x36 poster map; single-page image with no text layer — vision/print to read) (1), pdftotext -layout (WJ = pp.1044-1059 sliced from 1109-pp statewide compilation) (1), pdftotext -layout (WJ = pp.968-989 sliced from 1030-pp statewide compilation) (1), pdftotext -layout (WJ = pp.1224-1248 sliced from 1303-pp statewide compilation) (1), pdftotext -layout (WJ = pp.189-191 sliced from 199-pp statewide compilation) (1)

## Ordinances (adoption record)

- **Documents indexed:** 293  ·  **Date range:** 2020-05-13 to 2026-06-23
- **Direct source URLs recorded:** 293/293 (100%)  ·  **Host(s):** assets.westjordan.utah.gov, westjordan.primegov.com, www.westjordan.utah.gov
- **How the text was obtained:** derived from meeting_minutes/all_votes.csv motion text (via minutes document) (226), pdftotext -layout (64), tesseract OCR (scanned image PDF, 200dpi) (3)

## Utah Public Notice backfill

- **Documents indexed:** 60  ·  **Date range:** 2020-01-07 to 2026-06-09
- **Direct source URLs recorded:** 60/60 (100%)  ·  **Host(s):** assets.westjordan.utah.gov, www.utah.gov
- **How the text was obtained:** pdftotext-layout (54), tesseract-ocr (6)

## Meeting-video transcripts

- **Documents indexed:** 10  ·  **Date range:** 2024-11-06 to 2025-02-04
- **Direct source URLs recorded:** 10/10 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp --write-auto-sub --sub-lang en-orig --sub-format vtt; rolling-dedup clean_vtt.py (10)

## Campaign-finance disclosures

- **Documents indexed:** 135  ·  **Date range:** 2021-10-01 to 2026-04-06
- **Direct source URLs recorded:** 135/135 (100%)  ·  **Host(s):** ecf-api.easyvoteapp.com, www.westjordan.utah.gov
- **How the text was obtained:** pdftotext -layout (68), ocr:tesseract --psm 6 (67)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
