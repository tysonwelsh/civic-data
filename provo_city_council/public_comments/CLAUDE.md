# Provo public comments — coverage & provenance

**The bar (READ FIRST):** `all_comments_clean.csv` holds ONLY **genuine
public-submitted written/online comments** — text residents actually wrote and
submitted (email / letter / eComment portal) and the city published, exactly like
SLC's weekly public-comment PDFs. **Clerk paraphrases of in-person speakers in the
minutes do NOT count** and are kept separately (see below).

## Files

| File | What it is |
|---|---|
| **`all_comments_clean.csv`** | Canonical output. SLC schema (`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`). **81 genuine written comments**, all `source=agenda_packet`, 100% `date_normalized`. |
| `all_comments_dropped.csv` | Audit trail (`_drop_reason`) — staff / vendor / applicant / no-name / too-short blocks dropped during packet extraction (35 rows). |
| **`packets_scanned.csv`** | **Full-coverage audit.** One row per Regular-Meeting packet scanned (date, packet_url, had_comments, n_comments, pages, size_bytes, from_blocks, note). **All 138** regular packets 2020–2026 scanned; 26 had ≥1 genuine comment. Lets you confirm every packet was checked without hoarding the PDFs. |
| **`minutes_speaker_log.csv`** | **MEETING-RECORD NOTES, NOT public comments.** 737 clerk third-person paraphrases of in-person speakers from the minutes (with video timestamps). Header line says so. Kept for reference; **never merge into `all_comments_clean.csv`**. |
| `AVAILABILITY.md` | Full avenue-by-avenue hunt + verdicts (PORTAL-GATED / IN-PACKETS / SUBMIT-ONLY). |
| `harvest_packets.py` | **Full harvest driver.** Iterates every Regular-Meeting `packet_url`, downloads + `pdftotext`s each, scans for genuine comments, KEEPS the PDF (`raw/packets/<date>_packet.pdf`) + text only when ≥1 comment is found, logs all to `packets_scanned.csv`. Resumable (skips dates already scanned). |
| `extract_packet_comments.py` | Parses resident email blocks out of `raw/packet_txt/packet_*.txt` → `all_comments_clean.csv`. Drops staff/vendor/applicant senders (name blocklist + role regex), joins multi-page letters across form-feeds with a rule-based page classifier (see "Cleaning rules" — replaced the old truncating first-form-feed cut on 2026-07-02), normalizes dates + names, de-dups. |
| `extract_comments.py` | LEGACY — produced the minutes paraphrases (now in the speaker log). Do not use to populate the clean CSV. |
| `raw/packets/` | The **26 comment-bearing** packet PDFs (renamed `<date>_packet.pdf`, ~1.3 GB) — provenance for every extracted row. Comment-free packets are NOT retained (logged in `packets_scanned.csv` instead). |
| `raw/packet_txt/` | `pdftotext -layout` output for the 26 kept packets (one `packet_<date>.txt` each). |
| `raw/` | Also: OpenGov fetch logs + archived shells (the gated portal evidence). |

## What each source yielded

### 1. Agenda-packet PDFs (`documentType=5`) — the ONLY source of genuine written comments
`source = agenda_packet`, `has_attachment = True`. Provo bundles **verbatim
resident emails/letters** (forwarded to the Planning Commission / Council) inside the
agenda packets, as `From:/Sent:/To:/Subject:` + body blocks — the public's own words,
mostly on contentious rezone/land-use items. **FULL HARVEST DONE: all 138 Regular-Meeting
packets 2020–2026 were downloaded + scanned** (`harvest_packets.py` → `packets_scanned.csv`).
26 packets carried ≥1 genuine comment → **81 genuine written comments** after staff/vendor/
applicant exclusion + de-dup. Comment-free packets were not retained (just logged), keeping
only the 26 comment-bearing PDFs (~1.3 GB) as provenance.

### 2. OpenGov "Open City Hall" (`provout`) — PORTAL-GATED, 0 rows recovered
The portal was real and used (dozens of live `Issue_*` topics with registered +
unregistered statements), but the live host cloaks all bot requests to HTTP 404, and
Wayback archived only the topic *shells* (e.g. Issue_11414 = "27 statements") — **not the
statement bodies**; `/Issue_*/statements` sub-pages have no snapshot. Unrecoverable here.
Main gap for typed online comment. Details + evidence in `AVAILABILITY.md` / `raw/`.

### 3. provo.gov council-comment pages — SUBMIT-ONLY, 0 rows
`provo.gov/546/Public-Comments` etc. explain how to submit (email council, in-person,
Open City Hall) but publish no archive of received comments.

### (reclassified) In-minutes speaker paraphrases — NOT counted
737 third-person clerk summaries of in-person speakers → moved to
`minutes_speaker_log.csv`. They are meeting-record notes, not written comments.

## Per-year (genuine written comments, `all_comments_clean.csv`)
| year | comments | regular packets scanned | packets w/ comments |
|------|----------|-------------------------|---------------------|
| 2020 | 60 | 26 | 10 |
| 2021 | 19 | 22 | 11 |
| 2022 | 2  | 23 | 4  |
| 2023 | 0  | 20 | 0  |
| 2024 | 0* | 22 | 1* |
| 2025 | 0  | 17 | 0  |
| 2026 | 0  | 8  | 0  |
| **total** | **81** | **138** | **26** |

