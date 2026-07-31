# Sources — Millcreek civic data

Civic records of the Millcreek City Council, Community Reinvestment Agency (CRA), and Planning Commission, 2016-present (Millcreek incorporated December 2016 - the short history is the city's entire legislative life, not a gap). Minutes for all bodies are published by the City Recorder on the city's CivicPlus/CivicEngage AgendaCenter (millcreekut.gov). Millcreek publishes genuine written public comment only inside agenda-packet PDFs (no standalone comment archive). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py millcreek`.

## Council meeting minutes

- **Published by:** Millcreek City Recorder
- **Portal:** CivicPlus/CivicEngage AgendaCenter (millcreekut.gov)
- **Documents indexed:** 373  ·  **Date range:** 2016-12-05 to 2026-06-22
- **Direct source URLs recorded:** 373/373 (100%)  ·  **Host(s):** www.millcreekut.gov
- **How the text was obtained:** text (242), scanned (131)
- **Note:** Combined Agenda+Packet+Minutes PDFs with a scanned/OCR text layer (garble-tolerant extraction); the council also convenes in-session as the Community Reinvestment Agency (CRA), tagged body=CRA - no separate CRA portal files.

## Planning Commission minutes

- **Published by:** Millcreek City Planning Commission
- **Portal:** CivicPlus/CivicEngage AgendaCenter (millcreekut.gov)
- **Documents indexed:** 150  ·  **Date range:** 2017-02-15 to 2026-06-17
- **Direct source URLs recorded:** 150/150 (100%)  ·  **Host(s):** www.millcreekut.gov
- **How the text was obtained:** pdf-text (114), ocr (36)
- **Note:** Millcreek runs its own Planning Commission (not Salt Lake County); mix of born-digital text and OCR PDFs.

## Public comments

- **Published by:** Millcreek City (via agenda packets)
- **Portal:** CivicPlus/CivicEngage AgendaCenter (millcreekut.gov)
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Millcreek publishes no standalone comment compilations; verbatim resident letters appear inside PC agenda-packet PDFs - a Provo-style packet harvest is a documented pending follow-up (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 3  ·  **Date range:** 2019 to 2021
- **Direct source URLs recorded:** 3/3 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (2), csv (raw retained verbatim) (1)
- **Note:** County SOVC workbooks copied verbatim from the local slco-election-archive mirror of the county results site; per-file URLs were not recorded. 2021 & 2023 municipal races used ranked-choice voting.

## Agenda packets / staff reports

- **Documents indexed:** 552  ·  **Date range:** 2016-12-05 to 2026-06-22
- **Direct source URLs recorded:** 552/552 (100%)  ·  **Host(s):** www.millcreekut.gov
- **How the text was obtained:** not_extracted (index/join layer; combined PDF retained in sibling meeting_minutes|planning_commission raw/ or re-fetch source_url) (552)

## Housing plans / general plan

- **Documents indexed:** 7  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** jobs.utah.gov, www.millcreekut.gov, www.utah.gov
- **How the text was obtained:** pdftotext-layout (7)

## Ordinances (adoption record)

- **Documents indexed:** 550  ·  **Date range:** 2016-11 to 2026-06-22
- **Direct source URLs recorded:** 550/550 (100%)  ·  **Host(s):** s3.us-west-2.amazonaws.com
- **How the text was obtained:** pdftext (284), ocr (117), ocr+ocrL (63), pdftext+ocrL (28), ocr+ocrAll (21), index-only (oversize; not stored) (21), vision (6), pdftext+ocrAll (6), text-layer(oversize) (4)

## Utah Public Notice backfill

- **Documents indexed:** 1  ·  **Date range:** 2017-11-21 to 2017-11-21
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** ocr-tesseract (1)

## Meeting-video transcripts

- **Documents indexed:** 92  ·  **Date range:** 2025-01-06 to 2026-06-22
- **Direct source URLs recorded:** 92/92 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp auto-sub (ASR); not retrieved (sample-only policy) (82), yt-dlp auto-sub en-orig (ASR); vtt cleaned to md (10)

## Campaign-finance disclosures

- **Documents indexed:** 41  ·  **Date range:** 2019-10-28 to 2025-12-04
- **Direct source URLs recorded:** 41/41 (100%)  ·  **Host(s):** web.archive.org, www.millcreekut.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (41)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
