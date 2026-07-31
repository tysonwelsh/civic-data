# Sources — South Jordan civic data

Civic records of the South Jordan City Council (with in-session RDA/MBA sessions) and Planning Commission, 2020-present, plus municipal election results back to 2007. Council and Planning Commission minutes are published by the City Recorder on the city's CivicPlus/CivicEngage site (sjc.utah.gov DocumentCenter/ArchiveCenter), with 2020 backfilled from the Municode Meetings portal and the Utah Public Notice Website. South Jordan publishes no written public-comment compilations (comment is submit-only, by email or in person). Election results are produced by the Salt Lake County Clerk. Expansion datasets (agenda packets, housing/general plan, ordinances, public-notice backfill, transcripts, campaign finance) carry their own per-document provenance.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py south_jordan`.

## Council meeting minutes

- **Published by:** South Jordan City Recorder
- **Portal:** CivicPlus/CivicEngage (sjc.utah.gov); 2020 backfill: Municode Meetings + Utah Public Notice (utah.gov/pmn)
- **Documents indexed:** 243  ·  **Date range:** 2020-08-18 to 2026-05-19
- **Direct source URLs recorded:** 243/243 (100%)  ·  **Host(s):** www.sjc.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (243)
- **Note:** Born-digital text PDFs harvested from the DocumentCenter/ArchiveCenter year archives; the council sits in-session as the RDA and MBA (no separate RDA/MBA minutes files).

## Planning Commission minutes

- **Published by:** South Jordan City Planning Division
- **Portal:** CivicPlus/CivicEngage (sjc.utah.gov); Utah Public Notice (utah.gov/pmn)
- **Documents indexed:** 127  ·  **Date range:** 2020-01-14 to 2026-05-26
- **Direct source URLs recorded:** 127/127 (100%)  ·  **Host(s):** www.sjc.utah.gov, www.utah.gov
- **How the text was obtained:** pdf-text (127)
- **Note:** Born-digital text PDFs from the Planning Commission minutes archive; 2020 supplemented from Utah PMN.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** South Jordan publishes no written public comments - comment is submit-only (email to the City Recorder or in person), neither archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 17  ·  **Date range:** 2007 to 2025
- **Direct source URLs recorded:** 17/17 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (13), xls (raw retained verbatim) (3), filtered directly from the county canonical (clean_elections.py) (1)
- **Note:** County SOVC workbooks copied verbatim from the local slco-election-archive mirror of the county results site; per-file URLs were not recorded.

## Agenda packets / staff reports

- **Published by:** South Jordan City Recorder
- **Portal:** CivicPlus/CivicEngage (sjc.utah.gov); Municode Meetings
- **Documents indexed:** 169  ·  **Date range:** 2022-01-04 to 2026-06-16
- **Direct source URLs recorded:** 169/169 (100%)  ·  **Host(s):** mccmeetings.blob.core.usgovcloudapi.net
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand — pdftotext for staff-report text, vision/OCR for map/plat exhibits) (169)
- **Note:** Agendas and agenda packets, raw retained.

## Housing plans / general plan

- **Published by:** South Jordan City (sjc.utah.gov); Utah DWS/HCD filings
- **Portal:** sjc.utah.gov
- **Documents indexed:** 6  ·  **Date range:** 2020 to 2025
- **Direct source URLs recorded:** 6/6 (100%)  ·  **Host(s):** jobs.utah.gov, www.sjc.utah.gov
- **How the text was obtained:** pdftotext-layout (6)
- **Note:** General plan + moderate-income housing element documents.

## Ordinances (adoption record)

- **Published by:** South Jordan City Council (via adopted-motion record)
- **Portal:** CivicPlus/CivicEngage (sjc.utah.gov) - reconstructed from minutes
- **Documents indexed:** 130  ·  **Date range:** 2020-01-07 to 2026-05-19
- **Direct source URLs recorded:** 129/130 (99%)  ·  **Host(s):** s3-us-west-2.amazonaws.com, www.sjc.utah.gov, www.utah.gov
- **How the text was obtained:** motion-citation (derived from minutes; not independently corroborated) (79), scanned image PDF (OCR/vision on signature page for date; body OCR deferred) (46), pdftotext-layout (5)
- **Note:** Ordinance actions reconstructed from council minutes motions; source_url resolves to the minutes document that records adoption.

## Utah Public Notice backfill

- **Published by:** Utah Public Notice Website (Lt. Governor)
- **Portal:** utah.gov/pmn
- **Documents indexed:** 13  ·  **Date range:** 2020-01-07 to 2023-01-24
- **Direct source URLs recorded:** 13/13 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext-layout (13)
- **Note:** State-mandated public-notice copies of agendas/minutes.

## Meeting-video transcripts

- **Published by:** South Jordan City (meeting video)
- **Portal:** sjc.utah.gov / YouTube
- **Documents indexed:** 125  ·  **Date range:** 2013-09-23 to 2026-05-22
- **Direct source URLs recorded:** 125/125 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** index-only (caption track exists, not retrieved — sample-only policy) (74), index-only (no caption track published) (41), yt-dlp --write-auto-sub (ASR); vtt cleaned to text/ (10)
- **Note:** Meeting-video transcripts; per-row source URLs carried where recorded.

## Campaign-finance disclosures

- **Published by:** South Jordan City Recorder (candidate financial statements)
- **Portal:** sjc.utah.gov
- **Documents indexed:** 46  ·  **Date range:** 2019-12-01 to 2025-12-01
- **Direct source URLs recorded:** 46/46 (100%)  ·  **Host(s):** www.sjc.utah.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (46)
- **Note:** Candidate financial disclosures, raw retained.

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
