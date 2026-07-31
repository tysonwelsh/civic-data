# Sources — Taylorsville civic data

Civic records of the Taylorsville City Council (with in-session RDA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2007. Minutes are published by the City Recorder on the city's CivicPlus/CivicEngage Central site (taylorsvilleut.gov), with the Utah Public Notice Website as a cross-check/fallback. Taylorsville publishes no written public-comment compilations (comment is in-person/livestream, submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py taylorsville`.

## Council meeting minutes

- **Published by:** Taylorsville City Recorder
- **Portal:** CivicPlus/CivicEngage Central (taylorsvilleut.gov); fallback: Utah Public Notice (utah.gov/pmn)
- **Documents indexed:** 150  ·  **Date range:** 2020-01-08 to 2026-06-03
- **Direct source URLs recorded:** 150/150 (100%)  ·  **Host(s):** www.taylorsvilleut.gov, www.utah.gov
- **How the text was obtained:** pdf-text (129), ocr (21)
- **Note:** Born-digital text PDFs (showpublisheddocument) with a mid-2025 switch to scanned RICOH OCR PDFs; the council also convenes in-session as the Redevelopment Agency (RDA), tagged body=RDA - no separate RDA portal files.

## Planning Commission minutes

- **Published by:** Taylorsville City Planning Division
- **Portal:** CivicPlus/CivicEngage Central (taylorsvilleut.gov)
- **Documents indexed:** 91  ·  **Date range:** 2020-01-14 to 2026-04-28
- **Direct source URLs recorded:** 91/91 (100%)  ·  **Host(s):** www.taylorsvilleut.gov, www.utah.gov
- **How the text was obtained:** pdf-text (63), ocr (28)
- **Note:** Taylorsville runs its own Planning Commission (not Salt Lake County); mix of born-digital text and OCR PDFs.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Taylorsville publishes no written public comments - comment is in-person/livestream, submit-only and not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 3  ·  **Date range:** 2019 to 2021
- **Direct source URLs recorded:** 3/3 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (2), filtered directly from the county canonical (clean_elections.py) (1)
- **Note:** County SOVC workbooks copied verbatim from the local slco-election-archive mirror of the county results site (2019 re-parsed from the raw SOVC); per-file URLs were not recorded.

## Agenda packets / staff reports

- **Documents indexed:** 7  ·  **Date range:** 2026-06-03 to 2026-07-01
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** www.taylorsvilleut.gov
- **How the text was obtained:** none (raw retained; 1pg scan) (2), none (raw retained; born-digital PDF, pdftotext -layout, 16pg) (1), none (raw retained; born-digital DOCX, not PDF) (1), none (raw retained; 19pg scan, OCR/vision to read) (1), none (raw retained; born-digital PDF, pdftotext -layout, 45pg) (1), none (raw retained; 2pg scan) (1)

## Housing plans / general plan

- **Documents indexed:** 14  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 14/14 (100%)  ·  **Host(s):** jobs.utah.gov, www.taylorsvilleut.gov
- **How the text was obtained:** pdftotext-layout (14)

## Ordinances (adoption record)

- **Documents indexed:** 90  ·  **Date range:** 2020-01-08 to 2026-05-06
- **Direct source URLs recorded:** 90/90 (100%)  ·  **Host(s):** www.taylorsvilleut.gov, www.utah.gov
- **How the text was obtained:** pdftotext-layout (81), derived-from-minutes (6), tesseract-ocr (3)

## Utah Public Notice backfill

- **Documents indexed:** 17  ·  **Date range:** 2020-01-29 to 2026-03-24
- **Direct source URLs recorded:** 17/17 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (raw retained; converted only where promoted) (15), pdftotext-layout (1), ocr-tesseract (1)

## Meeting-video transcripts

- **Documents indexed:** 1  ·  **Date range:** 2024-05-15 to 2024-05-15
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp --write-auto-sub (YouTube ASR auto-captions), cleaned to text/ (1)

## Campaign-finance disclosures

- **Documents indexed:** 71  ·  **Date range:** 2017-02-15 to 2026-03-01
- **Direct source URLs recorded:** 71/71 (100%)  ·  **Host(s):** www.taylorsvilleut.gov
- **How the text was obtained:** none (acquisition-only; scanned image PDF, OCR/vision deferred) (42), none (acquisition-only; born-digital text layer present, pdftotext deferred) (28), duplicate-excluded (byte-identical md5 to doc10635; the 2025 annual mis-posted under the 2024 label — see campaign_finance/CLAUDE.md) (1)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
