# Sources — Vineyard civic data

Civic records of the Vineyard City Council and Planning Commission, 2020–present. Minutes are published via the city's CivicClerk portal (vineyardut.api.civicclerk.com), with one meeting recovered from the Utah Public Notice Website. Vineyard publishes no written public-comment compilations. Election results come from rcvis.com (2019–2023 ranked-choice rounds) and the Utah state Enhanced Voting portal (2025).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py vineyard`.

## Council meeting minutes

- **Published by:** Vineyard City Recorder
- **Portal:** CivicClerk (vineyardut.api.civicclerk.com)
- **Documents indexed:** 172  ·  **Date range:** 2020-01-08 to 2026-06-09
- **Direct source URLs recorded:** 172/172 (100%)  ·  **Host(s):** vineyardut.api.civicclerk.com, www.utah.gov
- **How the text was obtained:** text (135), plainText=false) (26), ocr (11)
- **Note:** Born-digital text streams (a few OCR).

## Planning Commission minutes

- **Published by:** Vineyard Planning Commission
- **Portal:** CivicClerk (vineyardut.api.civicclerk.com)
- **Documents indexed:** 102  ·  **Date range:** 2020-01-08 to 2026-05-06
- **Direct source URLs recorded:** 102/102 (100%)  ·  **Host(s):** vineyardut.api.civicclerk.com, www.utah.gov
- **How the text was obtained:** text (102)
- **Note:** Born-digital text streams.

## Public comments

- **Published by:** —
- **Portal:** —
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Vineyard publishes no written public comments (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** rcvis.com (RCV rounds 2019–2023); Utah Enhanced Voting portal (2025, Utah County)
- **Portal:** rcvis.com / electionresults.utah.gov
- **Documents indexed:** 12  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 7/12 (58%)  ·  **Host(s):** www.rcvis.com
- **How the text was obtained:** html (raw retained verbatim) (7), json (raw retained verbatim) (5)
- **Note:** Raw HTML/JSON mirrored verbatim in election_results/raw/; per-file URLs were not recorded (rcvis slugs documented in CLAUDE.md).

## Agenda packets / staff reports

- **Documents indexed:** 926  ·  **Date range:** 2014-01-08 to 2026-06-23
- **Direct source URLs recorded:** 926/926 (100%)  ·  **Host(s):** vineyardut.api.civicclerk.com
- **How the text was obtained:** civicclerk_odata (926)

## Housing plans / general plan

- **Documents indexed:** 7  ·  **Date range:** 2019-05 to 2025
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** jobs.utah.gov, s3-us-west-2.amazonaws.com, www.vineyardutah.gov
- **How the text was obtained:** pdftotext-layout (7)

## Ordinances (adoption record)

- **Documents indexed:** 84  ·  **Date range:** 2020-03-11 to 2025-10-22
- **Direct source URLs recorded:** 83/84 (99%)  ·  **Host(s):** vineyardut.api.civicclerk.com, www.utah.gov
- **How the text was obtained:** reconstructed from meeting_minutes/planning_commission motion text (CivicClerk minutes) (via minutes document) (78), pdftotext -layout (Utah Public Notice signed ordinance PDF) (5), reconstructed from meeting_minutes/planning_commission motion text (CivicClerk minutes) (1)

## Utah Public Notice backfill

- **Documents indexed:** 296  ·  **Date range:** 2015-01-14 to 2026-05-19
- **Direct source URLs recorded:** 296/296 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** none (216), pdftotext-layout (77), tesseract-ocr (3)

## Meeting-video transcripts

- **Documents indexed:** 34  ·  **Date range:** 2019-09-25 to 2020-12-09
- **Direct source URLs recorded:** 34/34 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp --flat-playlist channel enumeration; caption not downloaded (sample-only policy) (24), yt-dlp --write-auto-sub --sub-langs en (YouTube ASR) (10)

## Campaign-finance disclosures

- **Documents indexed:** 59  ·  **Date range:** 2015-08-15 to 2025-09-08
- **Direct source URLs recorded:** 59/59 (100%)  ·  **Host(s):** web.archive.org, www.vineyardutah.gov
- **How the text was obtained:** ocr:tesseract-psm6@300dpi (39), pdftotext_layout (16), unreadable:archive_capture_truncated (4)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
