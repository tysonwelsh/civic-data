# Public comments — availability (West Jordan City)

**Verdict: IN-PACKETS.** West Jordan does not publish genuine resident written comments on a
standalone page or comment portal. Instead, residents email comments to the council (to
`councilcomments@westjordan.utah.gov` or directly to a clerk/staff member), and the clerk
**forwards those emails into the meeting's PrimeGov "Complete Packet" PDF** under a
"correspondence / written comments received" section. Those forwarded emails are the genuine
written public-comment record, and they are what was harvested into
`all_comments_clean.csv`.

## Avenues checked (per extraction_standards.md hunt order)
1. **Dedicated published-comments page / archive** — none found. West Jordan's site has no
   SLC-style weekly comment PDFs and no St. George-style `public_comments.php`.
2. **eComment / Open City Hall / Speak-Up portal** — the PrimeGov public portal
   (`westjordan.primegov.com`) exposes meetings, agendas, packets, and minutes, but **no
   public eComment submission/export feed**. No separate Granicus/OpenGov comment portal.
3. **Agenda-packet attachments ("correspondence / written comments received")** — **THIS IS
   THE SOURCE.** Forwarded resident emails are bundled into the Complete Packet PDFs,
   identifiable by `From:/Sent:/To:/Subject:` headers, the "CAUTION: This email originated
   from outside of the organization" banner, mailto addresses, and `Name:/Address:` self-ID.
4. **Records / transparency / correspondence archive** — nothing additional beyond the
   packets.

## What was harvested
- **120 agenda packets** (the `packet_url` column of `meeting_minutes/minutes_index.csv`,
  covering **2022-2025**) were each downloaded, converted with `pdftotext -layout`, scanned
  for email artifacts, and deleted (disk discipline; only packets containing >=1 genuine
  resident comment were retained in `raw/`).
- **28 genuine resident written comments** were extracted after de-duplication.

### Per-year counts (genuine resident written comments)
| Year | Packets in index | Packets scanned | Genuine comments |
|------|------------------|-----------------|------------------|
| 2020 | 0 (no packets)   | 0               | 0                |
| 2021 | 0 (no packets)   | 0               | 0                |
| 2022 | 25               | 25              | 28               |
| 2023 | 38               | 38              | 0 *(see note)*   |
| 2024 | 38               | 38              | 0                |
| 2025 | 19               | 19              | 0                |
| **Total** | **120**     | **120**         | **28**           |

**Notes**
- **2020 and 2021 have no `packet_url` in the index** (and neither does 2026), so no written
  comments are harvestable for those years from this source. Minutes exist for those years
  (see `minutes_speaker_log.csv` for in-person speakers).
- All 28 genuine comments cluster in **2022** and concern the **Welby West / Bowman's Arrow
  rezone** (corner of 9000 S & 4800 W). The city clerk re-bundled this same correspondence
  into the "written comments received" section of roughly ten consecutive council packets
  from Aug 2022 through Jan 2023 and beyond. Cross-packet content de-duplication keeps each
  unique resident email **once** (attributed to the earliest packet that published it,
  2022-08-10/2022-09-14); the ~297 re-bundled copies are logged in
  `all_comments_dropped.csv` as `recurrent_correspondence_dup`. Without dedup the raw count
  would be ~330, but those are the same ~28 emails counted repeatedly, not distinct comments.
- 2023-2025 packets were scanned in full; the only email artifacts found in them were
  **staff memos, engineering/consultant traffic studies, and inter-agency (Salt Lake County,
  UDOT) correspondence** — not resident public comments — and were dropped
  (`vendor_or_firm:*`, `official_correspondence:*`, `internal_domain:*`,
  `other_government:*`). It appears West Jordan only bundles resident emails into packets
  when a controversial land-use item draws an email campaign; routine meetings carry none.

## Auditability
- `packets_scanned.csv` — one row per packet URL scanned (had_comments / n_comments /
  n_dropped / status) for all 120.
- `all_comments_dropped.csv` — every removed candidate with a `_drop_reason` (445 rows).
- `raw/` — only the 2 packet PDFs that hold the first appearance of a unique kept comment.

This is **not** a "no genuine written comments published" verdict — West Jordan does publish
them, just embedded inside agenda packets rather than on a dedicated page.
