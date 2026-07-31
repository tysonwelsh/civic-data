# Sources — South Salt Lake civic data

Civic records of the South Salt Lake City Council (with a separate Redevelopment Agency) and Planning Commission, plus municipal election results back to 2007. Minutes come from Utah Public Notice (council body 1295, RDA 1296, PC 1297). South Salt Lake is a strong-mayor city: a 7-member council (5 districts + 2 at-large) legislates and the executive Mayor does NOT vote (max council roll = 7). South Salt Lake publishes no written public-comment archive (submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py south_salt_lake`.

## Council meeting minutes

- **Published by:** South Salt Lake City Recorder
- **Portal:** Utah Public Notice (utah.gov/pmn; council body 1295, RDA body 1296)
- **Documents indexed:** 139  ·  **Date range:** 2020-05-27 to 2026-07-08
- **Direct source URLs recorded:** 139/139 (100%)  ·  **Host(s):** sslc.gov, www.utah.gov
- **How the text was obtained:** pdf-text (139)
- **Note:** ⚠ COVERAGE: the PMN 'Meeting Minutes' slot usually serves the AGENDA PACKET (no roll call), even for files labelled '...RC Minutes.pdf' - real recorded minutes were content-detected by roll-call grammar. The city posts RECORDED council minutes essentially only for 2020-early-2021 plus sporadic recent meetings; 2021-mid through 2025 it published agenda packets only (253 agenda-only gaps logged in minutes_unrecovered.csv - an HONEST publication gap, not a scraper miss). The council also convenes as a separate RDA (body=RDA). Mayor is non-voting (max roll 7). SSL prints no result string, so `result` is a synthesized <aye>-<nay> tally.

## Planning Commission minutes

- **Published by:** South Salt Lake Planning Division
- **Portal:** Utah Public Notice (utah.gov/pmn; body 1297)
- **Documents indexed:** 61  ·  **Date range:** 2022-01-20 to 2026-06-18
- **Direct source URLs recorded:** 61/61 (100%)  ·  **Host(s):** sslc.gov, www.utah.gov
- **How the text was obtained:** pdf-text (61)
- **Note:** South Salt Lake runs its own Planning Commission (up to 8 commissioners). Recorded PC minutes begin 2023-01-19 (2020-2022 were never published as minutes - agendas only).

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** South Salt Lake publishes no written public comments - in-person + Zoom + connect@sslc.gov; submit-only, not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 6  ·  **Date range:** 2011 to 2021
- **Direct source URLs recorded:** 6/6 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (5), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2011 & 2019 recovered from raw SOVC, 2021 re-parsed for privacy suppression. 5 districts + 2 At-Large + Mayor; a 2025 off-cycle At-Large 2-year special (deWolfe).

## Agenda packets / staff reports

- **Documents indexed:** 429  ·  **Date range:** 2020-01-08 to 2026-07-16
- **Direct source URLs recorded:** 429/429 (100%)  ·  **Host(s):** sslc.gov
- **How the text was obtained:** not_retrieved (index-only; fetch source_url on demand) (357), pdftotext -layout (72)

## Housing plans / general plan

- **Documents indexed:** 8  ·  **Date range:** 2016-08-11 to 2025
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** jobs.utah.gov, sslc.gov
- **How the text was obtained:** pdftotext -layout (8)

## Ordinances (adoption record)

- **Documents indexed:** 114  ·  **Date range:** 2020-01-08 to 2026-06-17
- **Direct source URLs recorded:** 114/114 (100%)  ·  **Host(s):** library.municode.com
- **How the text was obtained:** parsed Municode COCOTADILI comparative table (api.municode.com, born-digital) (100), derived from meeting_minutes/all_votes.csv motion text (14)

## Utah Public Notice backfill

- **Documents indexed:** 130  ·  **Date range:** 2022-01-20 to 2026-06-17
- **Direct source URLs recorded:** 130/130 (100%)  ·  **Host(s):** sslc.gov
- **How the text was obtained:** pdftotext -layout (130)

## Meeting-video transcripts

- **Documents indexed:** 269  ·  **Date range:** 2022-12-05 to 2026-07-09
- **Direct source URLs recorded:** 269/269 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp --list-subs (android client): en ASR track available, not fetched (sample-only) (259), yt-dlp --write-auto-sub (android client, en) -> clean_captions_ssl.py (10)

## Campaign-finance disclosures

- **Documents indexed:** 68  ·  **Date range:** 2021-11-30 to 2026-01-31
- **Direct source URLs recorded:** 68/68 (100%)  ·  **Host(s):** municipal.utah.gov, sslc.gov
- **How the text was obtained:** none (acquisition-only; scanned image PDF, OCR/vision deferred) (54), none (acquisition-only; born-digital text PDF) (14)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
