# Public-comment QC — source documents for spot-checking extraction accuracy

Purpose: verify the `public_comments/all_comments_clean.csv` rows against the ORIGINAL
source PDFs, the way SLC's image-PDF problem was caught. Compare each CSV row's `comment`
text + `contact_name` against the source doc; check for (a) garbling, (b) DROPPED comments.

## Where the source documents live (by city)

| City | Source docs on disk | Maps to CSV via |
|---|---|---|
| **St. George** | `st_george_city_council/public_comments/raw/<year>/*.pdf` (53 PDFs, RETAINED) | `source_file` column (+ `page_numbers`); manifest: `public_comments/comments_json/_manifest.json` |
| **Provo** | `provo_city_council/public_comments/raw/packets/*.pdf` (26 packet PDFs, RETAINED) | `public_comments/packets_scanned.csv` (date→packet_url→n_comments); CSV `source_file` = packet_txt name |
| **West Jordan** | `_comment_qc/west_jordan/packet_tid{99,308}.pdf` (RE-FETCHED here; originals were deleted) | CSV `source_file` = `2022-08-10_packet_tid99.pdf` / `2022-09-14_packet_tid308.pdf` |
| **Park City** | comments quoted verbatim IN the minutes markdown: `park_city_city_council/meeting_minutes/minutes/...md` (on disk) | CSV `source_file` points to the exact .md (433 of 459); 26 are CivicClerk packets (re-fetchable on request) |
| **Lehi** | comments quoted in 2020 minutes markdown (on disk) | CSV `source_file` = the minutes .md |

## How to QC a city
1. Open a source PDF (or .md) above.
2. Filter `all_comments_clean.csv` to rows whose `source_file` matches it.
3. Check: every comment in the PDF is a row (no DROPS); each row's text matches the PDF (no garbling);
   `contact_name`/`date` correct. Note: `quality_flag` already flags known edge cases
   (truncated_at_attachment, name_inferred, name_unreliable, date_from_filename).

## Why this matters
SLC's comment PDFs were scanned IMAGES (bad/again text layer) → needed the vision API. The cities
above use BORN-DIGITAL text PDFs (or minutes text), so `pdftotext` produced clean output — but
completeness (no dropped comments) is best confirmed against these originals.
