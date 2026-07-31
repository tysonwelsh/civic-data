# Public comments — availability audit (Herriman City)

**Verdict: HONEST-EMPTY — no published written-comment archive.** Herriman offers only
**submit-only** public-comment channels; nothing is published as a retrievable
written-comment dataset. `all_comments_clean.csv` is therefore **header-only** (the 14-col
collection schema, zero rows), which is *data*, not a gap — do not fabricate rows.

**Audit date:** 2026-07-11 (browser UA throughout). This supersedes the recon's
"UNCONFIRMED" placeholder with a completed audit.

## What was checked

| # | Source checked | Method | Finding |
|---|---|---|---|
| 1 | **PrimeGov portal** `herriman.primegov.com/public/portal` | Fetched portal UI | Exposes an **"Add a new comment"** (eComment) form and a **"Request To Speak"** form — both **submission** mechanisms tied to a live/upcoming meeting, not an archive. |
| 2 | **PrimeGov meeting API** `ListArchivedMeetings?year=YYYY` (2023–2025) + `ListUpcomingMeetings` | Enumerated every meeting's `documentList` template names + the `allowPublicComment`/`allowPublicSpeaker` flags | Document types published are only **Agenda, HTML Agenda, Packet, HTML Mini-Packet, Minutes, Presentations, Notice of Cancellation** — **no "Public Comment", "eComment", or "Correspondence" document exists**. `allowPublicComment`/`allowPublicSpeaker` are **False** on all archived meetings (and on the one upcoming meeting) — the eComment feature is toggled on only in the immediate pre-meeting window, and submissions are **not** retained as a public document. |
| 3 | **City site** `herriman.gov/agendas-and-minutes` | Fetched page | Links a **"Public Comment Form"** hosted on **Cognito Forms** (`cognitoforms.com/HerrimanCity1/PublicCommentForm`). Policy text: *"Citizens requesting to address the Council will be asked to complete a written comment form and present it to the City Recorder."* Submissions go **to the City Recorder** and are incorporated into the meeting record; the page shows **no public archive/list of submitted comments**. Email alternative: `recorder@herriman.org`. |
| 4 | **Agenda packets** (`documentList` `Packet` template) | Template-name enumeration (163 packets 2023–25) + recon's packet inspection | Packets bundle the agenda + staff reports; no standalone published written-correspondence archive is exposed as its own dataset. (Any correspondence embedded inside a packet PDF is a document-mining target, not a structured comment feed.) |

## Why header-only (not `minutes_speaker_log.csv` here)

Herriman minutes **transcribe/paraphrase public-hearing speakers inline** (clerk notes).
Per the collection's `extraction_standards`, those are **meeting-record speaker notes, NOT
genuine public-submitted comments**, and belong in a labeled `minutes_speaker_log.csv`
produced by the **minutes-extraction** pass — never in `all_comments_clean.csv`. That log
is out of scope for this comments audit (the minutes corpus is built by the separate
minutes/votes agent); it is not evidence of a published comment archive.

Comparable honest-zeros in the collection: **south_jordan** and **taylorsville** (both
"comments submit-only"). Herriman joins them.

## If this ever changes (refresh guidance)

- Watch the PrimeGov `documentList` for a new **"Public Comment" / "Correspondence"**
  template, or `allowPublicComment=True` meetings that later publish a comment report.
- The Cognito public-comment form and `recorder@herriman.org` inbox are **not** public;
  a GRAMA request would be required to obtain submitted comments — an acquisition path, not
  a scrape.
- Written correspondence embedded **inside** agenda packets could be mined per-meeting
  (document task), and if recovered would populate this table with `source=agenda_packet`.
