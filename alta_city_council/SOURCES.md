# Sources — Alta civic data

Civic records of the Town of Alta (~380 residents, a Little Cottonwood Canyon ski-resort town) Town Council and Planning Commission, 2020-present, plus municipal election results. Alta uses Utah's Town form: 4 at-large councilmembers + a VOTING Mayor (max council roll = 5). Minutes are enumerated via Utah Public Notice (council body 1601, PC body 1602). Alta publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-29 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py alta`.

## Council meeting minutes

- **Published by:** Alta Town Clerk
- **Portal:** Utah Public Notice (utah.gov/pmn; council body 1601)
- **Documents indexed:** 85  ·  **Date range:** 2020-02-12 to 2026-06-17
- **Direct source URLs recorded:** 85/85 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdf-text (49), ocr (36)
- **Note:** Born-digital text PDFs. Named per-member roll calls INCLUDING the Mayor (Town form - the mayor votes; max tally 5). Sparse by design: the Town Council meets monthly (2nd Wednesday, ~12/yr). Advisory Budget/Capital committee minutes are excluded (not the Town Council body).

## Planning Commission minutes

- **Published by:** Alta Planning Commission
- **Portal:** Utah Public Notice (utah.gov/pmn; body 1602)
- **Documents indexed:** 17  ·  **Date range:** 2022-06-02 to 2025-12-17
- **Direct source URLs recorded:** 17/17 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** ocr (13), pdf-text (4)
- **Note:** Alta's Planning Commission (Land Use Authority) meets 4th Wednesday AS-NEEDED (often cancelled) - thin but real (17 docs 2022-06 -> 2025-12; none 2020-2021). Votes are tally-only in this era.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Alta publishes no written public comments - comment is in-person / submit-only, not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** filtered directly from the county canonical (clean_elections.py) (1)
- **Note:** Filtered from the canonical Salt Lake County results - genuine Town-of-Alta contests only (COUNCIL AT LARGE + ALTA MAYOR); the ALTA CANYON RECREATION special-service-district contests are EXCLUDED (not the Town). At-large multi-seat races.

## Agenda packets / staff reports

- **Documents indexed:** 847  ·  **Date range:** 2020-01-08 to 2026-07-08
- **Direct source URLs recorded:** 847/847 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (829), none (image-only; vision/OCR required) (17), claude_vision (1)

## Housing plans / general plan

- **Documents indexed:** 2  ·  **Date range:** 2016 to 2016
- **Direct source URLs recorded:** 2/2 (100%)  ·  **Host(s):** storage.googleapis.com
- **How the text was obtained:** pdftotext -layout (2)

## Ordinances (adoption record)

- **Documents indexed:** 50  ·  **Date range:** 2020-10-14 to 2026-06-26
- **Direct source URLs recorded:** 50/50 (100%)  ·  **Host(s):** storage.googleapis.com, www.utah.gov
- **How the text was obtained:** tesseract 5 OCR @300dpi (pdftoppm PNG) (25), pdftotext -layout (19), na (6)

## Utah Public Notice backfill

- **Documents indexed:** 5  ·  **Date range:** 2020-05-06 to 2024-08-14
- **Direct source URLs recorded:** 5/5 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (4), tesseract-ocr (1)

## Meeting-video transcripts

- **Documents indexed:** 172  ·  **Date range:** 2020-04-04 to 2026-07-08
- **Direct source URLs recorded:** 172/172 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** flat-playlist catalog (caption not downloaded) (158), yt-dlp --write-auto-sub (en) + vtt-clean -> text/<date>.md (14)

## Campaign-finance disclosures

- **Documents indexed:** 36  ·  **Date range:** 2021-10-08 to 2025-12-04
- **Direct source URLs recorded:** 36/36 (100%)  ·  **Host(s):** municipal.utah.gov, storage.googleapis.com
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (36)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
