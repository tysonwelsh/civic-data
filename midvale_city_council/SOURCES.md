# Sources — Midvale civic data

Civic records of the Midvale City Council (with in-session RDA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2007. Minutes are published on the city's Revize Document Center (midvale.utah.gov). Midvale uses Utah's six-member council form: 5 district councilmembers legislate and the Mayor votes only to break ties (max ordinary council roll = 5). Midvale publishes no written public-comment compilations (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py midvale`.

## Council meeting minutes

- **Published by:** Midvale City Recorder
- **Portal:** Revize Document Center (midvale.utah.gov)
- **Documents indexed:** 151  ·  **Date range:** 2020-01-07 to 2026-06-16
- **Direct source URLs recorded:** 151/151 (100%)  ·  **Host(s):** www.midvale.utah.gov
- **How the text was obtained:** text (121), ocr (30)
- **Note:** Born-digital text PDFs 2022+, but the 2020-2021 council minutes are SCANNED image PDFs recovered via OCR (format=ocr; recon's 'born-digital' claim held only for recent years). Named tabular roll calls. The council also convenes in-session as the RDA (body=RDA). Mayor votes only on ties (max ordinary roll = 5).

## Planning Commission minutes

- **Published by:** Midvale City Planning Division
- **Portal:** Revize Document Center (midvale.utah.gov)
- **Documents indexed:** 104  ·  **Date range:** 2020-01-08 to 2026-06-24
- **Direct source URLs recorded:** 104/104 (100%)  ·  **Host(s):** www.midvale.utah.gov
- **How the text was obtained:** text (88), ocr (16)
- **Note:** Midvale runs its own Planning & Zoning Commission (2nd & 4th Wednesday); mix of born-digital text and OCR'd scans. One 2020 PC doc had a corrupt source PDF (logged in minutes_unrecovered.csv).

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Midvale publishes no written public comments - inline 'Public Comments' speaker notes in minutes; submit-only, not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 4  ·  **Date range:** 2019 to 2021
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (3), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2019 general recovered from raw SOVC. A 2023 bond question is kept out of the council/mayor races file.

## Agenda packets / staff reports

- **Documents indexed:** 117  ·  **Date range:** 2020-10-20 to 2026-07-08
- **Direct source URLs recorded:** 117/117 (100%)  ·  **Host(s):** www.midvale.utah.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand) (110), not_retrieved (dead link — city page 404s as-published) (7)

## Housing plans / general plan

- **Documents indexed:** 8  ·  **Date range:** 2016 to 2025
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** jobs.utah.gov, www.midvale.utah.gov
- **How the text was obtained:** pdftotext -layout (8)

## Ordinances (adoption record)

- **Documents indexed:** 263  ·  **Date range:** 2012-01-01 to 2048-07-17
- **Direct source URLs recorded:** 263/263 (100%)  ·  **Host(s):** www.midvale.utah.gov
- **How the text was obtained:** pdftotext -layout (149), tesseract 5 OCR @300dpi (15pg) (29), tesseract 5 OCR @300dpi (3pg) (22), tesseract 5 OCR @300dpi (4pg) (13), tesseract 5 OCR @300dpi (6pg) (10), tesseract 5 OCR @300dpi (2pg) (10), tesseract 5 OCR @300dpi (5pg) (7), tesseract 5 OCR @300dpi (8pg) (4), tesseract 5 OCR @300dpi (13pg) (4), tesseract 5 OCR @300dpi (10pg) (4), tesseract 5 OCR @300dpi (7pg) (3), na (2), tesseract 5 OCR @300dpi (12pg) (1), tesseract 5 OCR @300dpi (first 15 of 50pp; gs-repaired corrupt xref) (1), tesseract 5 OCR @300dpi (4pg; gs-repaired corrupt xref) (1), tesseract 5 OCR @300dpi (9pg) (1), textutil (1), tesseract 5 OCR @300dpi (4pg; DocuSign text-layer only, forced OCR) (1)

## Utah Public Notice backfill

- **Documents indexed:** 25  ·  **Date range:** 2020-01-21 to 2025-06-03
- **Direct source URLs recorded:** 25/25 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext (21), ocr (4)

## Meeting-video transcripts

- **Documents indexed:** 258  ·  **Date range:** 2020-04-08 to 2026-07-08
- **Direct source URLs recorded:** 258/258 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** enumerated (248), yt-dlp --write-auto-sub (en ASR) (10)

## Campaign-finance disclosures

- **Documents indexed:** 84  ·  **Date range:** 2017-08-29 to 2025-12-04
- **Direct source URLs recorded:** 84/84 (100%)  ·  **Host(s):** municipal.utah.gov, www.midvale.utah.gov
- **How the text was obtained:** none (acquisition-only; scanned image PDF, OCR/vision deferred) (57), none (acquisition-only; born-digital text PDF) (27)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
