# public_comments/ — Orem, Utah

## What's here

| File | What it is |
|---|---|
| `all_comments_clean.csv` | **95 genuine public-submitted WRITTEN comments** — residents' own verbatim text, published by the city as attachments at the end of the 2020–2021 City Council minutes. The ONLY genuine-comment dataset. |
| `all_comments_dropped.csv` | 4 rows removed (developers / applicant agents / real-estate reps commenting in a business capacity), each with `_drop_reason`. Audit trail — nothing silently deleted. |
| `minutes_speaker_log.csv` | **122 in-person speakers** paraphrased by the clerk in the minutes. **MEETING-RECORD NOTES, NOT public-submitted comments** (header note in the file). Do NOT present as the comments dataset. Note: built before the 68 empty minutes were OCR-repaired, so it **undercounts 2022–2026 in-person speakers** — regenerate over the full minutes for complete coverage. |
| `raw/` | The 9 comment-bearing source minutes `.md` files (only the ones that produced clean comments). |
| `AVAILABILITY.md` | The 4-avenue hunt + verdict (**IN-PACKETS**, i.e. embedded in 2020–2021 minutes). |

## The key distinction (read `extraction_standards.md`)

- **`all_comments_clean.csv`** = genuine public-submitted written/online text the
  city published (here: the verbatim comments residents submitted and that were
  "attached to the end of the minutes in their entirety" during the 2020–2021
  electronic-meeting period). `source = minutes_attached_written`.
- **`minutes_speaker_log.csv`** = clerk's third-person paraphrase of who spoke
  in person ("X stated…"). These are meeting-record notes, NOT the public's own
  words. Kept separate, clearly labeled. **Never merge into the clean CSV.**

## Schema

`all_comments_clean.csv`:
`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`
- `date` / `date_normalized` = the **meeting date** (ISO; the published attachment
  is dated to the meeting). 100% populated → `quality_flag` carries
  `date_from_filename` on every row.
- `district` = empty — **Orem is at-large, no districts** (see `../geo/CLAUDE.md`).
- `comment` = full verbatim re-stitched text (page-footer / `DRAFT` watermark
  lines that interrupted the comment were stripped and the text re-joined).
- `quality_flag` `|`-joined: `no_name` (9 anonymous submissions), `short_comment`.

`minutes_speaker_log.csv`:
`date_normalized,contact_name,subject,comment,source_file,quality_flag`
(preceded by a `#` note line declaring these are meeting-record notes).

## Provenance / how to extend

- Genuine written comments exist **only** for the 2020–2021 electronic-meeting
  window — that is the era Orem published resident text inline. After in-person
  meetings resumed, the city stopped publishing written comments (the CivicClerk
  written-comment feature is disabled on all events, and agenda packets carry no
  correspondence section — see `AVAILABILITY.md`).
- To add more written comments you would need new published sources to appear
  (CivicClerk `publicCommentsEnabled` turned on with published-back comments, or a
  packet "Correspondence" section). None exist as of the 2026-06 build.
- The speaker log was extracted from the PERSONAL APPEARANCES / public-comment
  sections across all 130 minutes `.md` files; "No personal appearances" sections
  were skipped.

## Don't

- Don't treat `minutes_speaker_log.csv` as public comments.
- Don't add a `district` value — Orem has none.
- Don't re-download CivicClerk/Drive agenda packets expecting correspondence;
  two were sampled and confirmed to contain none (and large PDFs strain the disk
  guard).
