# Sources — Salt Lake City civic data

Civic records of the Salt Lake City Council and Planning Commission, 2020–present, plus municipal election results back to 2007. Council minutes are published by the City Recorder / Council Office on the PrimeGov portal (slc.primegov.com; born-digital, 2021+) with the older material on the city's Laserfiche WebLink archive (webdme.slcgov.com/AgendasMinutes; scanned + OCR). Planning Commission minutes are published by the Planning Division on slcdocs.com and Laserfiche. Written public comments are published as weekly PDF compilations on slcdocs.com. Election results are produced by the Salt Lake County Clerk.

The machine-readable companion to this page is [`sources.csv`](sources.csv) — one row per source document with its original URL (where recorded), local path, and extraction method. Generated 2026-07-20 by `scripts/build_sources_index.py`; regenerate with `python3 scripts/build_sources_index.py slc`.

## Council meeting minutes

- **Published by:** Salt Lake City Recorder / City Council Office
- **Portal:** PrimeGov (slc.primegov.com); archival: Laserfiche WebLink (webdme.slcgov.com)
- **Documents indexed:** 477  ·  **Date range:** 2020-01-07 to 2026-06-16
- **Direct source URLs recorded:** 474/477 (99%)  ·  **Host(s):** slc.primegov.com, www.utah.gov
- **How the text was obtained:** text (409), ocr (68)
- **Note:** 2021+ born-digital HTML minutes converted to text; 2020 files are OCR of Laserfiche scans (65 of 68 carry equivalent-record PMN citation URLs since 2026-07-19; 3 formal-session dates are verified no-PMN gaps).

## Planning Commission minutes

- **Published by:** Salt Lake City Planning Division
- **Portal:** slcdocs.com / Laserfiche WebLink / slc.gov
- **Documents indexed:** 146  ·  **Date range:** 2020-01-08 to 2026-06-24
- **Direct source URLs recorded:** 146/146 (100%)  ·  **Host(s):** webdme.slcgov.com, www.slc.gov, www.slcdocs.com
- **How the text was obtained:** text (146)
- **Note:** Born-digital PDFs on slcdocs.com; older items from Laserfiche.

## Public comments

- **Published by:** Salt Lake City Council Office
- **Portal:** slcdocs.com (weekly public-comment PDF compilations)
- **Documents indexed:** 217  ·  **Date range:** 2020-03-24 to 2026-04-07
- **Direct source URLs recorded:** 217/217 (100%)  ·  **Host(s):** www.slcdocs.com
- **How the text was obtained:** claude-vision (vision_extract.py) (217)
- **Note:** Extracted from the weekly PDFs with Claude Vision; ~8 unrecoverable pages documented in public_comments/CLAUDE.md.

## Municipal election results

- **Published by:** Salt Lake County Clerk (Elections Division)
- **Portal:** saltlakecounty.gov/clerk/elections/election-results
- **Documents indexed:** 1  ·  **Date range:** n/a
- **Direct source URLs recorded:** 1/1 (100%)  ·  **Host(s):** www.saltlakecounty.gov
- **How the text was obtained:** filtered directly from the county canonical (clean_elections.py) (1)
- **Note:** County-wide canvass exports (2007–2025) filtered to Salt Lake City races; per-file download URLs were not recorded at capture time.

## Agenda packets / staff reports

- **Documents indexed:** 582  ·  **Date range:** 2020-01-06 to 2026-07-08
- **Direct source URLs recorded:** 582/582 (100%)  ·  **Host(s):** slc.primegov.com, www.slc.gov, www.slcdocs.com
- **How the text was obtained:** not_retrieved (543), pdftotext (39)

## Housing plans / general plan

- **Documents indexed:** 11  ·  **Date range:** 2015-12-01 to 2025
- **Direct source URLs recorded:** 11/11 (100%)  ·  **Host(s):** jobs.utah.gov, www.slc.gov, www.slcdocs.com
- **How the text was obtained:** pdftotext-layout (6), pymupdf-pagerange (4), tesseract-ocr (1)

## Ordinances (adoption record)

- **Documents indexed:** 464  ·  **Date range:** 2020-01-17 to 2026-06-16
- **Direct source URLs recorded:** 464/464 (100%)  ·  **Host(s):** slc.primegov.com
- **How the text was obtained:** reconstructed from meeting_minutes council motion text (PrimeGov minutes) (410), ordinance number found in minutes text only (no matched vote row) (54)

## Utah Public Notice backfill

- **Documents indexed:** 7  ·  **Date range:** 2020-06-09 to 2026-01-05
- **Direct source URLs recorded:** 7/7 (100%)  ·  **Host(s):** www.utah.gov
- **How the text was obtained:** pdftotext -layout (7)

## Meeting-video transcripts

- **Documents indexed:** 10  ·  **Date range:** 2026-05-05 to 2026-06-09
- **Direct source URLs recorded:** 10/10 (100%)  ·  **Host(s):** www.youtube.com
- **How the text was obtained:** yt-dlp_auto_sub_en (10)

---

*Where a row's `source_url` reads `unrecorded (…)`, the original download URL was not captured at retrieval time; the parenthetical names the issuing office/portal so the document can be re-obtained from the publisher. `verified_date` is stamped only on rows whose URL was re-checked live on that date (sampled, not exhaustive). No URL in this index is reconstructed or guessed.*
