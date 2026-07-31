# Sources — Kearns civic data

Civic records of the Kearns City Council (formerly Metro Township) and its MSD-staffed Planning Commission, plus municipal election results. Kearns was a metro township 2017-2024, converted to a CITY 2024-05-01 (Utah H.B. 35); the first city election was Nov 2025 (Mayor Jesse Valdez, Utah's first Hispanic mayor). City-era: directly-elected Mayor who VOTES + 4 district councilmembers (max council roll = 5). Minutes are on Utah PMN (the city site is Cloudflare-blocked). Kearns publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py kearns`.

## Council meeting minutes

- **Published by:** Kearns City Recorder (via Greater Salt Lake MSD)
- **Portal:** Utah Public Notice (utah.gov/pmn; council body 5823)
- **Documents indexed:** 119  ·  **Date range:** 2018-07-09 to 2026-05-29
- **Direct source URLs recorded:** 119/119 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** text (96), ocr (23)
- **Note:** COVERAGE: written 'Meeting Minutes' ARE published to PMN body 5823 across the township era; the 2026-07-12 backfill harvested them, so council minutes now run 2018-07-09 -> 2026 (85 township-era docs + 32 city-era). Format: OCR for scanned minutes, text for born-digital (incl. 2 .docx via textutil). REMAINING GAPS (minutes_unrecovered.csv, 41 rows): 25 township meetings (2017-01 -> 2018-06) whose 'Meeting Minutes' attachment WAS published but whose file blob has been purged from PMN's pre-~July-2018 file store (file_id<~450000 now 404; notice link is stale; not on the Internet Archive either); 7 township meetings that posted only an agenda + MP3 audio (no minutes ever published); 9 recent meetings not yet approved/posted. Votes are narrative-tally (unanimous rolls unnamed/tally-only; abstainers named), EXCEPT some 2018-2023 minutes print a full named roll call - those per-member Ayes/Nays are captured verbatim. City-era Mayor votes (max 5). A CRA convenes in-recess (referenced in docs) but its own PMN body is separate/un-acquired (0 CRA rows).

## Planning Commission minutes

- **Published by:** Greater Salt Lake MSD Planning & Development (for Kearns)
- **Portal:** Utah Public Notice (utah.gov/pmn; body 1561)
- **Documents indexed:** 44  ·  **Date range:** 2019-03-11 to 2026-06-01
- **Direct source URLs recorded:** 44/44 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** text (44)
- **Note:** Kearns' Planning Commission is MSD-administered; approved-minutes PDFs begin 2019-03 (2017-2018 posted agendas only). Land-use cases keyed OAM<YYYY>-<NNNNNN>; recommends to Council. Born-digital.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Kearns publishes no written public comments - in-meeting 3-min input + email to the MSD recorder; submit-only, not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** parsed by content directly from the raw SLCo Clerk SOVC workbooks (clean_elections.py; the county canonical long file drops 2019 / merges foreign candidates for Kearns) (1)
- **Note:** ⚠ Parsed from RAW SOVC by content - the canonical slco_municipal_results_long.csv is CORRUPTED for Kearns (2019 dropped entirely; the 2025 SheetNN->contest mapping merged OTHER municipalities' candidates under 'CITY OF KEARNS MAYOR'). kearns_races.csv is authoritative; the county-grain election_result tag for Kearns is unreliable (see TODO.md). Oquirrh Park / Improvement District / MSD decoys excluded.

## Agenda packets / staff reports

- **Documents indexed:** 80  ·  **Date range:** 2019-01-14 to 2026-07-13
- **Direct source URLs recorded:** 80/80 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (79), none (image-only PDF; vision/OCR required) (1)

## Housing plans / general plan

- **Documents indexed:** 8  ·  **Date range:** 2020 to 2025
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** jobs.utah.gov, msd.utah.gov
- **How the text was obtained:** pdftotext -layout (4), pdftotext/pymupdf page-range extract (4)

## Ordinances (adoption record)

- **Documents indexed:** 223  ·  **Date range:** 2017-02-01 to 2026-06-11
- **Direct source URLs recorded:** 223/223 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com
- **How the text was obtained:** pdftotext_layout (116), ocr_tesseract (104), textutil_docx (3)

## Utah Public Notice backfill

- **Documents indexed:** 3  ·  **Date range:** 2019-04-08 to 2025-09-08
- **Direct source URLs recorded:** 3/3 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (2), tesseract-ocr (1)

## Meeting-video transcripts

- **Documents indexed:** 288  ·  **Date range:** 2016-02-08 to 2026-07-13
- **Direct source URLs recorded:** 288/288 (100%)  ·  **Host(s):** www.utah.gov, www.youtube.com
- **How the text was obtained:** none (PMN audio MP3 — no caption track; Whisper candidate, not run) (218), none (PMN file purged/unavailable — HTTP 404; pre-~2018-07 blob rot) (58), yt-dlp --write-auto-sub en (YouTube ASR); VTT->text via kearns_clean_captions.py (11), none (YouTube video has no caption track as of retrieval) (1)

## Campaign-finance disclosures

- **Documents indexed:** 38  ·  **Date range:** 2016-06-01 to 2021-12-01
- **Direct source URLs recorded:** 38/38 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (38)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
