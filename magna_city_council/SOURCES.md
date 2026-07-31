# Sources — Magna civic data

Civic records of the Magna City Council (with in-recess CRA sessions) and its MSD-staffed Planning Commission, 2017-present, plus municipal election results. Magna was a metro township 2017-2024, converted to a CITY 2024-05-01 (Utah H.B. 35). 5 district councilmembers. Across the seam the presiding officer's vote flips: the township-era elected Chair (titled 'Mayor') VOTED, but the 2026+ directly-elected executive Mayor (Mick Sudbury) does NOT vote (max council roll = 5 both eras). Minutes are on CivicPlus (2022+) and Utah PMN (2017-2021). Magna publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py magna`.

## Council meeting minutes

- **Published by:** Magna City Recorder
- **Portal:** CivicPlus AgendaCenter (magna.utah.gov, catID 3) + Utah PMN body 5803 (2017-2021 archive)
- **Documents indexed:** 173  ·  **Date range:** 2018-07-17 to 2026-05-26
- **Direct source URLs recorded:** 173/173 (100%)  ·  **Host(s):** magna.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (151), pdf-ocr (21), docx-text (1)
- **Note:** Born-digital text PDFs (2024 Apr-Dec + early 2025 signed-scan minutes were image-only, OCR'd; format=pdf-ocr). Narrative-tally votes. The Chair-titled-'Mayor' votes pre-2026; the exec Mayor Sudbury does not vote 2026+ (max 5). Council also convenes in-recess as the CRA ('Board Member' roles; body=CRA). ⚠ CivicPlus sometimes serves wrong docs in the Minutes slot (agendas/spreadsheets/correspondence) - recovered real minutes from PMN where possible. 2017 + Jan-Jun 2018 council minutes (36 mtgs) are 404-unrecoverable on PMN (logged in minutes_unrecovered.csv).

## Planning Commission minutes

- **Published by:** Greater Salt Lake MSD Planning & Development (for Magna)
- **Portal:** Utah Public Notice (utah.gov/pmn; body 1559)
- **Documents indexed:** 80  ·  **Date range:** 2019-03-14 to 2026-06-11
- **Direct source URLs recorded:** 80/80 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdf-text (80)
- **Note:** Magna's Planning Commission is MSD-staffed; minutes begin 2019 (2017-2018 posted agendas only, 57 logged). Rezones keyed REZ####; recommends to Council. Born-digital.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Magna publishes no written public comments - in-person sign-up sheet + QR-to-staff; no eComment portal; PMN posts audio only; submit-only (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 4  ·  **Date range:** 2016 to 2021
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (3), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; the 2016 founding election + 2019 D1/D3/D5 recovered from raw SOVC, 2021 re-parsed for suppression; the 2025 primary/general split. The Magna Water District (all variants) + MSD + 2015 incorporation ballot questions are EXCLUDED (~95% of raw 'magna' rows are the Water District).

## Agenda packets / staff reports

- **Documents indexed:** 501  ·  **Date range:** 2019-01-10 to 2026-07-14
- **Direct source URLs recorded:** 501/501 (100%)  ·  **Host(s):** magna.utah.gov, www.utah.gov
- **How the text was obtained:** pdftotext-layout (294), section_split (204), pdftotext-layout (image-only; vision/OCR to read) (2), docx-xml (born-digital; word/document.xml strip) (1)

## Housing plans / general plan

- **Documents indexed:** 9  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 9/9 (100%)  ·  **Host(s):** jobs.utah.gov, msd.utah.gov, www.msd.utah.gov, www.utah.gov
- **How the text was obtained:** pdftotext -layout (8), pdftotext -layout (image-based; low text yield) (1)

## Ordinances (adoption record)

- **Documents indexed:** 239  ·  **Date range:** 2017-01-01 to 2026-06-23
- **Direct source URLs recorded:** 239/239 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com
- **How the text was obtained:** ocr_tesseract (150), pdftotext_layout (88), textutil_docx (1)

## Utah Public Notice backfill

- **Documents indexed:** 20  ·  **Date range:** 2020-08-11 to 2026-06-09
- **Direct source URLs recorded:** 20/20 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (11), tesseract-ocr (9)

## Meeting-video transcripts

- **Documents indexed:** 457  ·  **Date range:** 2016-09-15 to 2026-07-09
- **Direct source URLs recorded:** 457/457 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** none (PMN audio MP3 — no caption track; Whisper candidate, not run) (370), none (PMN file purged/unavailable — HTTP 404; pre-~2018 blob rot) (87)

## Campaign-finance disclosures

- **Documents indexed:** 64  ·  **Date range:** 2016-06-01 to 2025-10-28
- **Direct source URLs recorded:** 64/64 (100%)  ·  **Host(s):** magna.utah.gov, www.saltlakecounty.gov
- **How the text was obtained:** none (raw acquisition; text/OCR/vision deferred) (64)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
