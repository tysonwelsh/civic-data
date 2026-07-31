# Sources — Lehi civic data

Civic records of the Lehi City Council and Planning Commission, 2020–present. Minutes are published by the Lehi City Recorder on the city's Granicus portal (lehi.granicus.com). Public comments appear only inside council minutes (no separate comment channel). Election results are produced by the Utah County Clerk (vote.utahcounty.gov) and the Utah state Enhanced Voting portal (electionresults.utah.gov); ranked-choice rounds via rcvis.com. Expansion datasets (agenda packets, housing/general plan, ordinances, public-notice backfill, transcripts, campaign finance) carry their own per-document URLs.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py lehi`.

## Council meeting minutes

- **Published by:** Lehi City Recorder
- **Portal:** Granicus (lehi.granicus.com)
- **Documents indexed:** 175  ·  **Date range:** 2020-01-14 to 2026-01-27
- **Direct source URLs recorded:** 175/175 (100%)  ·  **Host(s):** lehi.granicus.com
- **How the text was obtained:** text (175)
- **Note:** Born-digital PDFs served via MinutesViewer/DocumentViewer.

## Planning Commission minutes

- **Published by:** Lehi City Planning Department
- **Portal:** Granicus (lehi.granicus.com)
- **Documents indexed:** 161  ·  **Date range:** 2020-01-09 to 2026-06-11
- **Direct source URLs recorded:** 161/161 (100%)  ·  **Host(s):** lehi.granicus.com
- **How the text was obtained:** text (161)
- **Note:** Born-digital PDFs, same portal as council minutes.

## Public comments

- **Published by:** Lehi City Recorder (via council minutes)
- **Portal:** Granicus (lehi.granicus.com)
- **Documents indexed:** 4  ·  **Date range:** 2020-03-31 to 2020-06-23
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** lehi.granicus.com
- **How the text was obtained:** transcribed from minutes text (4)
- **Note:** Lehi publishes no separate comment compilations; the few written comments read into the record live inside the cited minutes documents.

## Municipal election results

- **Published by:** Utah County Clerk; Utah Lt. Governor's Enhanced Voting portal; rcvis.com (RCV rounds)
- **Portal:** vote.utahcounty.gov / electionresults.utah.gov / rcvis.com
- **Documents indexed:** 22  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 14/22 (64%)  ·  **Host(s):** vote.utahcounty.gov, www.rcvis.com
- **How the text was obtained:** html (raw retained verbatim) (9), json (raw retained verbatim) (8), pdf (raw retained verbatim) (4), csv (raw retained verbatim) (1)
- **Note:** Raw county/state files mirrored verbatim in election_results/raw/; per-file URLs documented for the county portal only as hashed /cms/uploads/ names (see election_results/CLAUDE.md).

## Agenda packets / staff reports

- **Published by:** Lehi City Recorder
- **Portal:** Granicus (lehi.granicus.com)
- **Documents indexed:** 564  ·  **Date range:** 2024-01-04 to 2025-12-22
- **Direct source URLs recorded:** 564/564 (100%)  ·  **Host(s):** legistarweb-production.s3.amazonaws.com, lehi.granicus.com
- **How the text was obtained:** none (raw retained) (564)
- **Note:** Agendas and agenda packets, raw PDFs retained.

## Housing plans / general plan

- **Published by:** Lehi City (lehi-ut.gov); Utah DWS/HCD filings
- **Portal:** lehi-ut.gov
- **Documents indexed:** 9  ·  **Date range:** 2021 to 2025
- **Direct source URLs recorded:** 9/9 (100%)  ·  **Host(s):** jobs.utah.gov, www.lehi-ut.gov
- **How the text was obtained:** pdftotext-layout (7), none (2)
- **Note:** General plan + moderate-income housing element documents.

## Ordinances (adoption record)

- **Published by:** Lehi City Council (via adopted-motion record)
- **Portal:** Granicus (lehi.granicus.com) — reconstructed from minutes
- **Documents indexed:** 313  ·  **Date range:** 2020-01-28 to 2026-02-10
- **Direct source URLs recorded:** 313/313 (100%)  ·  **Host(s):** lehi.granicus.com, www.lehi-ut.gov
- **How the text was obtained:** reconstructed from meeting_minutes motion text (born-digital Granicus minutes) (via minutes document) (309), pdftotext -layout (born-digital city Notice of Ordinance Adoption PDF) (4)
- **Note:** Ordinance actions reconstructed from council minutes motions; source_url resolves to the minutes document that records adoption.

## Utah Public Notice backfill

- **Published by:** Utah Public Notice Website (Lt. Governor)
- **Portal:** utah.gov/pmn
- **Documents indexed:** 8  ·  **Date range:** 2020-02-04 to 2026-05-07
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (8)
- **Note:** State-mandated public-notice copies of agendas/minutes.

## Meeting-video transcripts

- **Published by:** Lehi City (YouTube channel); OpenUtah mirror
- **Portal:** lehi.openutah.org / YouTube
- **Documents indexed:** 12  ·  **Date range:** 2025-03-27 to 2026-05-28
- **Direct source URLs recorded:** 12/12 (100%)  ·  **Host(s):** lehi.openutah.org
- **How the text was obtained:** unrecovered_yt-dlp_absent (12)
- **Note:** No caption files were retrievable (yt-dlp absent at build time); index rows carry the source URLs only — no local documents.

## Campaign-finance disclosures

- **Published by:** Lehi City Recorder (candidate financial statements)
- **Portal:** lehi-ut.gov
- **Documents indexed:** 134  ·  **Date range:** 2019-08-01 to 2025
- **Direct source URLs recorded:** 134/134 (100%)  ·  **Host(s):** www.lehi-ut.gov
- **How the text was obtained:** pdftotext -layout (69), tesseract OCR (pdftoppm 300dpi) (64), tesseract OCR (image) (1)
- **Note:** Born-digital PDFs, raw retained.

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
