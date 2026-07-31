# Sources — Cottonwood Heights civic data

Civic records of the Cottonwood Heights City Council (with in-session CDRA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2009 (incorporated 2005). Minutes are published on the city's Granicus/CivicEngage portal, whose rolling ~5-year window was backfilled from Utah Public Notice. 4 district councilmembers + a separately-elected VOTING Mayor (max council roll = 5). Cottonwood Heights publishes no written public-comment compilations (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py cottonwood_heights`.

## Council meeting minutes

- **Published by:** Cottonwood Heights City Recorder
- **Portal:** Granicus/CivicEngage (cottonwoodheights.utah.gov) unioned with Utah Public Notice (council body 2147)
- **Documents indexed:** 185  ·  **Date range:** 2020-01-06 to 2026-06-16
- **Direct source URLs recorded:** 185/185 (100%)  ·  **Host(s):** web.archive.org, www.cottonwoodheights.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (184), docx-text (1)
- **Note:** Born-digital text PDFs (+ a few .docx). The CivicEngage portal only retains ~5 years (2022 column decayed to 4 docs), so 2020-2024 was backfilled from PMN. The MAYOR VOTES (max council roll = 5: 4 districts + mayor). Council also convenes in-session as the CDRA (Community Development & Renewal Agency; body=CDRA).

## Planning Commission minutes

- **Published by:** Cottonwood Heights Planning Division
- **Portal:** Granicus/CivicEngage (cottonwoodheights.utah.gov) + Utah Public Notice (body 2148)
- **Documents indexed:** 103  ·  **Date range:** 2020-01-08 to 2026-02-04
- **Direct source URLs recorded:** 103/103 (100%)  ·  **Host(s):** www.cottonwoodheights.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (100), docx-text (3)
- **Note:** Cottonwood Heights runs its own Planning Commission (Wednesday); born-digital text. Administrative-hearing-officer sessions carry no roll-call votes (legitimate 0-motion files).

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Cottonwood Heights publishes no written public comments - eComment submission form + emailed to the City Recorder + inline hearing speaker notes; submit-only, not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 4  ·  **Date range:** 2011 to 2021
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** csv (raw retained verbatim) (2), xlsx (raw retained verbatim) (2)
- **Note:** Filtered from the canonical Salt Lake County results; 2011 & 2019 recovered from raw SOVC, 2021 re-parsed for privacy suppression. Parks & Rec Service Area and Cottonwood Improvement Board contests are EXCLUDED (not the city).

## Agenda packets / staff reports

- **Documents indexed:** 69  ·  **Date range:** 2024-11-06 to 2026-07-07
- **Direct source URLs recorded:** 69/69 (100%)  ·  **Host(s):** www.cottonwoodheights.utah.gov
- **How the text was obtained:** pdftotext-layout (69)

## Housing plans / general plan

- **Documents indexed:** 12  ·  **Date range:** 2005-01-14 to 2025-07-01
- **Direct source URLs recorded:** 12/12 (100%)  ·  **Host(s):** jobs.utah.gov, www.cottonwoodheights.utah.gov
- **How the text was obtained:** pdftotext -layout (10), tesseract OCR (2)

## Ordinances (adoption record)

- **Documents indexed:** 128  ·  **Date range:** 2020-01-07 to 2026-05-19
- **Direct source URLs recorded:** 128/128 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com, www.cottonwoodheights.utah.gov, www.utah.gov
- **How the text was obtained:** tesseract 5 OCR @300dpi (scanned/image PDF) (81), na (36), pdftotext -layout (born-digital) (11)

## Utah Public Notice backfill

- **Documents indexed:** 16  ·  **Date range:** 2020-03-11 to 2023-03-01
- **Direct source URLs recorded:** 16/16 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (16)

## Meeting-video transcripts

- **Documents indexed:** 511  ·  **Date range:** 2018-08-28 to 2026-07-07
- **Direct source URLs recorded:** 511/511 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** mapped_not_fetched (501), yt-dlp --write-auto-sub (YouTube ASR auto-captions), cleaned to text/ (10)

## Campaign-finance disclosures

- **Documents indexed:** 86  ·  **Date range:** 2017-08-31 to 2025-12-04
- **Direct source URLs recorded:** 86/86 (100%)  ·  **Host(s):** municipal.utah.gov, www.cottonwoodheights.utah.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (86)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
