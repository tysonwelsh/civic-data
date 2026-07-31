# West Valley City — Public Comments

## TL;DR — what's in this directory

West Valley City does **not publish a dataset of genuine public-submitted written/online
public comments** (no eComment / Speak-Up portal, no published-comments PDFs, no
"correspondence" document type, no written-comment section in agenda packets). The full
hunt — OnBase document types, agenda packets, the city website, GRAMA/transparency archives,
the Utah PMN site, and Wayback — is documented in **`AVAILABILITY.md`**.

Consequently:

- **`all_comments_clean.csv` is intentionally EMPTY (header row only).** There is no
  genuine written/online public-comment dataset to populate it with. This is the correct,
  honest state — not a missing file. Do **not** backfill it with the minutes paraphrases.
- The City Recorder's **third-person paraphrases of in-person speakers**, transcribed inside
  the Regular-meeting minutes, are preserved separately in
  **`minutes_speaker_log.csv`** — clearly headed as **meeting-record notes, NOT
  public-submitted written comments**. These are testimony summaries, not the public's own
  written words, so per `extraction_standards.md` they may **not** go in the comments table.

## Why `all_comments_clean.csv` is empty (the bar)

Per `~/.claude/skills/build-city-data-repo/references/extraction_standards.md`, the comments
dataset must be **genuine public-submitted written/online comments** — text the public
actually wrote and submitted (web form / email / eComment / uploaded letter) and that the
city **published**, like SLC's weekly public-comment PDFs. Clerk paraphrases of in-person
speakers are explicitly **excluded**.

WVC's only public-comment channel is **in-person at the Regular meeting** ("request
recognition by the Mayor … approach the microphone"). The Recorder paraphrases each speaker
in the minutes. There is no published written/online comment dataset anywhere (see
`AVAILABILITY.md` for every avenue + verdict). Therefore the clean table is empty.

**The one near-miss:** during 2020 COVID *electronic* meetings the Recorder twice read a
resident's emailed/written submission **verbatim** into the record (2020-07-13 Monica Dixon;
2020-07-27 Fattima Ahmed/UCA). These are genuine written text but exist **only** as quotes
embedded in two minutes PDFs — n=2 out of ~222 meetings, not a published dataset. Extracting
just those two and presenting them as "WVC's written public comments" would misrepresent the
source, so they are **documented in `AVAILABILITY.md`** and left in the minutes, not pulled
into the clean CSV. (Full rationale in `AVAILABILITY.md` → "COVID-era exception".)

## Files

- **`AVAILABILITY.md`** — the authoritative record of the written-comment hunt: every
  avenue (OnBase doctypes, agenda packets, city site, eComment/portal, GRAMA, PMN, Wayback),
  its URL, and its verdict. **Read this first.**
- **`all_comments_clean.csv`** — SLC schema header, **0 data rows** (correctly empty).
  Schema:
  `date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`.
  If WVC ever starts publishing genuine written comments, that is where they go
  (`source = written_published` or `agenda_packet`, 100% `date_normalized`).
- **`minutes_speaker_log.csv`** — the **in-person speaker paraphrases** lifted from the
  Regular-meeting minutes (824 rows + a multi-line header banner). Header explicitly states
  these are **third-person meeting-record notes, NOT public-submitted written comments**.
  This is the speaker log, **not** the comments dataset; never present it as the latter.
- **`extract_comments.py`** — the parser that slices the "PUBLIC COMMENT PERIOD" section out
  of each `*regular*.md` minutes file and produces the speaker-log rows (handles the two
  minutes layouts, page-break artifacts, continuation re-stitching, and routes
  council/mayor/staff to the dropped audit). Idempotent; rebuilds from the minutes markdown.
- **`all_comments_dropped.csv`** — audit trail of paragraphs the parser dropped while
  building the speaker log (`official_or_staff`, `official_continuation`,
  `no_comments_procedural`, `empty_placeholder`, `orphan_continuation`), each with a
  `_drop_reason`. Nothing silently discarded.
- **`raw/`** — empty. (Would hold downloaded written-comment source files if any existed.
  None do.)

## Speaker-log details (for `minutes_speaker_log.csv`)

The speaker log covers **Regular** meetings only (Study sessions have no public-comment
period). ~222 Regular minutes scanned (2020–2026); 216 had ≥1 speaker. Each row is one
in-person speaker, `source = in_person_minutes`, `comment` text = the Recorder's
**paraphrase** (treat as a staff summary, not the speaker's verbatim words), no attachments.
See the header banner inside the CSV and the parser comments in `extract_comments.py` for the
section-delimiter heuristics, speaker-detection rules, and cleaning decisions.

## For the orchestrator

- Do **not** run `build_weeks.py` from here (handled at repo level).
- The empty `all_comments_clean.csv` is **intended**. Do not treat it as a build failure and
  do not repopulate it from `minutes_speaker_log.csv`.
- Re-run the hunt only if WVC changes vendors or stands up an eComment/Speak-Up portal;
  start from the avenue table in `AVAILABILITY.md`.
