# Sources — Draper civic data

Civic records of the Draper City Council and Planning Commission, 2020-present, plus municipal election results back to 2007. Minutes are published on the city's Granicus portal (draper.granicus.com); Draper is governed by 5 AT-LARGE councilmembers + a separately-elected, NON-voting Mayor. Draper straddles Salt Lake (primary) and Utah counties, but Salt Lake County administers the entire city election. Draper publishes no written public-comment compilations (comment is in-person/email, submit-only).

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py draper`.

## Council meeting minutes

- **Published by:** Draper City Recorder
- **Portal:** Granicus (draper.granicus.com, ViewPublisher view_id=1)
- **Documents indexed:** 155  ·  **Date range:** 2020-01-14 to 2026-06-09
- **Direct source URLs recorded:** 155/155 (100%)  ·  **Host(s):** draper.granicus.com, www.utah.gov
- **How the text was obtained:** text (155)
- **Note:** Born-digital text PDFs via the Granicus MinutesViewer. Recent meetings publish BOTH a tally-only 'Recap' and the full 'Minutes' behind a JS document selector; the build resolves to the full Minutes and drops every Recap. Mayor is non-voting except one 2024-10-15 tie-break (recorded as a plain Aye). 3 broken Granicus docs (299-byte stubs) logged in minutes_unrecovered.csv.

## Planning Commission minutes

- **Published by:** Draper City Planning Division
- **Portal:** Granicus (draper.granicus.com, ViewPublisher view_id=1)
- **Documents indexed:** 143  ·  **Date range:** 2020-01-09 to 2026-05-28
- **Direct source URLs recorded:** 143/143 (100%)  ·  **Host(s):** draper.granicus.com, www.utah.gov
- **How the text was obtained:** text (143)
- **Note:** Draper runs its own Planning Commission (Thursday); named Yes/No/Abstained/Not-Participating/Absent grid; land-use motions cite case numbers YYYY-NNNN-<TYPE>.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Draper publishes no written public comments - comment is in-person / email (public.comment@draper.ut.us), submit-only and not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 5  ·  **Date range:** 2019 to 2025
- **Direct source URLs recorded:** 5/5 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (4), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2019 general + 2021 general recovered from raw SOVC. NOTE: the canonical long file undercounts 2025 Draper (dropped Utah-vintage 25DR0N precinct labels) - Draper's races here are re-parsed from raw SOVC and reconcile to the certified totals (see TODO.md).

## Agenda packets / staff reports

- **Documents indexed:** 4721  ·  **Date range:** 2020-01-09 to 2026-07-09
- **Direct source URLs recorded:** 4721/4721 (100%)  ·  **Host(s):** d2kbkoa27fdvtw.cloudfront.net, d3n9y02raazwpg.cloudfront.net, draper.granicus.com, draper.novusagenda.com, legistarweb-production.s3.amazonaws.com
- **How the text was obtained:** pdftotext -layout (2939), html tag-strip (894), none (image-only pdf; OCR/vision if needed) (322), none (html below text threshold) (288), none (not stored) (271), claude_vision (4), scanned (3)

## Housing plans / general plan

- **Documents indexed:** 12  ·  **Date range:** 2019-11-19 to 2025
- **Direct source URLs recorded:** 12/12 (100%)  ·  **Host(s):** jobs.utah.gov, www.draperutah.gov
- **How the text was obtained:** pdftotext -layout (12)

## Ordinances (adoption record)

- **Documents indexed:** 276  ·  **Date range:** 2018-08-07 to 2026-07-07
- **Direct source URLs recorded:** 207/276 (75%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (182), na (69), html-strip (18), tesseract 5 OCR @300dpi (7)

## Utah Public Notice backfill

- **Documents indexed:** 7  ·  **Date range:** 2020-12-10 to 2025-08-13
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (7)

## Meeting-video transcripts

- **Documents indexed:** 25  ·  **Date range:** 2026-01-06 to 2026-04-15
- **Direct source URLs recorded:** 25/25 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** not_retrieved_sample_policy (13), yt-dlp --write-auto-sub (YouTube timedtext ASR); cleaned by clean_vtt.py (10), no_caption_track_on_source (2)

## Campaign-finance disclosures

- **Documents indexed:** 125  ·  **Date range:** 2011-11-08 to 2025-12-04
- **Direct source URLs recorded:** 125/125 (100%)  ·  **Host(s):** drapercityut.contentmanager.tylerapp.com, www.draperutah.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (116), none (raw acquisition; born-digital, pdftotext-ready) (9)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
