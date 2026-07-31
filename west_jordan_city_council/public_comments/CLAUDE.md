# public_comments/ — West Jordan City

## What this is
Genuine **public-submitted written comments** for the West Jordan City Council, harvested
from the city's PrimeGov agenda packets. West Jordan does not run a standalone public-comment
portal or a published-comments page; instead, residents email
`councilcomments@westjordan.utah.gov` (or a staff member), and the clerk **forwards those
emails into the meeting's Complete Packet PDF** as "correspondence / written comments
received." Those forwarded emails are the genuine written-comment record, and they are what
lives in `all_comments_clean.csv`.

Verdict: **IN-PACKETS** (see `AVAILABILITY.md`).

## Files
- `all_comments_clean.csv` — genuine resident written comments (SLC schema). One row per
  forwarded resident email. `source=agenda_packet`; `date`/`date_normalized` = the meeting
  date the packet belongs to (100% populated); `contact_name` = the email sender;
  `subject` = the email subject line.
- `all_comments_dropped.csv` — every removed candidate row with a `_drop_reason`
  (staff/vendor/applicant/internal-routing senders, automated-system mail, internal-domain
  `@westjordan.utah.gov`, empty/too-short, no resident signal, within-packet duplicate, and
  cross-packet `recurrent_correspondence_dup` — the same email re-bundled into a later
  meeting's packet). Nothing is silently deleted.
- `packets_scanned.csv` — audit log: one row per packet URL scanned
  (`date,url,meetingTemplateId,had_comments,n_comments,n_dropped,status`).
- `minutes_speaker_log.csv` — **MEETING-RECORD NOTES, NOT public-submitted comments.**
  Clerk paraphrases of in-person public-comment speakers extracted from the minutes `.md`
  files. Provided for context only; do NOT present these as the comments dataset and do NOT
  merge them into `all_comments_clean.csv`.
- `raw/` — packet PDFs are kept here **only** when the packet contained >=1 genuine resident
  comment (disk discipline: every other packet was downloaded, scanned, and deleted).
- `packet_text/` — reserved (empty); packet text is processed in a temp dir and discarded.

## How it was built (resumable)
For each of the 120 packet URLs in `meeting_minutes/minutes_index.csv` (`packet_url`
column, 2022-2025): download to a temp path -> `pdftotext -layout` -> parse email-artifact
blocks (`From:/Sent:/To:/Subject:` headers + the "CAUTION: This email originated from
outside the organization" banner + `Name:/Address:` self-ID) -> classify sender
(resident vs staff/vendor/automated) -> delete the PDF. Disk checked every ~15 packets.
After harvest, a finalize pass applied cross-packet content dedup (keep earliest meeting
date), dropped agenda boilerplate, and remapped to the canonical SLC schema.

## Caveats
- `pdftotext` injects spurious spaces into the WJ packets (e.g. `gmail.   com`,
  `1: 04 AM`); email addresses were de-spaced, comment bodies were left readable.
- The West Jordan Welby West / Bowman's Arrow rezone generated a large correspondence
  bundle that the clerk re-attached to several consecutive 2022-2023 packets. Cross-packet
  dedup keeps the earliest copy; later copies are in `*_dropped.csv` as
  `recurrent_correspondence_dup`.
- 2020-2021 (and 2026) meetings have no `packet_url` in the index, so no written comments
  were harvestable for those years from this source.
- Do NOT run `build_weeks.py` on this data without re-checking; this agent did not.
