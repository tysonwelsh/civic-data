# Sources — Provo civic data

Civic records of the Provo Municipal Council and Planning Commission, 2020–present. Council minutes and agenda packets are published on the city's Hyland OnBase 'Agenda Online' portal (agendas.provo.gov); recent Planning Commission minutes on the CivicPlus AgendaCenter (provo.gov). Written public comments were harvested from council agenda packets. Election results are produced by the Utah County Clerk (vote.utahcounty.gov).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py provo`.

## Council meeting minutes

- **Published by:** Provo Municipal Council Office / City Recorder
- **Portal:** OnBase Agenda Online (agendas.provo.gov)
- **Documents indexed:** 312  ·  **Date range:** 2020-01-07 to 2026-05-26
- **Direct source URLs recorded:** 312/312 (100%)  ·  **Host(s):** agendas.provo.gov, www.utah.gov
- **How the text was obtained:** pdf (310), pdf-ocr (1), text (1)
- **Note:** PDF minutes (one 2020 file OCR).

## Planning Commission minutes

- **Published by:** Provo Development Services
- **Portal:** CivicPlus AgendaCenter (provo.gov)
- **Documents indexed:** 28  ·  **Date range:** 2025-02-26 to 2026-07-08
- **Direct source URLs recorded:** 28/28 (100%)  ·  **Host(s):** www.provo.gov
- **How the text was obtained:** text (28)
- **Note:** Born-digital documents, 2025+ only (earlier PC minutes not published there).

## Public comments

- **Published by:** Provo Municipal Council Office
- **Portal:** OnBase Agenda Online (agendas.provo.gov) — agenda packets
- **Documents indexed:** 15  ·  **Date range:** 2020-05-05 to 2022-10-04
- **Direct source URLs recorded:** 15/15 (100%)  ·  **Host(s):** agendas.provo.gov
- **How the text was obtained:** pdftotext + page-walk comment classifier (15)
- **Note:** 138 packets scanned (record: public_comments/packets_scanned.csv); the 15 packets that contributed comments to the dataset are indexed here. Raw packet text retained under public_comments/raw/packet_txt/.

## Municipal election results

- **Published by:** Utah County Clerk
- **Portal:** vote.utahcounty.gov
- **Documents indexed:** 14  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 14/14 (100%)  ·  **Host(s):** vote.utahcounty.gov
- **How the text was obtained:** pdf (raw retained verbatim) (9), csv (raw retained verbatim) (5)
- **Note:** County SOVC CSVs / results PDFs mirrored verbatim in election_results/raw/; per-file URLs were not recorded (hashed /cms/uploads/ names, see CLAUDE.md).

## Agenda packets / staff reports

- **Documents indexed:** 391  ·  **Date range:** 2020-01-07 to 2026-07-08
- **Direct source URLs recorded:** 391/391 (100%)  ·  **Host(s):** agendas.provo.gov, www.provo.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url with session cookie+Referer, use vision/OCR) (306), not_retrieved (index-only; fetch source_url, use vision/OCR) (85)

## Housing plans / general plan

- **Documents indexed:** 6  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 6/6 (100%)  ·  **Host(s):** jobs.utah.gov, www.provo.gov
- **How the text was obtained:** pdftotext-layout (6)

## Ordinances (adoption record)

- **Documents indexed:** 213  ·  **Date range:** 2020-02-18 to 2026-06-23
- **Direct source URLs recorded:** 213/213 (100%)  ·  **Host(s):** agendas.provo.gov, www.utah.gov
- **How the text was obtained:** motion_citation (all_votes.csv) (via minutes document) (126), pmn_docx_notice; python-docx-xml (87)

## Utah Public Notice backfill

- **Documents indexed:** 391  ·  **Date range:** 2020-01-08 to 2026-06-24
- **Direct source URLs recorded:** 391/391 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (390), textutil (1)

## Meeting-video transcripts

- **Documents indexed:** 10  ·  **Date range:** 2024-03-05 to 2025-12-16
- **Direct source URLs recorded:** 10/10 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp auto-sub en-orig vtt; rolling-window dedup (clean_vtt.py) (10)

## Campaign-finance disclosures

- **Documents indexed:** 41  ·  **Date range:** 2021-06-24 to 2025-12-04
- **Direct source URLs recorded:** 41/41 (100%)  ·  **Host(s):** www.provo.gov
- **How the text was obtained:** pdftotext -layout (37), tesseract OCR (pdftoppm; OSD-derotated) (4)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
