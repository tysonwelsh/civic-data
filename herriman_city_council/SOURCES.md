# Sources — Herriman civic data

Civic records of the Herriman City Council (with in-session CDRA / HCSEA / HCFSA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2007. Minutes are published on the city's PrimeGov portal (herriman.primegov.com); 2020 minutes were recovered from the city's legacy AWS S3 agenda bucket. Herriman publishes no written public-comment compilations (comment is in-person/eComment-window, submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py herriman`.

## Council meeting minutes

- **Published by:** Herriman City Recorder
- **Portal:** PrimeGov (herriman.primegov.com; committeeId 3); 2020 backfill from the legacy herriman-agendas S3 bucket
- **Documents indexed:** 180  ·  **Date range:** 2020-01-08 to 2026-05-27
- **Direct source URLs recorded:** 180/180 (100%)  ·  **Host(s):** herriman.primegov.com, s3-us-west-1.amazonaws.com
- **How the text was obtained:** text (178), ocr (2)
- **Note:** Born-digital text PDFs (CompiledDocument). Named roll-call votes; the MAYOR VOTES as a full member (max council roll = 5: 4 districts + mayor). Council also convenes in-session as CDRA (17C renewal agency), HCSEA (Safety Enforcement Area) and HCFSA (Fire Service Area), tagged by the body column. 2020 recovered from legacy S3 (PrimeGov only goes back to 2021-01).

## Planning Commission minutes

- **Published by:** Herriman City Planning Division
- **Portal:** PrimeGov (herriman.primegov.com; committeeId 14)
- **Documents indexed:** 131  ·  **Date range:** 2020-01-02 to 2026-06-03
- **Direct source URLs recorded:** 131/131 (100%)  ·  **Host(s):** herriman.primegov.com, s3-us-west-1.amazonaws.com
- **How the text was obtained:** text (112), ocr (19)
- **Note:** Herriman runs its own Planning Commission; born-digital text PDFs, named roll calls; 2020 recovered from legacy S3.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Herriman publishes no written public comments - comment is in-person / PrimeGov eComment-window, submit-only and not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 4  ·  **Date range:** 2011 to 2021
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (3), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2011 general, 2019 general, and 2021 general recovered from raw SOVC workbooks (canonical long-file misses/suppresses them).

## Agenda packets / staff reports

- **Documents indexed:** 373  ·  **Date range:** 2020-01-08 to 2026-07-15
- **Direct source URLs recorded:** 373/373 (100%)  ·  **Host(s):** herriman.primegov.com, s3-us-west-1.amazonaws.com
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand, use vision/OCR) (373)

## Housing plans / general plan

- **Documents indexed:** 11  ·  **Date range:** 2013-10-07 to 2025
- **Direct source URLs recorded:** 11/11 (100%)  ·  **Host(s):** jobs.utah.gov, web.archive.org, www.herriman.gov
- **How the text was obtained:** pdftotext -layout (10), pdftotext -layout (embedded Acrobat Paper Capture OCR layer) (1)

## Ordinances (adoption record)

- **Documents indexed:** 278  ·  **Date range:** 2014-06-12 to 2026-06-18
- **Direct source URLs recorded:** 274/278 (99%)  ·  **Host(s):** herriman.primegov.com, s3-us-west-1.amazonaws.com, s3-us-west-2.amazonaws.com, www.utah.gov
- **How the text was obtained:** html-strip (PMN Recorder adoption notice; summary only, not full ordinance text) (121), tesseract OCR @300dpi (no text layer) (101), reconstructed from meeting_minutes motion text (no independent document found) (46), pdftotext -layout (10)

## Utah Public Notice backfill

- **Documents indexed:** 81  ·  **Date range:** 2020-01-16 to 2026-06-09
- **Direct source URLs recorded:** 81/81 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (67), html (9), tesseract-ocr (4), text (1)

## Meeting-video transcripts

- **Documents indexed:** 677  ·  **Date range:** 2015-03-11 to 2026-07-08
- **Direct source URLs recorded:** 677/677 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** mapped_not_fetched (667), yt-dlp --write-auto-sub (YouTube ASR auto-captions), cleaned to text/ (10)

## Campaign-finance disclosures

- **Documents indexed:** 50  ·  **Date range:** 2021-08-03 to 2025-12-04
- **Direct source URLs recorded:** 50/50 (100%)  ·  **Host(s):** web.archive.org, www.herriman.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (33), none (raw acquisition; born-digital text layer present) (17)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
