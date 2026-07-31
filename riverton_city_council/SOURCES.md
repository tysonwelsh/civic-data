# Sources — Riverton civic data

Civic records of the Riverton City Council and Planning Commission, 2020-present, plus municipal election results back to 2007. Minutes are published on the city's Granicus portal and mirrored on Utah Public Notice (the machine-readable spine used here). Riverton is governed by 5 district councilmembers + a separately-elected Mayor who is NON-voting except to break ties (the Park City model). Riverton publishes no written public-comment compilations (comment is in-person/eComment, submit-only). Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-19 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py riverton`.

## Council meeting minutes

- **Published by:** Riverton City Recorder
- **Portal:** Utah Public Notice (utah.gov/pmn; council + PC body 5473) mirroring the city's Granicus archive (rivertoncity.granicus.com)
- **Documents indexed:** 128  ·  **Date range:** 2020-02-18 to 2026-06-02
- **Direct source URLs recorded:** 128/128 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** text (128)
- **Note:** Born-digital text PDFs. Named roll-call votes. The Mayor is non-voting on ordinary motions (max council roll = 5) EXCEPT tie-breaks, captured as the 'Aye (Mayor tie-break)' vocabulary extension (1 row, 2025-12-16, Mayor Staggs). The city's Revize CMS lists dates only; acquisition is via PMN/Granicus.

## Planning Commission minutes

- **Published by:** Riverton City Planning Division
- **Portal:** Utah Public Notice (utah.gov/pmn; body 5473) / Granicus
- **Documents indexed:** 119  ·  **Date range:** 2020-01-23 to 2026-06-11
- **Direct source URLs recorded:** 119/119 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** text (119)
- **Note:** Riverton runs its own Planning Commission (2nd & 4th Thursday); prints a full named roll call on DIVIDED votes and 'unanimous consent' (unnamed placeholder) on unanimous ones - the honest tally-only convention.

## Public comments

- **Published by:** -
- **Portal:** -
- **Documents indexed:** none — this city publishes no documents of this type (an honest gap, not missing data).
- **Note:** Riverton publishes no written public comments - comment is in-person (paraphrased inline in minutes) / Granicus eComment, submit-only and not archived (see public_comments/AVAILABILITY.md).

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 4  ·  **Date range:** 2019 to 2021
- **Direct source URLs recorded:** 4/4 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** xlsx (raw retained verbatim) (3), csv (raw retained verbatim) (1)
- **Note:** Filtered from the canonical Salt Lake County results; 2019 general + 2021 general recovered from raw SOVC (2021 was method-split privacy-suppressed in the long file). NOTE the D3<->D4 renumber by 2022 Ord 22-07 - person<->district joins across 2022 must not assume stable numbers (see election_results/CLAUDE.md).

## Agenda packets / staff reports

- **Documents indexed:** 3015  ·  **Date range:** 2020-01-07 to 2026-07-09
- **Direct source URLs recorded:** 3015/3015 (100%)  ·  **Host(s):** d3n9y02raazwpg.cloudfront.net, legistarweb-production.s3.amazonaws.com, rivertoncity.granicus.com
- **How the text was obtained:** pdftotext -layout (2490), none (oversize >4MB; not stored) (301), none (image-only pdf; OCR/vision if needed) (108), none (403 AccessDenied; legistarweb restricted this 2020 object) (83), none (not stored; index-only) (18), none (extraction error; OCR/vision if needed) (8), none (Granicus auth-wall HTML capture; login-gated PDF - see AVAILABILITY.md) (5), html tag-strip (2)

## Housing plans / general plan

- **Documents indexed:** 8  ·  **Date range:** 2020-08-18 to 2025
- **Direct source URLs recorded:** 8/8 (100%)  ·  **Host(s):** jobs.utah.gov, www.rivertonutah.gov
- **How the text was obtained:** pdftotext -layout (8)

## Ordinances (adoption record)

- **Documents indexed:** 155  ·  **Date range:** 2020-03-17 to 2026-06-02
- **Direct source URLs recorded:** 155/155 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** reconstructed from meeting_minutes motion text (no independent adoption PDF) (93), pdftotext -layout (born-digital PMN Notice-of-Adoption signed ordinance PDF) (62)

## Utah Public Notice backfill

- **Documents indexed:** 7  ·  **Date range:** 2020-01-07 to 2026-06-25
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** rivertoncity.granicus.com, www.utah.gov
- **How the text was obtained:** pdftotext-layout (4), textutil-docx (2), textutil-doc (1)

## Meeting-video transcripts

- **Documents indexed:** 1  ·  **Date range:** 2018-05-01 to 2018-05-01
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp --write-auto-sub (YouTube timedtext ASR); cleaned by clean_vtt.py (1)

## Campaign-finance disclosures

- **Documents indexed:** 60  ·  **Date range:** 2021-11-02 to 2025-12-05
- **Direct source URLs recorded:** 60/60 (100%)  ·  **Host(s):** municipal.utah.gov, www.rivertonutah.gov
- **How the text was obtained:** none (raw acquisition; OCR/vision deferred) (60)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
