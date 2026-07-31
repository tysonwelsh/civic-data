# Sources — West Valley City civic data

Civic records of the West Valley City Council and Planning Commission, 2020–present. Minutes are published on the city's self-hosted Hyland OnBase 'Agenda Online' portal (ob.wvc-ut.gov). West Valley publishes no written public-comment compilations. Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-31 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py west_valley`.

## Council meeting minutes

- **Published by:** West Valley City Recorder
- **Portal:** OnBase Agenda Online (ob.wvc-ut.gov)
- **Documents indexed:** 555  ·  **Date range:** 2020-01-07 to 2026-06-23
- **Direct source URLs recorded:** 555/555 (100%)  ·  **Host(s):** ob.wvc-ut.gov, www.utah.gov
- **How the text was obtained:** md (465), text (90)
- **Note:** Born-digital documents.

## Planning Commission minutes

- **Published by:** West Valley City Community & Economic Development
- **Portal:** OnBase Agenda Online (ob.wvc-ut.gov)
- **Documents indexed:** 264  ·  **Date range:** 2020-01-02 to 2026-05-27
- **Direct source URLs recorded:** 264/264 (100%)  ·  **Host(s):** ob.wvc-ut.gov
- **How the text was obtained:** text (264)
- **Note:** Born-digital documents.

## Public comments

- **Published by:** —
- **Portal:** —
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** West Valley publishes no written public comments (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** filtered directly from the county canonical (build_wvc_elections.py) (1)
- **Note:** County SOVC workbooks copied verbatim from a local mirror of the county results site; per-file URLs were not recorded.

## Agenda packets / staff reports

- **Documents indexed:** 965  ·  **Date range:** 2020-01-02 to 2026-07-08
- **Direct source URLs recorded:** 965/965 (100%)  ·  **Host(s):** ob.wvc-ut.gov
- **How the text was obtained:** pdftotext (965)

## Housing plans / general plan

- **Documents indexed:** 18  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 18/18 (100%)  ·  **Host(s):** jobs.utah.gov, www.wvc-ut.gov
- **How the text was obtained:** html-strip (12), pdftotext-layout (6)

## Ordinances (adoption record)

- **Documents indexed:** 329  ·  **Date range:** 2020-01-07 to 2026-06-23
- **Direct source URLs recorded:** 329/329 (100%)  ·  **Host(s):** ob.wvc-ut.gov, www.wvc-ut.gov
- **How the text was obtained:** minutes-derived (via minutes document) (214), pdf-pdftotext (106), minutes-derived-consent (via minutes document) (9)

## Utah Public Notice backfill

- **Documents indexed:** 13  ·  **Date range:** 2020-01-17 to 2026-06-09
- **Direct source URLs recorded:** 13/13 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (13)

## Meeting-video transcripts

- **Documents indexed:** 461  ·  **Date range:** 2020-01-07 to 2026-06-23
- **Direct source URLs recorded:** 461/461 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** mapped_not_fetched (451), yt-dlp_auto_sub (10)

## Campaign-finance disclosures

- **Documents indexed:** 105  ·  **Date range:** 2019-11-30 to 2025-12-29
- **Direct source URLs recorded:** 105/105 (100%)  ·  **Host(s):** www.wvc-ut.gov
- **How the text was obtained:** ocr:tesseract --psm 6 @300dpi (pdftoppm) (63), pdftotext -layout (42)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
