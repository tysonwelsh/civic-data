# Sources — Nephi civic data

Civic records of the Nephi City Council and Planning Commission, 2020–present. Minutes are published on the city's CivicPlus CivicEngage AgendaCenter (nephi.utah.gov). Nephi publishes no written public-comment compilations. Election results come from the Utah state Enhanced Voting portal (Juab County, 2023+) and archived news canvasses for 2019/2021 (no county archive exists).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-31 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py nephi`.

## Council meeting minutes

- **Published by:** Nephi City Recorder
- **Portal:** CivicPlus AgendaCenter (nephi.utah.gov)
- **Documents indexed:** 251  ·  **Date range:** 2020-01-07 to 2026-06-16
- **Direct source URLs recorded:** 251/251 (100%)  ·  **Host(s):** www.nephi.utah.gov, www.utah.gov
- **How the text was obtained:** text (251)
- **Note:** Born-digital documents.

## Planning Commission minutes

- **Published by:** Nephi City Planning Commission
- **Portal:** CivicPlus AgendaCenter (nephi.utah.gov)
- **Documents indexed:** 72  ·  **Date range:** 2020-01-08 to 2026-05-13
- **Direct source URLs recorded:** 72/72 (100%)  ·  **Host(s):** www.nephi.utah.gov
- **How the text was obtained:** text (68), docx (4)
- **Note:** Born-digital documents (some .docx).

## Public comments

- **Published by:** —
- **Portal:** —
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Nephi publishes no written public comments (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Utah Enhanced Voting portal (Juab County); archived news canvasses (2019 Deseret News, 2021 Mid-Utah Radio)
- **Portal:** electionresults.utah.gov / juabcounty.gov
- **Documents indexed:** 12  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 3/12 (25%)  ·  **Host(s):** juabcounty.gov, midutahradio.com, www.deseret.com
- **How the text was obtained:** json (raw retained verbatim) (8), html (raw retained verbatim) (3), pdf (raw retained verbatim) (1)
- **Note:** No pre-existing Juab County election archive; 2019/2021 numbers rest on archived unofficial canvasses (documented in election_results/CLAUDE.md).

## Agenda packets / staff reports

- **Documents indexed:** 328  ·  **Date range:** 2020-01-07 to 2026-06-16
- **Direct source URLs recorded:** 328/328 (100%)  ·  **Host(s):** www.nephi.utah.gov
- **How the text was obtained:** none (raw retained) (328)

## Housing plans / general plan

- **Documents indexed:** 6  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 6/6 (100%)  ·  **Host(s):** jobs.utah.gov, www.nephi.utah.gov
- **How the text was obtained:** pdftotext-layout (6)

## Ordinances (adoption record)

- **Documents indexed:** 103  ·  **Date range:** 2020-01-21 to 2026-06-02
- **Direct source URLs recorded:** 103/103 (100%)  ·  **Host(s):** www.nephi.utah.gov, www.utah.gov
- **How the text was obtained:** reconstructed from meeting_minutes (ordinance number in minutes header/motion text) (via minutes document) (80), reconstructed from meeting_minutes; same-day multi-ordinance, motion linked POSITIONALLY (suffix letter truncated in all_votes source) (via minutes document) (10), minutes header/motion text only; no discrete vote row on adoption date (audit signal) (via minutes document) (8), PMN Notice-of-Ordinance PDF corroborates number+subject; linked to council motion (5)

## Utah Public Notice backfill

- **Documents indexed:** 16  ·  **Date range:** 2020-11-24 to 2026-04-14
- **Direct source URLs recorded:** 16/16 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (9), textutil -convert txt (7)

## Meeting-video transcripts

- **Documents indexed:** 5  ·  **Date range:** 2026-05-05 to 2026-08-11
- **Direct source URLs recorded:** 5/5 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp_auto_sub_en_vtt (4), not_yet_aired_scheduled_live (1)

## Campaign-finance disclosures

- **Documents indexed:** 43  ·  **Date range:** 2019-11-05 to 2025-12-08
- **Direct source URLs recorded:** 43/43 (100%)  ·  **Host(s):** www.nephi.utah.gov
- **How the text was obtained:** ocr:tesseract --psm 6 @200dpi (32), ocr:tesseract --psm 6 @150dpi (11)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
