# Sources — White City civic data

Civic records of the White City Council and its MSD-staffed Planning Commission from 2018 (earliest published minutes; incorporated as a metro township 2017, converted to a CITY 2024-05-01 under Utah H.B. 35), plus municipal election results. Council minutes are published on the city's Streamline CMS (whitecity.utah.gov), mirrored on Utah PMN (body 5805); PC minutes exist only on PMN (body 5879). White City is a 5-member at-large body; the presiding Chair (township era) / directly-elected Mayor (city era, 2026+) VOTES (max tally 5). White City publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py white_city`.

## Council meeting minutes

- **Published by:** White City Recorder
- **Portal:** Streamline CMS (whitecity.utah.gov); Utah PMN body 5805 fallback
- **Documents indexed:** 124  ·  **Date range:** 2018-01-04 to 2026-06-11
- **Direct source URLs recorded:** 124/124 (100%)  ·  **Host(s):** whitecity.utah.gov, www.utah.gov
- **How the text was obtained:** text (112), ocr (12)
- **Note:** Born-digital text PDFs (12 mid/late-2024 minutes were image-only scans recovered via OCR; format=ocr). Three vote-grammar eras across the ~Jan-2026 seam: narrative-tally (2018-2025), narrative-named-dissent (2020-2022), and full named roll calls (2026+). The Chair/Mayor votes in every era (max tally 5). 2017 is agenda-only (no minutes published).

## Planning Commission minutes

- **Published by:** White City Planning Commission (MSD-staffed; minuted by Greater Salt Lake MSD Planning & Development Services)
- **Portal:** Utah Public Notice (utah.gov/pmn; PC body 5879)
- **Documents indexed:** 22  ·  **Date range:** 2019-01-29 to 2025-05-20
- **Direct source URLs recorded:** 22/22 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** text (22)
- **Note:** RECOVERED FROM PMN BODY 5879 (promoted 2026-07-16): the Streamline site publishes no PC minutes, but PMN carries a sporadic MSD 'MEETING MINUTE SUMMARY' series - 22 minutes docs 2019-01-29 -> 2025-05-20 (106 motions, provenance=pmn_minutes). MSD narrative-tally style: only mover/seconder (+ a named abstainer) are named; unanimous rolls are tally-only placeholders; hearing open/close/adjourn motions print no outcome (empty result = honest NULL). Land-use cases keyed OAM/EXP/WVR + county file #. The series is sporadic: 28 further PC dates were noticed with agendas but no minutes were ever posted (minutes_unrecovered.csv); many other months the PC simply cancelled.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** White City publishes no written public comments - in-meeting speaker input only, no eComment portal; submit-only (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 2  ·  **Date range:** 2019 to 2019
- **Direct source URLs recorded:** 2/2 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (1), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2019 metro-township council recovered from raw SOVC. 2017 & 2021 are genuine no-election years (initial council elected Nov-2016; some seats filled uncontested). The White City Water Improvement District + 2015 MSD/incorporation ballot questions are EXCLUDED (not the city).

## Agenda packets / staff reports

- **Documents indexed:** 99  ·  **Date range:** 2018-02-01 to 2026-07-02
- **Direct source URLs recorded:** 99/99 (100%)  ·  **Host(s):** whitecity.utah.gov
- **How the text was obtained:** pdftotext -layout (99)

## Housing plans / general plan

- **Documents indexed:** 8  ·  **Date range:** 2019-11-14 to 2025
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** jobs.utah.gov, msd.utah.gov, whitecity.specialdistrict.org, whitecity.utah.gov
- **How the text was obtained:** pdftotext/pymupdf page-range extract (4), pdftotext -layout (3), tesseract 5.5 OCR (300dpi) (1)

## Ordinances (adoption record)

- **Documents indexed:** 136  ·  **Date range:** 2017-01-05 to 2025-12-04
- **Direct source URLs recorded:** 136/136 (100%)  ·  **Host(s):** s3-us-west-2.amazonaws.com
- **How the text was obtained:** ocr_tesseract (99), pdftotext_layout (37)

## Utah Public Notice backfill

- **Documents indexed:** 31  ·  **Date range:** 2019-01-29 to 2025-05-20
- **Direct source URLs recorded:** 31/31 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (30), ocr (tesseract; embedded text layer corrupt) (1)

## Meeting-video transcripts

- **Documents indexed:** 13  ·  **Date range:** 2025-07-10 to 2026-06-04
- **Direct source URLs recorded:** 13/13 (100%)  ·  **Host(s):** whitecity.utah.gov
- **How the text was obtained:** none (audio MP3/M4A — no caption track; Whisper candidate, not run) (13)

## Campaign-finance disclosures

- **Documents indexed:** 28  ·  **Date range:** 2025-01-15 to 2026-01-29
- **Direct source URLs recorded:** 28/28 (100%)  ·  **Host(s):** whitecity.utah.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (28)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
