# Sources — Bluffdale civic data

Civic records of the Bluffdale City Council (with in-session RDA and LBA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2007. Minutes are published on the city's CivicPlus/CivicEngage AgendaCenter (bluffdale.gov). Bluffdale is a 5 at-large council + Mayor; the Mayor is non-voting in the Council (max member tally = 5) except rare tie-breaks, but votes as Chair in the in-session RDA/LBA (max 6). Bluffdale straddles Salt Lake (primary) + Utah (unpopulated Camp Williams) counties; Salt Lake County administers the whole election. Bluffdale publishes no written public-comment archive (submit-only).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py bluffdale`.

## Council meeting minutes

- **Published by:** Bluffdale City Recorder
- **Portal:** CivicPlus/CivicEngage AgendaCenter (bluffdale.gov, CID=2 council)
- **Documents indexed:** 166  ·  **Date range:** 2020-01-06 to 2026-06-24
- **Direct source URLs recorded:** 166/166 (100%)  ·  **Host(s):** www.bluffdale.gov
- **How the text was obtained:** text (137), ocr (29)
- **Note:** Mix of born-digital text PDFs, 2 .docx, and scanned PDFs recovered via OCR (only 29 of 166 council docs needed OCR - recon overstated the scan rate; format=ocr where used). Full named roll calls. The council convenes in-session as the RDA and LBA (body=RDA / body=LBA), where the Mayor votes as Chair; in the pure Council body the Mayor is non-voting except 2 recorded tie-breaks.

## Planning Commission minutes

- **Published by:** Bluffdale City Planning Division
- **Portal:** CivicPlus/CivicEngage AgendaCenter (bluffdale.gov, CID=3)
- **Documents indexed:** 91  ·  **Date range:** 2020-01-08 to 2026-06-03
- **Direct source URLs recorded:** 91/91 (100%)  ·  **Host(s):** www.bluffdale.gov
- **How the text was obtained:** text (68), ocr (23)
- **Note:** Bluffdale runs its own Planning Commission (1st & 3rd Wednesday); mix of born-digital and OCR'd scans. One 2025-10-15 PC tally is OCR-garbled (printed 4-2 vs counted 3-1) and surfaced honestly, not patched.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Bluffdale publishes no written public comments - emailed comments (councilmeetingcomment@bluffdale.gov) are submitted but NOT read at the meeting and not posted; submit-only (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 4  ·  **Date range:** 2019 to 2021
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (3), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2019 recovered from raw SOVC. At-large multi-seat races. 2021 was the Utah RCV pilot (2-seat ranked-choice; take winners Aston seat-1 + Crockett seat-2 from the canvass, NOT first-choice rank).

## Agenda packets / staff reports

- **Documents indexed:** 217  ·  **Date range:** 2020-01-08 to 2026-07-15
- **Direct source URLs recorded:** 217/217 (100%)  ·  **Host(s):** www.bluffdale.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand — pdftotext for born-digital staff-report text, vision/OCR for map/plat exhibits) (157), pdftotext (59), pdftotext_raw (1)

## Housing plans / general plan

- **Documents indexed:** 11  ·  **Date range:** 2021 to 2025-07-15
- **Direct source URLs recorded:** 11/11 (100%)  ·  **Host(s):** jobs.utah.gov, www.bluffdale.gov
- **How the text was obtained:** pdftotext -layout (11)

## Ordinances (adoption record)

- **Documents indexed:** 150  ·  **Date range:** 2020-01-29 to 2026-06-10
- **Direct source URLs recorded:** 150/150 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com, www.bluffdale.gov
- **How the text was obtained:** reconstructed from meeting_minutes motion text (no independent PDF in archive) (75), pdftotext -layout (born-digital adopted ordinance PDF, Municipal Code Online archive) (54), tesseract OCR (scanned signed ordinance PDF, Municipal Code Online archive) (21)

## Utah Public Notice backfill

- **Documents indexed:** 1  ·  **Date range:** 2023-11-14 to 2023-11-14
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (1)

## Campaign-finance disclosures

- **Documents indexed:** 106  ·  **Date range:** 2017-08-08 to 2025-12-04
- **Direct source URLs recorded:** 106/106 (100%)  ·  **Host(s):** www.bluffdale.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (106)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
