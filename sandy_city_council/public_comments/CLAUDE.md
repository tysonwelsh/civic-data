# public_comments — Sandy City Council

## Verdict: SUBMIT-ONLY / NOT PUBLISHED

Sandy City does **not publish genuine written/online public comments**. Public comment to
the Council is **submit-only**: residents either speak live (in person or via Zoom) during
the "General Citizen Comment Period" / a per-item public hearing, **or** email
`CitizenComment@sandy.utah.gov` (alt: `mapplegarth@sandy.utah.gov` by 3 PM on meeting day)
to be distributed to Council and "read into the record." The submitted text itself is **not
published** anywhere public — it is obtainable only via a GRAMA records request. Full audit
trail (every avenue + URLs) in **`AVAILABILITY.md`**.

Because nothing genuine is published, **`all_comments_clean.csv` is header-only** (the SLC
schema, zero data rows). That is the correct, legitimate outcome — do not backfill it from
the minutes (see below).

## Files

| File | What it is |
|---|---|
| `all_comments_clean.csv` | **Header-only.** Reserved for genuine public-submitted written/online comments (SLC schema). None exist for Sandy → no data rows. Do not populate from minutes. |
| `minutes_speaker_log.csv` | **NOT the comments dataset.** Clerk paraphrases of in-person speakers (and a handful of emails read aloud) extracted from the 274 minutes. Meeting-record notes only. |
| `AVAILABILITY.md` | The availability audit: all six avenues checked, URLs, and the verdict + JSON. |
| `raw/` | (empty) reserved for raw published-comment source files, if Sandy ever publishes any. |

## `minutes_speaker_log.csv` — read this carefully

These are **meeting-record notes, NOT public-submitted written comments** (the first line of
the CSV says so). They are third-person clerk paraphrases of people who spoke at meetings
("Josh Karr spoke… He urged…"), so per `extraction_standards.md` they do **not** belong in
`all_comments_clean.csv` and must never be presented as "the public comments."

- Columns: `date_normalized, contact_name, subject, comment, source_file, quality_flag`.
- `subject` is an inferred short topic label; `comment` is the clerk's paraphrase.
- ~361 speaker rows across **117 meetings** (the rest had no named public speaker — many
  meetings show only "Public comment opened. Public comment closed.").
- `quality_flag` values (`|`-joined):
  - `paraphrase_only` — on every row (all are clerk paraphrases).
  - `public_hearing` — spoke during a per-item public-hearing comment period (vs the general
    citizen comment period). ~113 rows.
  - `email_read_into_record` — the minutes note an emailed comment that staff read aloud and
    paraphrased (the closest thing to a written comment, but still only a minutes paraphrase,
    not published verbatim text). ~7 rows.
- **Excluded** from the log: council members, the Mayor, city staff/directors, and invited
  presenters/applicants giving staff reports (they are not members of the public commenting).
  Applicants/their attorneys speaking *inside* a public-hearing comment period are included.

## How comment works at Sandy (for future runs)

- **Granicus SpeakUp / eComment portal** (`https://sandyutah.granicusideas.com`) was
  **briefly active in 2020–2021** — the 2020–21 minutes carry per-item "Click here to
  eComment on this item" links to `granicusideas.com`. But it is now **dormant/empty**
  ("recently launched," "No Meetings Scheduled"), and **no submissions from any era are
  publicly visible or exportable**; every Legistar meeting detail shows eComment **"Not
  available."** If that portal ever re-activates and exposes submissions, it becomes the
  genuine-comments source — re-check it and the events API. (A future deep dive could probe
  Wayback captures of specific 2020–21 `granicusideas.com` item pages.)
- **Agenda packets** (`View.ashx?M=A…` / `M=AO…`) were sampled (budget + zoning hearings)
  and contain **no "Correspondence / Written Comments Received" section** — so packets are
  not a hidden comment source here either.
- To actually obtain emailed comment text, a **GRAMA** request is required
  (`https://sandy.utah.gov/440/GRAMA-Requests`) — out of scope for this archive.

## Do NOT

- Do not move speaker-log rows into `all_comments_clean.csv`.
- Do not declare comments "PUBLISHED" on the strength of the speaker log — finding only
  in-person speaker paraphrases is explicitly **not** "published."
