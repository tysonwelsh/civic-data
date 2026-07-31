# Sources — St. George civic data

Civic records of the St. George City Council and Planning Commission, 2020–present. Minutes are published on the city's Revize CMS (sgcityutah.gov), with some meetings recovered from the Utah Public Notice Website. Written public comments are published as weekly PDF compilations on sgcityutah.gov. Election results are produced by the Washington County Clerk (washco.utah.gov).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py st_george`.

## Council meeting minutes

- **Published by:** St. George City Recorder
- **Portal:** Revize CMS (sgcityutah.gov); fallback: Utah Public Notice (utah.gov/pmn)
- **Documents indexed:** 308  ·  **Date range:** 2020-01-06 to 2026-07-02
- **Direct source URLs recorded:** 308/308 (100%)  ·  **Host(s):** sgcityutah.gov, www.utah.gov
- **How the text was obtained:** pdf (299), docx (8), doc (1)
- **Note:** Born-digital PDFs/doc files.

## Planning Commission minutes

- **Published by:** St. George Planning Division
- **Portal:** Revize CMS (sgcityutah.gov); Utah Public Notice (utah.gov/pmn)
- **Documents indexed:** 133  ·  **Date range:** 2020-01-14 to 2026-06-23
- **Direct source URLs recorded:** 133/133 (100%)  ·  **Host(s):** sgcityutah.gov, www.utah.gov
- **How the text was obtained:** text (133)
- **Note:** Born-digital documents.

## Public comments

- **Published by:** St. George City Council Office
- **Portal:** sgcityutah.gov (weekly 'Public Comments Received' PDFs)
- **Documents indexed:** 53  ·  **Date range:** 2023-05-05 to 2026-06-12
- **Direct source URLs recorded:** 53/53 (100%)  ·  **Host(s):** sgcityutah.gov
- **How the text was obtained:** claude-vision (extract_comments.py) (53)
- **Note:** Weekly PDFs mirrored under public_comments/raw/ with a full URL manifest (comments_json/_manifest.json).

## Municipal election results

- **Published by:** Washington County Clerk
- **Portal:** washco.utah.gov (files served from outpost.washco.utah.gov)
- **Documents indexed:** 13  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 10/13 (77%)  ·  **Host(s):** outpost.washco.utah.gov
- **How the text was obtained:** csv (raw retained verbatim) (7), pdf (raw retained verbatim) (6)
- **Note:** County CSV exports + precinct PDFs mirrored verbatim in election_results/raw/; the CLAUDE.md source table records the host and partial paths, not full URLs.

## Agenda packets / staff reports

- **Documents indexed:** 224  ·  **Date range:** 2022-01-03 to 2025-12-18
- **Direct source URLs recorded:** 224/224 (100%)  ·  **Host(s):** sgcityutah.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand) (224)

## Housing plans / general plan

- **Documents indexed:** 7  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** jobs.utah.gov, sgcityutah.gov
- **How the text was obtained:** pdftotext -layout (2), html_strip (1), pdftotext -layout -f 820 -l 833 (sidecar text/stgeorge-2023.txt) (1), pdftotext -layout -f 782 -l 794 (sidecar text/stgeorge-2024.txt) (1), pdftotext -layout -f 953 -l 971 (sidecar text/stgeorge-2025.txt) (1), pdftotext -layout -f 151 -l 152 (sidecar text/stgeorge-sb34.txt) (1)

## Ordinances (adoption record)

- **Documents indexed:** 258  ·  **Date range:** 2023-04-06 to 2026-07-02
- **Direct source URLs recorded:** 258/258 (100%)  ·  **Host(s):** sgcityutah.gov, www.utah.gov
- **How the text was obtained:** pdftotext -layout (Recorder Notice of Adoption); cross-matched to council motion citing same ordinance number (124), derived from meeting_minutes/all_votes.csv motion text (within-source linkage; no independent Recorder notice posted for this date) (via minutes document) (91), pdftotext -layout (Recorder Notice of Adoption); no council motion cited this number (likely consent-calendar adoption) — matched by adoption date to that meeting (39), pdftotext -layout (Recorder Notice of Adoption); no matching council meeting in all_votes.csv (3), pdftotext -layout (PMN-hosted codified Title 10) (1)

## Utah Public Notice backfill

- **Documents indexed:** 20  ·  **Date range:** 2020-06-23 to 2025-01-14
- **Direct source URLs recorded:** 20/20 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (18), textutil docx->txt (1), pdftotext -layout (178pp agenda packet) (1)

## Meeting-video transcripts

- **Documents indexed:** 47  ·  **Date range:** 2023-01-05 to 2026-01-22
- **Direct source URLs recorded:** 47/47 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** none (37), yt-dlp --write-auto-sub (YouTube ASR, en-orig) + clean_vtt.py dedupe (10)

## Campaign-finance disclosures

- **Documents indexed:** 104  ·  **Date range:** 2021-08-03 to 2025-12-04
- **Direct source URLs recorded:** 104/104 (100%)  ·  **Host(s):** sgcityutah.gov, web.archive.org
- **How the text was obtained:** ocr:tesseract-psm6@200dpi (104)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
