# Sources — Sandy civic data

Civic records of the Sandy City Council and Planning Commission, 2020–present. Council minutes are published on Granicus Legistar (sandyutah.legistar.com). Planning Commission votes come from the Legistar web API (structured EventItemVote records; Sandy publishes no separate PC minutes files in this pipeline). Sandy publishes no written public-comment compilations. Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py sandy`.

## Council meeting minutes

- **Published by:** Sandy City Recorder
- **Portal:** Granicus Legistar (sandyutah.legistar.com)
- **Documents indexed:** 277  ·  **Date range:** 2020-01-07 to 2026-06-23
- **Direct source URLs recorded:** 277/277 (100%)  ·  **Host(s):** sandyutah.legistar.com
- **How the text was obtained:** text (156), text_pua_decoded (63), ocr (58)
- **Note:** Born-digital PDFs (some with PUA-encoded fonts, decoded; some OCR).

## Planning Commission minutes

- **Published by:** Sandy Community Development
- **Portal:** Granicus Legistar web API (sandyutah.legistar.com)
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 0/1 (0%)
- **How the text was obtained:** legistar-api (1)
- **Note:** Votes built from Legistar EventItemVote API records staged in db/staging/ — not from minutes documents.

## Public comments

- **Published by:** —
- **Portal:** —
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Sandy publishes no written public comments (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 3  ·  **Date range:** 2021 to 2021
- **Direct source URLs recorded:** 3/3 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** pdf (raw retained verbatim) (2), filtered directly from the county canonical (build_sandy_elections.py) (1)
- **Note:** County SOVC workbooks + RCV reports copied verbatim from a local mirror of the county results site; per-file URLs were not recorded.

## Agenda packets / staff reports

- **Documents indexed:** 6908  ·  **Date range:** 2020-01-02 to 2026-07-07
- **Direct source URLs recorded:** 6908/6908 (100%)  ·  **Host(s):** content.civicplus.com, docs.google.com, extension.usu.edu, luau.utah.gov, privacy.utah.gov, sandy.utah.gov, sandyutah.granicusideas.com, sandyutah.legistar1.com, soundcloud.com, tinyurl.com, training.auditor.utah.gov, www.mwdsls.org, www.sandy.utah.gov, www.slc.gov, www.youtube.com, youtu.be
- **How the text was obtained:** legistar_matter_attachment (6350), legistar_event_agenda_file (462), claude_vision (96)

## Housing plans / general plan

- **Documents indexed:** 36  ·  **Date range:** 1979-08 to 2025-09-10
- **Direct source URLs recorded:** 36/36 (100%)  ·  **Host(s):** content.civicplus.com, jobs.utah.gov, sandycity.maps.arcgis.com, sandyutah.legistar1.com, www.sandy.utah.gov
- **How the text was obtained:** pdftotext-layout (28), arcgis-rest-api (4), pdftotext-layout+cmap-shift-decode (3), none (1)

## Ordinances (adoption record)

- **Documents indexed:** 170  ·  **Date range:** 2020-02-04 to 2026-06-23
- **Direct source URLs recorded:** 170/170 (100%)  ·  **Host(s):** sandyutah.legistar.com, sandyutah.legistar1.com
- **How the text was obtained:** legistar web api (matters/histories/attachments) — MatterTypeId 53 (170)

## Utah Public Notice backfill

- **Documents indexed:** 8  ·  **Date range:** 2022-05-17 to 2026-06-23
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** tesseract OCR (pdftoppm 300dpi) (6), pdftotext -layout (2)

## Meeting-video transcripts

- **Documents indexed:** 88  ·  **Date range:** 2022-10-25 to 2026-06-23
- **Direct source URLs recorded:** 88/88 (100%)  ·  **Host(s):** sandy.openutah.org, www.youtube.com
- **How the text was obtained:** yt-dlp --write-auto-sub (YouTube timedtext) (87), yt-dlp --list-subs (no caption track published) (1)

## Campaign-finance disclosures

- **Documents indexed:** 83  ·  **Date range:** 2021-10-10 to 2026-01-15
- **Direct source URLs recorded:** 83/83 (100%)  ·  **Host(s):** sandycityut.easyvotecampaignfinance.com
- **How the text was obtained:** ocr_tesseract (83)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
