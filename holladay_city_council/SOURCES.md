# Sources — Holladay civic data

Civic records of the Holladay City Council (with in-session RDA and LBA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2007 (incorporated 1999). Minutes are published on Utah Public Notice (council body 388, PC body 389). Holladay is Council-Manager: 5 district councilmembers + a VOTING Mayor (max council roll = 6); the City Manager is the executive. Holladay publishes no written public-comment compilations (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py holladay`.

## Council meeting minutes

- **Published by:** Holladay City Recorder
- **Portal:** Utah Public Notice (utah.gov/pmn; council body 388); city Revize (holladayut.gov) + SuiteOne mirror
- **Documents indexed:** 152  ·  **Date range:** 2020-01-08 to 2026-04-16
- **Direct source URLs recorded:** 152/152 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdf-text (152)
- **Note:** Born-digital text PDFs. The MAYOR VOTES (max council roll = 6). Two vote-grammar eras (2020-21 prose 'in favor'; 2022+ 'Name-Aye/Yes' - printed Yes/No normalized to Aye/Nay per SCHEMA_SPEC §4). Council also convenes in-session as the RDA and LBA (body=RDA / body=LBA). 25 honest gaps (retreats/pending) in minutes_unrecovered.csv.

## Planning Commission minutes

- **Published by:** Holladay City Planning Division
- **Portal:** Utah Public Notice (utah.gov/pmn; body 389)
- **Documents indexed:** 71  ·  **Date range:** 2020-01-07 to 2026-04-28
- **Direct source URLs recorded:** 71/71 (100%)  ·  **Host(s):** cityofholladay.com, www.utah.gov
- **How the text was obtained:** pdf-text (71)
- **Note:** Holladay runs its own 7-member Planning Commission (Tuesday). NOTE: Holladay posts PC minutes to PMN only intermittently - 2026-07-16: the 2020 H1 + 2021 H1 PC minutes (27 docs) were recovered from the former cityofholladay.com WordPress site via Wayback and promoted (provenance=wayback_minutes); 2020 H2, 2021 H2 and all of 2023 remain genuine gaps (62 rows in minutes_unrecovered.csv; dead on PMN/Revize/SuiteOne/Wayback).

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Holladay publishes no written public comments - emailed comments are read aloud + paraphrased inline; no eComment portal, no correspondence archive; submit-only (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 2  ·  **Date range:** 2019 to 2021
- **Direct source URLs recorded:** 2/2 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (2)
- **Note:** Filtered from the canonical Salt Lake County results; 2019 general recovered from raw SOVC (HOL Council sheets), 2021 re-parsed for privacy suppression. Cycle A = Mayor+D1+D3, Cycle B = D2/D4/D5.

## Agenda packets / staff reports

- **Documents indexed:** 78  ·  **Date range:** 2025-01-07 to 2026-07-16
- **Direct source URLs recorded:** 78/78 (100%)  ·  **Host(s):** holladayut.suiteonemedia.com
- **How the text was obtained:** pdftotext -layout (78)

## Housing plans / general plan

- **Documents indexed:** 11  ·  **Date range:** 2016-07-14 to 2025-11
- **Direct source URLs recorded:** 11/11 (100%)  ·  **Host(s):** holladayut.gov, jobs.utah.gov, www.utah.gov
- **How the text was obtained:** pdftotext -layout (10), ocr (tesseract 5.5.0, 200dpi) (1)

## Ordinances (adoption record)

- **Documents indexed:** 123  ·  **Date range:** 2020-02-06 to 2026-05-21
- **Direct source URLs recorded:** 123/123 (100%)  ·  **Host(s):** holladayut.gov, www.utah.gov
- **How the text was obtained:** minutes-citation (derived from ../meeting_minutes/all_votes.csv; no independent ordinance document) (102), tesseract-ocr (15), pdftotext (6)

## Utah Public Notice backfill

- **Documents indexed:** 27  ·  **Date range:** 2020-01-07 to 2021-06-15
- **Direct source URLs recorded:** 27/27 (100%)  ·  **Host(s):** cityofholladay.com
- **How the text was obtained:** pdftotext-layout (27)

## Meeting-video transcripts

- **Documents indexed:** 81  ·  **Date range:** 2020-12-15 to 2026-07-07
- **Direct source URLs recorded:** 81/81 (100%)  ·  **Host(s):** holladayut.suiteonemedia.com, www.youtube.com
- **How the text was obtained:** none (SuiteOne video-only MP4; no caption track; ASR via Whisper deferred) (75), yt-dlp --write-auto-sub (YouTube ASR, en) -> clean_captions_holladay.py (6)

## Campaign-finance disclosures

- **Documents indexed:** 52  ·  **Date range:** 2017-08-08 to 2026-01-31
- **Direct source URLs recorded:** 52/52 (100%)  ·  **Host(s):** municipal.utah.gov, www.holladayut.gov
- **How the text was obtained:** none (acquisition-only; scanned image PDF, OCR/vision deferred) (39), none (acquisition-only; born-digital text PDF) (13)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
