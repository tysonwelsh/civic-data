# Public comments — availability (South Jordan City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**

South Jordan City accepts public comment two ways — (1) **in person** at the Council
meeting (3-minute limit), or (2) **written comment emailed in advance** to the City
Recorder, **Anna Crookston, `acrookston@sjc.utah.gov`, by 3:00 p.m. on the day of the
meeting** (this instruction is printed verbatim on every agenda). The city publishes
**no** archive of those emailed written comments: no dedicated comments page, no
eComment / Open City Hall / Speak-Up portal, no "correspondence received" folder, and no
correspondence section inside the agenda packets. The **only** public record of a comment
is the **clerk's paraphrase of in-person speakers written into the meeting minutes** — a
speaker log, which per `extraction_standards.md` is **meeting-record notes, NOT
public-submitted written comments**, so it does not populate `all_comments_clean.csv`.

**No `all_comments_clean.csv` was built** (no genuine published written-comment corpus
exists). This is an honest empty result, not a gap to be filled.

## Avenues checked (comments-auditor hunt order)

1. **Dedicated published-comments page / archive** — **none.** The City Council page
   (`https://www.sjc.utah.gov/241/City-Council`, checked 2026-07-06) carries meeting
   times, Zoom links, agendas, minutes, and member contacts, but no public-comment
   submission form, no comment archive, and no "correspondence received" link. No
   SLC-style weekly comment PDFs and no St. George-style `public_comments.php`.

2. **eComment / Open City Hall / Speak-Up / Peak Democracy portal** — **none found.**
   Web search for South Jordan + each portal brand (2026-07-06) surfaced only the
   CivicPlus site and the Municode meetings portal — no online-comment submission or
   export feed. Municode Meetings (`https://southjordan-ut.municodemeetings.com/`) exposes
   only three doc types per meeting — **Agenda, Minutes, Packet** — with no "comment" or
   "correspondence" document type.

3. **Inside the minutes** — **in-person speakers are transcribed inline, but as clerk
   paraphrase (a speaker log, not submitted comments).** Sampled
   `DocumentCenter/View/7551/03-18-2025-...-Meeting-Minutes` (17 pp, born-digital text):
   the **"F. Public Comment"** section names each speaker with a `(Resident)` tag and
   gives a detailed **third-person near-verbatim paraphrase** of their remarks
   (e.g. *"Erie Walker (Resident) requested that the city consider creating a collection
   point for fluorescent light tube recycling…"*; *"Catherine Campbell (Resident) noted
   this was the first meeting she has attended…"*). Public **hearings** likewise record
   *"There were no public comments"* or paraphrase those who spoke. **Fidelity: named
   speakers + rich paraphrase, third-person, not the citizen's own submitted text.** No
   emailed/written comments are reproduced or listed anywhere in the minutes. → This is
   the `minutes_speaker_log.csv` material (built by the minutes pipeline, labeled NOT
   comments), never `all_comments_clean.csv`.

4. **Agenda packets ("correspondence / written comments received")** — **checked; none
   bundled.** South Jordan's Municode `MEET-Packet-<uid>.pdf` is an **agenda + minutes +
   staff-report + contract bundle**, not a correspondence container. Retrieved and
   text-scanned the 2025-10-21 Council packet (`MEET-Packet-4241b93d…`, 8-page bundle,
   ~3,400 text lines, includes a public hearing on the Village at High Ridge development):
   the only email artifact present is the recorder's submission instruction; **no
   forwarded resident emails** (no `From:/Sent:/Subject:` blocks, no "CAUTION: external"
   banner, no "Dear Council" letters, no petitions/comment cards, no "the following
   correspondence was received"). The document's `SIGNATURE` markers are franchise/contract
   signature pages, not comment petitions. This is unlike West Jordan, where the clerk
   forwards resident emails into the PrimeGov packet — South Jordan does not.

5. **Records / transparency / correspondence archive** — none surfaced. The
   DocumentCenter (`https://www.sjc.utah.gov/DocumentCenter`) shows no Correspondence /
   Public Comment / Communications category. Emailed comments would be retrievable only by
   a GRAMA records request (out of scope; GET-only, non-fabricating).

6. **Email-only submission — confirmed** as the written-comment channel (item above):
   `acrookston@sjc.utah.gov`, deadline 3:00 p.m. meeting day. Accepted but **not
   published** — a legitimate "not published" finding.

## What the minutes DO carry (for downstream, labeled correctly)
In-person Public Comment speakers are named + paraphrased in the minutes. When the minutes
are extracted, that belongs in a **`minutes_speaker_log.csv`** (meeting-record notes),
explicitly **not** merged into `all_comments_clean.csv`. Finding only this is **not**
"PUBLISHED."

## How comments are submitted (summary)
- **In person** at the meeting (Council Chambers, 1600 W. Towne Center Dr.), 3-minute limit.
- **Written, in advance:** email City Recorder Anna Crookston `acrookston@sjc.utah.gov` by
  3:00 p.m. on the meeting day. **Virtual/phone attendees may not comment live.**
- No online comment portal; no published archive of the emailed comments.

## Sources checked (all GET-only, 2026-07-06)
| Avenue | URL | Result |
|---|---|---|
| City Council page | https://www.sjc.utah.gov/241/City-Council | No comment form/archive; Zoom + email route only |
| Council agenda (submission rule) | https://mccmeetings.blob.core.usgovcloudapi.net/sojordanut-pubu/MEET-Agenda-4241b93d99a244b99b0292b3df64a573.pdf | "submit written comments … to City Recorder … by 3:00 p.m." |
| Council minutes sample | https://www.sjc.utah.gov/DocumentCenter/View/7551/03-18-2025-South-Jordan-City-Council-Meeting-Minutes | Named in-person speakers, third-person paraphrase (speaker log) |
| Council packet (correspondence check) | https://mccmeetings.blob.core.usgovcloudapi.net/sojordanut-pubu/MEET-Packet-4241b93d99a244b99b0292b3df64a573.pdf | Agenda+minutes+staff/contracts; NO forwarded emails/correspondence section |
| Municode Meetings portal | https://southjordan-ut.municodemeetings.com/ | Doc types = Agenda/Minutes/Packet only; no correspondence type |
| DocumentCenter | https://www.sjc.utah.gov/DocumentCenter | No Correspondence/Public-Comment category |
| Portal search (eComment/Open City Hall/Speak-Up/Peak Democracy) | web search | None exist for South Jordan |

```json
{"verdict":"SUBMIT-ONLY / NOT PUBLISHED","locations":[],"notes":"Written comment accepted only by email to City Recorder Anna Crookston (acrookston@sjc.utah.gov) by 3:00 p.m. meeting day, or in person (3-min limit); virtual/phone attendees cannot comment live. City publishes NO archive of emailed comments: no comments page, no eComment/Open City Hall portal, no correspondence document category, and agenda packets (MEET-Packet-*.pdf) are agenda+minutes+staff-report bundles with no forwarded-email/correspondence section (verified on the 2025-10-21 Council packet incl. a public hearing). The only public record of comment is the clerk's named, third-person near-verbatim paraphrase of in-person speakers inside the minutes = a minutes_speaker_log (meeting-record notes), NOT the comments dataset. No all_comments_clean.csv built; honest empty result."}
```
