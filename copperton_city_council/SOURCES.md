# Sources — Copperton civic data

Civic records of the Town of Copperton Council (~800 residents) and its (mostly-cancelled) Planning Commission, plus municipal election results. Copperton was a metro township 2017-2024, converted to a TOWN 2024-05-01 (Utah H.B. 35). 5 at-large seats; the Mayor/Chair VOTES in both eras (max tally 5). Minutes are on the town's GoDaddy site + Utah PMN (council body 5831, PC body 1560). Copperton publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py copperton`.

## Council meeting minutes

- **Published by:** Town of Copperton Recorder
- **Portal:** copperton.utah.gov (GoDaddy, curl -k for the TLS mismatch) + Utah PMN body 5831
- **Documents indexed:** 106  ·  **Date range:** 2018-07-18 to 2026-05-20
- **Direct source URLs recorded:** 106/106 (100%)  ·  **Host(s):** img1.wsimg.com, www.utah.gov
- **How the text was obtained:** text (91), ocr (14), text+ocr (1)
- **Note:** Born-digital text PDFs (14 town-era 2024-2025 minutes were RICOH scans, OCR'd; format=ocr). Narrative-tally votes (mover+seconder named, collective tally; per-member roll calls rare). The Mayor/Chair votes in both eras (max 5). ⚠ 2017-02 -> 2018-06 council minutes are 404-PURGED from PMN (retention window) and predate the GoDaddy site (2023+) - 29 meetings logged in minutes_unrecovered.csv.

## Planning Commission minutes

- **Published by:** Town of Copperton Planning Commission (MSD-supported)
- **Portal:** Utah Public Notice (utah.gov/pmn; body 1560)
- **Documents indexed:** 17  ·  **Date range:** 2019-03-12 to 2025-05-13
- **Direct source URLs recorded:** 17/17 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** text (17)
- **Note:** Copperton's PC is nominal - most scheduled meetings are CANCELLED (tiny land-use volume); 18 minutes docs 2019-2025, tally-only/mover-only, no mayor. Thin by design.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Copperton publishes no written public comments - in-person 'Community Input' + inline speaker notes; submit-only (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; at-large seats A-E (2017/2021/2023). 2019 council absent from the county archive; the 2025 first-Mayor race (Clayton unopposed) was NOT tabulated by the county (all seats unopposed). Copperton MSD / Improvement-District / 2015 ballot questions EXCLUDED.

## Agenda packets / staff reports

- **Documents indexed:** 305  ·  **Date range:** 2019-01-15 to 2026-07-15
- **Direct source URLs recorded:** 305/305 (100%)  ·  **Host(s):** img1.wsimg.com, www.utah.gov
- **How the text was obtained:** pdftotext -layout (250), none (docx raw retained) (47), none (image-only PDF; vision/OCR to read) (7), textutil (docx->txt) (1)

## Housing plans / general plan

- **Documents indexed:** 2  ·  **Date range:** 2020 to 2020
- **Direct source URLs recorded:** 2/2 (100%)  ·  **Host(s):** ut-greatersaltlakemsd.civicplus.com
- **How the text was obtained:** pdftotext -layout (2)

## Ordinances (adoption record)

- **Documents indexed:** 129  ·  **Date range:** 2017-01-05 to 2026-06-17
- **Direct source URLs recorded:** 129/129 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com
- **How the text was obtained:** pdftotext_layout (71), ocr_tesseract (58)

## Utah Public Notice backfill

- **Documents indexed:** 1  ·  **Date range:** 2025-10-15 to 2025-10-15
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (1)

## Meeting-video transcripts

- **Documents indexed:** 160  ·  **Date range:** 2017-02-15 to 2026-06-17
- **Direct source URLs recorded:** 160/160 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** none (PMN audio file — no caption track; Whisper candidate, not run) (120), none (PMN file purged/unavailable — HTTP 404; pre-~mid-2018 blob rot) (40)

## Campaign-finance disclosures

- **Documents indexed:** 25  ·  **Date range:** 2016-11-01 to 2026-01-01
- **Direct source URLs recorded:** 25/25 (100%)  ·  **Host(s):** img1.wsimg.com, www.saltlakecounty.gov
- **How the text was obtained:** none (raw acquisition; text/OCR/vision deferred) (25)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
