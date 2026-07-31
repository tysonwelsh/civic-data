# public_comments/ — Nephi, UT

## TL;DR
Nephi publishes **no genuine written/online public comments**. Public comment is taken
**in person only** (council meetings / public hearings); there is no comment page, no
correspondence/"written comments received" archive, no eComment / Speak-Up / Open City
Hall portal, and no comment attachments in the CivicPlus AgendaCenter agenda packets.
→ **Verdict: IN-MINUTES-ONLY.**

- `all_comments_clean.csv` is **header-only (0 rows)** on purpose — this is the correct
  result, not a missing dataset. Do NOT backfill it with minutes paraphrases.
- The only public-comment material that exists is a **speaker log** of in-person speakers
  paraphrased by the clerk in the minutes → `minutes_speaker_log.csv` (**116 rows**,
  2020–2026). Per `extraction_standards.md` those are **meeting-record notes, NOT
  public-submitted written comments**, and must never be presented as the comments dataset.

See `AVAILABILITY.md` for the full hunt (city site, AgendaCenter packets, eComment portal,
minutes, PMN mirror, records) with URLs.

## The distinction (read before touching the CSVs)
- `all_comments_clean.csv` = residents' OWN published written/online text. Nephi publishes
  none → **header only, 0 rows**.
- `minutes_speaker_log.csv` = the clerk's **third-person PARAPHRASE** of who spoke in
  person during "PUBLIC COMMENT:" / public hearings ("Joel Cowan asked what the current
  code allows for chickens."). These are meeting-record notes, NOT the public's own written
  words. `quality_flag = clerk_paraphrase_not_written_comment` on every row.

## Files
| File | What it is |
|---|---|
| `all_comments_clean.csv` | Genuine written/online comments — **header only, 0 rows** (IN-MINUTES-ONLY; none published). SLC schema. |
| `all_comments_dropped.csv` | Drop log — header only (no genuine comments ingested, nothing to drop). |
| `minutes_speaker_log.csv` | **116** in-person public-comment speakers, 2020–2026 (88 distinct), paraphrased from the council minutes. First line is a header note stating these are NOT written comments. Columns: `date_normalized, contact_name, subject, topic, comment, source, source_file, quality_flag`. |
| `extract_speaker_log.py` | Deterministic extractor (no fabrication) that rebuilds the speaker log from `meeting_minutes/minutes/**/*.md`. Copies the clerk paraphrase verbatim into `comment`. |
| `AVAILABILITY.md` | Avenues checked (with URLs) + IN-MINUTES-ONLY verdict. |
| `raw/` | (empty) reserved for raw comment files — none exist for Nephi. |

## How the extractor works (and its guards)
- Walks each minutes `.md`; ALL-CAPS lines (incl. inline `PLEDGE OF ALLEGIANCE: ...`
  flattened headers) set the current section. Paragraphs under a `PUBLIC COMMENT` /
  `PUBLIC HEARING` / `PUBLIC INPUT` header, plus inline "opened ... public comment."
  triggers, are scanned for a leading **named member of the public**.
- A row is emitted only when the paragraph starts with a 2–3-word name AND that speaker's
  **own first sentence** contains a speaking verb / residency phrase.
- **Excluded:** city staff & officials (title-prefixed lines like "City Attorney …",
  "Library Director …", "Recreation Director …"; and the bare City Administrator name
  "Seth Atkinson" et al. via `STAFF_NAMES`), the mayor, and sitting council members
  (the minutes prefix them "Councilor …"; a bare council name whose only verb is in a
  *later* sentence about someone else is rejected by the first-sentence rule — e.g. a
  2025 "Shari Cowan" deliberation line was correctly dropped).
- **Note on intent:** the minutes treat a person as a *public commenter* when they appear
  with no "Councilor" prefix and "address the council." So former officials speaking as
  residents are legitimately included (e.g. former mayor **Glade Nielson** in 2025 —
  "said he has his citizen hat on …"; former councilman **Larry Ostler**). This mirrors
  the source's own framing and is intentional, not a leak.

## Reproduce
```bash
python3 extract_speaker_log.py   # -> minutes_speaker_log.csv (116 rows from 243 minutes)
```

## Don't
- Don't move speaker-log paraphrases into `all_comments_clean.csv`. Different things.
- Don't treat the header-only `all_comments_clean.csv` as a bug — it IS the verdict.
- Don't go hunting agenda packets for comment letters — City Council AgendaCenter has only
  Agenda + Minutes (thin 2-page agendas), no correspondence attachments (verified).