\*The one 2024 comment-bearing packet (2024-04-30) held only a staff/mayor letter that was
dropped, so 2024 contributes 0 genuine resident rows. **Genuine attached resident comments
cluster hard on the contentious 2020–2021 land-use fights** (Foothills/Hillside Overlay,
Christensen Oil, Heron's Landing, LaFontaine, Osprey, East Bay). From 2023 on, packets carry
only the boilerplate "written comments … addressed in the Staff Report" footer with no
attached resident emails — that typed input now lives in the (gated) OpenGov portal.

## Cleaning rules (mirror SLC `clean_comments.py`)
- Parse each `From:/Sent:/To:/Subject:`+body email block from packet text; one row per block.
- **Drop non-public senders** → `all_comments_dropped.csv` (35 rows): city-staff / internal
  (role regex — Development Services, Council Policy Analyst, `@provo.org`, "Public Hearings",
  director/officer/coordinator/mayor…) PLUS a reviewed **name blocklist** of staff who reply
  inside threads (Gary McGinn, Robert Mills, Austin Taylor…), the **project applicant/landowner**
  (J Gordon, Bruce Nelson), **vendors** (Zagster Billing, Adam Greenstein, newspaper ad reps
  Jamie Rivera / David Mortensen) and a **councilmember/committee reply** (David Sewell). A
  petition/signature sheet is not a comment and none was emitted as one.
- Scrub the "CAUTION: …outside…" security banner; **join each letter across its page breaks
  with a rule-based classifier** (2026-07-02 fix). *History, honestly:* until 2026-07-02 the
  cleaner cut every body at the **first form-feed past 200 chars**. That did guarantee zero
  cross-commenter bleed (some packets bundle multi-commenter eComment tables and back-to-back
  letters with no recoverable per-email headers, and one matched `From:` block would otherwise
  swallow them), but it also **silently truncated every multi-page letter mid-sentence — 18 of
  81 rows** — and this file previously described that cut as if it were lossless. It was not.
  The replacement walks the letter page by page and joins a page only when it belongs to the
  same letter, using signals derived from reviewing every page boundary in all 26 packets:
  **STOP** at a blank page, at a page opening like another document (email headers `From:/Sent:/
  To:/Subject:/Date:` incl. lowercase-address forms, STAFF REPORT / ORDINANCE / RESOLUTION /
  Memo headers, OpenGov `opentownhall` comment-export pages, `PLxx…` case-number headings, and
  `Timestamp Name …` multi-commenter eComment tables — the original bleed hazard); **JOIN** a
  page opening mid-sentence (lowercase word / bracket / bullet); otherwise (capitalized prose)
  JOIN only if the letter so far does **not** already end in the sender's signature (first/last
  name in the last 8 non-blank lines). Then cut at strong document-section markers (STAFF
  REPORT / ORDINANCE / EXHIBIT …) as before. Hard cap raised 6000 → 20000 chars
  (`truncated_long` backstop; no row hits it).
- **Verification of the 2026-07-02 fix** (old CSV preserved at
  `_backups/2026-07-02/provo_city_council/public_comments/`): row count 81 → 81, per-year
  counts unchanged, dropped-audit rows 35 → 35. **19 rows changed**: 18 truncated letters
  extended to their genuine endings (old text is a strict prefix of the new text in every
  case — nothing reworded), 1 row (Brenton Chu) lost a stray `PROVO MUNICIPAL COUNCIL`
  staff-report header that had leaked into its tail. Rows ending on a dangling function word:
  6 → 0. The three audit-verified truncations now end at their signatures — McCoard
  (…`champion the "highest and best use." Melanie McCoard`), Steed (…`Respectfully submitted,
  Marc Steed`), Bogdin 2021-07-26 (…`-- Becky Bogdin Lakewood Neighborhood Chair`).
  **Cross-commenter bleed re-checked across all 81 rows: 0** (no foreign `From:/Sent:/Subject:`
  headers or third-party email addresses appear mid-row; the few `@provo.org` addresses inside
  rows are hearing-notice boilerplate the residents themselves quoted, present at identical
  offsets before the fix). Two rows end on same-submitter **attachment** content rather than a
  signature, faithfully to the source: Tom Scheidt 2020-09-22 ends in his own attached traffic
  spreadsheet, and Becky Bogdin 2020-05-26 (a ~20k-char position paper) ends in her attached
  area-map figure labels; Ken Millar 2020-10-05 is a neighborhood-meeting report that ends at
  the report's own final line (no signature in the source).
- Normalize the `Sent:`/`Date:` header → ISO `date_normalized` (falls back to meeting date →
  `date_from_filename` only if the email has no parseable date). **100% dated.**
- Normalize names: strip `<email>`/`[mailto:]`, flip Outlook `Last, First` → `First Last`,
  flag junk/placeholder sender names (`name_unreliable`) while keeping the genuine comment text.
- De-dup on (name, date, first 80 chars of comment) — the same household resubmitting on a
  different date is kept (e.g. the Bogdin family, Robert & Heidi Lawrence across items).
- `district`/`topic`/`page_numbers`/`period_*` left blank unless literally present; nothing invented.

## Honesty notes
- `comment` text here IS the resident's own written words (verbatim email/letter body),
  unlike the speaker log (which is clerk paraphrase).
- **Agenda-packet coverage is now COMPLETE**: all 138 Regular-Meeting packets 2020–2026 were
  downloaded + scanned (`packets_scanned.csv`), not a sample. The remaining ceiling is the
  **OpenGov "Open City Hall" portal**, which is bot-gated/Cloudflare-cloaked and was archived by
  Wayback only as topic *shells* (statement counts, not bodies) — unrecoverable without an
  interactive authenticated browser. So 2022+ typed online comment is largely outside this CSV
  by source-availability, not by omission. See `AVAILABILITY.md`.
- To re-run: `python3 harvest_packets.py` (resumable; re-downloads only un-scanned dates) then
  `python3 extract_packet_comments.py` (rebuilds the clean CSV deterministically from
  `raw/packet_txt/`). Do NOT run `extract_comments.py` to repopulate the clean CSV — it produces
  minutes paraphrases, which belong only in the speaker log.
