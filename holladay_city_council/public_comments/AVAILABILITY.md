# Public comments — availability (Holladay City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.** (Audited 2026-07-12, browser UA.)

Holladay City accepts public comment two ways — (1) **in person** at the Council / Planning
Commission meeting (a resident completes a written request form handed to the City Recorder
and is given time to speak), or (2) **written comment emailed in advance** and **read aloud
by the Chair** at the meeting. The agenda instruction is printed verbatim: *"persons wishing
to comment on any item not otherwise on the agenda may provide their comment via email to the
Council before 5:00 p.m. on the meeting date to `scarlson@cityofholladay.com`, with the
subject line: Public Comment"*; the Planning Commission variant routes emailed comments to
`jteerlink@holladayut.gov` and states *"Emailed comments will be read by the Commission
Chair."* The city publishes **no** archive of those emailed comments: no dedicated
public-comments page, no eComment / Open City Hall / Speak-Up / Peak-Democracy portal, and no
"correspondence received" bundle in the agenda packets. The **only** public record of a
comment is the **clerk's paraphrase of speakers written into the meeting minutes** — a
speaker log, which is meeting-record notes, **NOT** public-submitted written comments, so it
does not populate `all_comments_clean.csv`.

**No populated `all_comments_clean.csv` was built** — the file is **header-only** (the 14-col
SLC/South Jordan schema). This is an honest empty result, not a gap to be filled.

## Avenues checked (comments-auditor hunt order)

1. **Dedicated published-comments page / archive** — **none.** The City Recorder's page
   (`https://holladayut.gov/departments/city_recorder/`, checked 2026-07-12) lists only the
   recorder's email/phone/office and the note that agendas post ≥24 h before each meeting; no
   public-comment submission form, no comment archive, no "correspondence received" link. No
   SLC-style weekly comment PDFs, no St. George-style `public_comments.php`.

2. **eComment / Open City Hall / Speak-Up / Peak-Democracy portal** — **none found.** Web
   search (2026-07-12) for Holladay + each portal brand surfaced only the Revize city site
   (`holladayut.gov`; `cityofholladay.com` 301-redirects to it), the **SuiteOne** meeting
   portal, and the Utah Public Notice (PMN) body pages — no online-comment submission or
   export feed. The **SuiteOne** portal (`holladayut.suiteonemedia.com`) exposes only
   agenda/packet/minutes documents per event — no "comment" or "correspondence" document type.

3. **Inside the minutes** — **speakers are transcribed inline, but as clerk paraphrase (a
   speaker log, not submitted comments).** Sampled both born-digital minutes on disk:
   - **Council 2025-12-04** (`meeting_minutes/raw/2025-12-04_council_minutes.pdf`): a
     **"VII. Public Comments"** section paraphrases in-person speakers in the third person,
     plus public-hearing sections that record *"Mayor Dahle opened the public hearing. There
     were no comments."* — i.e. attendance-style notes, not a submitted-comment corpus.
   - **Planning Commission 2025-04-01** (`meeting_minutes/raw/pc_2025-04-01_minutes.pdf`):
     emailed comments are explicitly **read into the record and summarized** — *"An email
     comment was received from a resident yesterday…"*, *"there was one emailed comment
     received…"*, *"there was one email submitted that expressed concerns"*. The emails
     themselves are **not** published; only the clerk's inline summary survives.

## Bottom line

Holladay is a **submit-only** city (the same posture as Taylorsville and South Jordan): the
genuine written-comment corpus does not exist as a published archive. When council/PC minutes
are ingested, the inline speaker/hearing notes should be captured as a labeled
**`minutes_speaker_log.csv`** (meeting-record notes) if desired — never as
`all_comments_clean.csv`. Re-audit if the city later adopts an eComment/Open City Hall portal
or begins publishing a correspondence bundle in its SuiteOne packets.
