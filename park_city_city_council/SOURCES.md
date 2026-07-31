# Sources — Park City civic data

Civic records of the Park City Council and Planning Commission, 2020–present. Minutes are published via the city's CivicClerk portal (parkcityut.api.civicclerk.com). Written public comments appear inside minutes and, for a handful of meetings, inside agenda packets on the same portal. Election results are certified by the city (Board of Canvassers) with tabulation by the Summit County Clerk; the canvass PDFs are published on the city's election-results page (parkcity.gov).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py park_city`.

## Council meeting minutes

- **Published by:** Park City Municipal Corporation (City Recorder)
- **Portal:** CivicClerk (parkcityut.api.civicclerk.com)
- **Documents indexed:** 242  ·  **Date range:** 2020-01-09 to 2026-07-09
- **Direct source URLs recorded:** 242/242 (100%)  ·  **Host(s):** parkcityut.api.civicclerk.com
- **How the text was obtained:** text (242)
- **Note:** Born-digital text streams from the CivicClerk API.

## Planning Commission minutes

- **Published by:** Park City Planning Department
- **Portal:** CivicClerk (parkcityut.api.civicclerk.com)
- **Documents indexed:** 162  ·  **Date range:** 2020-01-08 to 2026-06-24
- **Direct source URLs recorded:** 162/162 (100%)  ·  **Host(s):** parkcityut.api.civicclerk.com
- **How the text was obtained:** text (162)
- **Note:** Born-digital text streams from the CivicClerk API.

## Public comments

- **Published by:** Park City Municipal Corporation
- **Portal:** CivicClerk (minutes + agenda packets)
- **Documents indexed:** 97  ·  **Date range:** 2020-09-17 to 2026-05-07
- **Direct source URLs recorded:** 97/97 (100%)  ·  **Host(s):** parkcityut.api.civicclerk.com
- **How the text was obtained:** transcribed from minutes text (92), civicclerk plain-text stream, comment-section parse (5)
- **Note:** Most comments are transcribed from minutes documents; 26 come from 5 agenda packets fetched from the CivicClerk file API.

## Municipal election results

- **Published by:** Park City Recorder / Board of Canvassers (tabulation: Summit County Clerk)
- **Portal:** parkcity.gov/government/elections/election_results.php
- **Documents indexed:** 8  ·  **Date range:** 2021 to 2026
- **Direct source URLs recorded:** 1/8 (12%)  ·  **Host(s):** www.parkcity.gov
- **How the text was obtained:** pdf (raw retained verbatim) (7), html (raw retained verbatim) (1)
- **Note:** Canvass/precinct PDFs saved from the city page and renamed locally (original file names collide across cycles); per-file URLs were not recorded.

## Agenda packets / staff reports

- **Documents indexed:** 942  ·  **Date range:** 2020-01-08 to 2026-07-09
- **Direct source URLs recorded:** 942/942 (100%)  ·  **Host(s):** parkcityut.api.civicclerk.com
- **How the text was obtained:** civicclerk_odata (942)

## Housing plans / general plan

- **Documents indexed:** 15  ·  **Date range:** 2019-11-07 to 2025-09-25
- **Direct source URLs recorded:** 15/15 (100%)  ·  **Host(s):** jobs.utah.gov, www.parkcity.gov
- **How the text was obtained:** pdftotext-layout (14), ocr-tesseract (1)

## Ordinances (adoption record)

- **Documents indexed:** 262  ·  **Date range:** 2020-01-09 to 2026-06-25
- **Direct source URLs recorded:** 262/262 (100%)  ·  **Host(s):** parkcityut.api.civicclerk.com, s3-us-west-2.amazonaws.com
- **How the text was obtained:** reconstructed from meeting_minutes motion text (born-digital CivicClerk minutes) (via minutes document) (164), pdftotext -layout (Municode MunicipalCodeOnline signed ordinance PDF) (98)

## Utah Public Notice backfill

- **Documents indexed:** 16  ·  **Date range:** 2020-01-09 to 2026-06-11
- **Direct source URLs recorded:** 16/16 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (16)

## Meeting-video transcripts

- **Documents indexed:** 194  ·  **Date range:** 2023-09-27 to 2026-07-01
- **Direct source URLs recorded:** 194/194 (100%)  ·  **Host(s):** parkcityut.portal.civicclerk.com
- **How the text was obtained:** none (video-only CivicClerk MP4; no captions; ASR via Whisper deferred) (194)

## Campaign-finance disclosures

- **Documents indexed:** 136  ·  **Date range:** 2017-01-01 to 2026-01-01
- **Direct source URLs recorded:** 136/136 (100%)  ·  **Host(s):** www.parkcity.gov
- **How the text was obtained:** pdftotext -layout (91), tesseract OCR (pdftoppm jpeg 200-300dpi, psm6) (45)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
