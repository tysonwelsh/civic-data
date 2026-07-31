# Sources — Logan civic data

Civic records of the Logan Municipal Council and Planning Commission, 2020–present. Minutes are published on the city's Revize CMS (loganutah.gov; files served from the Revize CDN). Logan publishes no written public-comment compilations. Election results: Logan administered its own 2019/2021 municipal elections (City Recorder); from 2023 the Cache County Clerk administers them; 2025 results come from the Utah state Enhanced Voting portal.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py logan`.

## Council meeting minutes

- **Published by:** Logan City Recorder
- **Portal:** Revize CMS (loganutah.gov)
- **Documents indexed:** 198  ·  **Date range:** 2020-01-07 to 2026-06-02
- **Direct source URLs recorded:** 198/198 (100%)  ·  **Host(s):** cms9files.revize.com
- **How the text was obtained:** text (196), text-draft (2)
- **Note:** Static PDF files linked from year-by-year listing pages.

## Planning Commission minutes

- **Published by:** Logan Community Development Department
- **Portal:** Revize CMS (loganutah.gov)
- **Documents indexed:** 131  ·  **Date range:** 2020-01-09 to 2026-07-09
- **Direct source URLs recorded:** 131/131 (100%)  ·  **Host(s):** www.loganutah.gov
- **How the text was obtained:** text (78), ocr (52), text-draft (1)
- **Note:** Mix of born-digital and scanned (OCR) PDFs.

## Public comments

- **Published by:** —
- **Portal:** —
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Logan publishes no written public comments (see public_comments/AVAILABILITY.md); in-person speakers are logged from minutes in minutes_speaker_log.csv.

## Municipal election results

- **Published by:** Logan City Recorder (2019/2021); Cache County Clerk (2023+); Utah Enhanced Voting portal (2025)
- **Portal:** loganutah.gov / cachecounty.gov / electionresults.utah.gov
- **Documents indexed:** 17  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 5/17 (29%)  ·  **Host(s):** www.cachecounty.gov
- **How the text was obtained:** pdf (raw retained verbatim) (9), json (raw retained verbatim) (8)
- **Note:** Raw official PDFs/JSON mirrored in election_results/raw/; per-file URLs were not recorded.

## Agenda packets / staff reports

- **Documents indexed:** 1124  ·  **Date range:** 2022-01-04 to 2026-07-07
- **Direct source URLs recorded:** 1124/1124 (100%)  ·  **Host(s):** cms9files.revize.com, www.loganutah.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand) (959), claude_vision (165)

## Housing plans / general plan

- **Documents indexed:** 7  ·  **Date range:** 2018 to 2026
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** cms9files.revize.com, jobs.utah.gov
- **How the text was obtained:** pdftotext-layout (7)

## Ordinances (adoption record)

- **Documents indexed:** 496  ·  **Date range:** 2020-01-21 to 2026-07-01
- **Direct source URLs recorded:** 496/496 (100%)  ·  **Host(s):** cms9files.revize.com, www.loganutah.gov
- **How the text was obtained:** recorder_listing (323), recorder_pdf (162), minutes_motion_text (via minutes document) (11)

## Utah Public Notice backfill

- **Documents indexed:** 3  ·  **Date range:** 2020-03-03 to 2026-05-26
- **Direct source URLs recorded:** 3/3 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (3)

## Meeting-video transcripts

- **Documents indexed:** 153  ·  **Date range:** 2021-01-05 to 2026-06-30
- **Direct source URLs recorded:** 153/153 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** mapped_not_downloaded (143), yt-dlp_auto_sub_vtt (10)

## Campaign-finance disclosures

- **Documents indexed:** 45  ·  **Date range:** 2021-08-03 to 2025-12-04
- **Direct source URLs recorded:** 45/45 (100%)  ·  **Host(s):** www.loganutah.gov, www.loganutah.org
- **How the text was obtained:** ocr_tesseract (45)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
