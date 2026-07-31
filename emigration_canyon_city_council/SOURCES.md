# Sources — Emigration Canyon civic data

Civic records of the Emigration Canyon City Council and its Planning Commission, plus municipal election results. Emigration Canyon was a metro township 2017-2024, converted to a CITY 2024-05-01 (Utah H.B. 35). 5 at-large councilmembers; the Mayor is peer-selected (Smolka township -> Brems city) and PRESIDES AND VOTES (Millcreek pattern, max tally 5). Minutes are on Utah PMN (council body 5809, PC body 1562) - there is no separate city CMS. Emigration Canyon publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-29 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py emigration_canyon`.

## Council meeting minutes

- **Published by:** Emigration Canyon City Recorder (via Greater Salt Lake MSD)
- **Portal:** Utah Public Notice (utah.gov/pmn; council body 5809)
- **Documents indexed:** 89  ·  **Date range:** 2018-10-25 to 2026-05-19
- **Direct source URLs recorded:** 89/89 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdf-text (81), ocr (7), docx-text (1)
- **Note:** Born-digital text PDFs (DocuSign-signed; 7 scanned council docs OCR'd, 2 of which yielded 0 motions - OCR-quality gap, born-digital re-fetch is a TODO). Narrative-tally votes; the peer-selected Mayor votes (max 5). ⚠ PMN purged its 2017 (+ scattered 2018-19) file store (404) - recovered coverage begins 2018-10 (council) / 2018-11 (PC); logged in minutes_unrecovered.csv.

## Planning Commission minutes

- **Published by:** Emigration Canyon Planning Commission
- **Portal:** Utah Public Notice (utah.gov/pmn; body 1562)
- **Documents indexed:** 60  ·  **Date range:** 2018-11-15 to 2026-06-11
- **Direct source URLs recorded:** 60/60 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdf-text (59), ocr (1)
- **Note:** Emigration Canyon runs its own Planning Commission (monthly); structured Motion/Vote grammar; land-use recommendations to Council. Born-digital; coverage from 2018-11.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Emigration Canyon publishes no written public comments - in-person/Zoom + email/phone; minutes paraphrase speakers only; submit-only (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** filtered directly from the county canonical (build_emigration_elections.py) (1)
- **Note:** Filtered from the canonical Salt Lake County results; at-large seats (2017/2023/2025). The mayor is council-selected (no separate mayor contest). The Emigration Improvement District (sewer) + 2015 MSD/incorporation ballot questions are EXCLUDED. 2019/2021 had no council contest; the 2016 founding election is even-year (outside the municipal archive).

## Agenda packets / staff reports

- **Documents indexed:** 375  ·  **Date range:** 2019-01-17 to 2026-07-09
- **Direct source URLs recorded:** 375/375 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (324), none (docx raw retained) (24), none (image-only PDF; vision/OCR to read) (24), none (oversize; raw retained) (2), claude_vision (1)

## Housing plans / general plan

- **Documents indexed:** 1  ·  **Date range:** 2022-03-22 to 2022-03-22
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** msd.utah.gov
- **How the text was obtained:** pdftotext (1)

## Ordinances (adoption record)

- **Documents indexed:** 98  ·  **Date range:** 2017-04-01 to 2026-05-19
- **Direct source URLs recorded:** 98/98 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com
- **How the text was obtained:** ocr_tesseract (53), pdftotext_layout (45)

## Utah Public Notice backfill

- **Documents indexed:** 1  ·  **Date range:** 2025-11-13 to 2025-11-13
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** ocr (1)

## Meeting-video transcripts

- **Documents indexed:** 244  ·  **Date range:** 2017-01-11 to 2026-07-09
- **Direct source URLs recorded:** 244/244 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** none (PMN audio file — no caption track; Whisper candidate, not run) (211), none (PMN file purged/unavailable — HTTP 404; pre-~mid-2018 blob rot) (33)

## Campaign-finance disclosures

- **Documents indexed:** 35  ·  **Date range:** 2016-11-01 to 2026-01-15
- **Direct source URLs recorded:** 35/35 (100%)  ·  **Host(s):** emigration.utah.gov, www.saltlakecounty.gov
- **How the text was obtained:** none (raw acquisition; text/OCR/vision deferred) (35)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
