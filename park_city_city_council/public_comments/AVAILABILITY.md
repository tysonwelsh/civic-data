# Public-comment availability — Park City, Utah (City Council)

**Audited:** 2026-06-26 · **Scope:** 2020–present · **Verdict: PUBLISHED**
(genuine public-submitted **written/online** comments are public, in two places, and have
been extracted to `all_comments_clean.csv`).

Park City Municipal Corporation (Summit County). Portal vendor **CivicClerk (CivicPlus)**;
open OData API at `https://parkcityut.api.civicclerk.com/v1/` (no auth). Council is
**at-large** (no districts → `district` column blank). Submit channels advertised:
email `council_mail@parkcity.gov`, the **eComment** electronic-comment feature tied to each
meeting, the `public_comments@parkcity.org` form (CivicPlus), and Zoom "raise hand."

## What we found, avenue by avenue

### 1. Dedicated published-comments page — NONE
No standalone "public comment" / "correspondence" archive page on `parkcity.gov`. The CMS
"pretty" nav pages 404 to scrapers; checked the council pages
(`parkcity.gov/government/city-council/city-council-meetings`). No SLC-style weekly
public-comment PDF archive exists.

### 2. Inside the minutes — **YES (primary source, genuine written comments)**
The born-digital council **minutes quote written eComment/email submissions VERBATIM**, in
quotation marks, e.g. `Timothy McBride eComment: "Wildlife are part of our community…"`.
These are the **public's own submitted words, published by the city** — they qualify as
genuine written comments (NOT clerk paraphrases). Found across **94 of 238** minutes files,
2020–2026 (≈420 eComment markers).
- Source: CivicClerk `Minutes` files (already mirrored in `meeting_minutes/minutes/…`).
- API doc fetch: `GET /v1/Meetings/GetMeetingFileStream(fileId=<id>,plainText=true)`.
- → **420 eComment + 13 emailed** verbatim comments extracted to `all_comments_clean.csv`.

The same minutes ALSO paraphrase **in-person speakers** in the third person
("Kris Campbell, 84098, LGBTQ Taskforce, thanked Council…"). Per the strict standard these
are **meeting-record notes, NOT public-submitted comments** → they are kept OUT of
`all_comments_clean.csv` and logged separately in **`minutes_speaker_log.csv`** (1,055 rows).

### 3. Agenda packets — **YES (secondary source, genuine written comments)**
CivicClerk `Agenda Packet` PDFs sometimes bundle a **"correspondence received"** exhibit of
**forwarded resident emails** to `planning@` / `Council_Mail@` / `public_comments@parkcity.org`
(Outlook `From:/Sent:/Subject:[External]` blocks) and CivicPlus "Public Comment Submission"
form relays. **All 239** council packets (2020–present) were fetched **as plaintext via the
API** (`GetMeetingFileStream(fileId=…,plainText=true)` — **no PDF ever stored; disk-safe**) and
parsed. Forwarded resident correspondence was concentrated in a handful of packets (richest:
the **2023-12-14** Deer Valley ROW-vacation packet, ~19 letters; also 2023-06-06, 2022-02-16,
2021-04, and scattered 2025 packets).
- → **26 packet-correspondence comments** extracted and merged into `all_comments_clean.csv`,
  deduped against the minutes eComments; the `source` column tags them and
  `quality_flag=from_agenda_packet`. Email bodies are followed by their attachments in the
  packet, so over-long bodies are cut at the attachment boundary (`truncated_at_attachment`).

### 4. eComment / Open-City-Hall / Speak-Up portal — submit-only, no public archive
CivicClerk's eComment feature accepts comments per meeting, but the portal exposes **no
public, exportable archive of raw submissions**. In practice the submissions surface
**inside the minutes** (verbatim, §2) and **inside agenda packets** (§3), which is what we
harvested. No Wayback-only / decommissioned-portal recovery was needed.

### 5. Records / transparency / open-data — n/a
No council-correspondence open-data feed beyond the packets/minutes above. Utah PMN body 654
exists for the Park City RDA but is a noticing body, not a comment archive. (GRAMA records
requests exist but are not a published comment archive.)

### 6. Email/phone-only submission — published, not hidden
Comments emailed to `council_mail@parkcity.gov` are, in practice, **published** — quoted
verbatim in the minutes and/or bundled as packet correspondence. This is therefore **not** a
"submit-only / not published" city.

## Verdict

**PUBLISHED.** Genuine public-submitted written/online comments are public via (a) **verbatim
eComment/email quotes in the council minutes** (primary; parsed across all 238 meetings) and
(b) **forwarded resident correspondence bundled in agenda-packet PDFs** (secondary;
intermittent). Both were extracted to `all_comments_clean.csv` — **459** comments, 2020–2026,
~400 unique commenters (433 from minutes, 26 from packets; 3 cross-source duplicates dropped
to `all_comments_dropped.csv`). In-person speaker paraphrases are **separately** logged in
`minutes_speaker_log.csv` (1,055 rows) and are deliberately excluded from the comments dataset.

```json
{"verdict":"published","locations":["verbatim eComment/email quotes inside CivicClerk council minutes (parkcityut.api.civicclerk.com/v1, categoryId 26, Minutes files; mirrored in meeting_minutes/minutes/)","forwarded resident correspondence inside CivicClerk Agenda Packet PDFs (fetched plaintext, disk-safe)"],"notes":"459 genuine written comments (420 eComment + 13 email quoted verbatim in minutes; 26 forwarded letters/form submissions harvested from agenda packets, deduped). 1,055 in-person Public-Input speakers logged separately in minutes_speaker_log.csv (NOT counted as comments). No standalone public-comment web page; no portal export. Council is at-large (no districts)."}
```
