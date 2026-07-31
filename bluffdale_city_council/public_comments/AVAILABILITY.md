# Public comments — availability (Bluffdale City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED — honest empty result.**

Bluffdale City accepts public comment two ways — (1) **in person** at the Council meeting,
or (2) **written comment emailed in advance** to **`councilmeetingcomment@bluffdale.gov`**
(older agendas: `councilmeetingcomment@bluffdale.com`) **by 4:00 p.m. on the day of the
meeting**. Every Council agenda 2022→2025 prints the same rule and states that emailed
comments **are submitted to the Council but WILL NOT be read at the meeting** — and the
city posts **no** archive of them. There is **no dedicated comments page, no eComment /
Open City Hall / Speak-Up portal, and no "correspondence received" document type** in the
AgendaCenter or DocumentCenter.

The **only** public record of a comment is the **clerk's paraphrase of in-person speakers
written into the meeting minutes** (e.g. 2025-09-24: *"Rob Hughes reported that he lives on
Pastoral Way…"*). Per the collection standard that is **meeting-record speaker-log
material, NOT public-submitted written comments**, so it belongs in a labeled
`minutes_speaker_log.csv` (built by the minutes pipeline) and **never** populates
`all_comments_clean.csv`.

**`all_comments_clean.csv` is written HEADER-ONLY** (the 14-column collection schema, zero
data rows). No genuine published written-comment corpus exists to fill it. This is an
honest empty result, not a gap to be backfilled.

## Avenues checked (comments-auditor hunt order, GET-only, 2026-07-12)

1. **Dedicated published-comments page / archive** — **none.** The Elections page
   (`https://www.bluffdale.gov/498/Elections`) and the site footer expose only generic
   contact routes (`info@bluffdale.gov`, City Recorder `ttimothy@bluffdale.gov`,
   "Report Your Concern"). No comment-submission form, no comment archive, no SLC-style
   weekly comment PDFs, no St. George-style `public_comments.php`.

2. **eComment / Open City Hall / Speak-Up / Peak Democracy portal** — **none found.** Web
   search surfaced only the CivicPlus/CivicEngage AgendaCenter (Agenda + Minutes doc types)
   and the PMN mirror — no online-comment submission or export feed.

3. **The submission rule itself** — **confirmed submit-only, explicitly not read/posted.**
   Multiple 2022–2025 Council agendas (verified via web search of the AgendaCenter
   `ViewFile` docs and PMN notices) carry: *"the public may comment … or by emailing
   comments to councilmeetingcomment@bluffdale.gov by 4:00 PM the day of the meeting;
   emailed comments will be submitted to the City Council but not read at the meeting."*
   Accepted but **not published** — a legitimate "not published" finding.

4. **Inside the minutes** — in-person speakers are transcribed inline as **clerk paraphrase
   (third-person speaker log), not submitted comment text** (recon verified on the
   2025-09-24 council minutes). This is `minutes_speaker_log.csv` material, labeled NOT
   comments; finding only this is **not** "PUBLISHED."

5. **Agenda packets ("correspondence / written comments received")** — Bluffdale's
   AgendaCenter publishes an **Agenda** and a **Minutes** doc per meeting; no bundled
   "correspondence" / forwarded-resident-email container surfaced (unlike West Jordan's
   PrimeGov packets). Emailed comments would be retrievable only by a GRAMA records request
   (out of scope; GET-only, non-fabricating).

## How comments are submitted (summary)
- **In person** at the meeting (Council Chambers, Bluffdale City Hall, 2222 W 14400 S).
- **Written, in advance:** email `councilmeetingcomment@bluffdale.gov` (older `.com`) by
  **4:00 p.m.** on the meeting day. **Submitted to Council but NOT read aloud, and not
  posted.**
- No online comment portal; no published archive of the emailed comments.

```json
{"verdict":"SUBMIT-ONLY / NOT PUBLISHED","csv":"header-only","locations":[],"notes":"Written comment accepted only by email to councilmeetingcomment@bluffdale.gov (older .com) by 4:00 p.m. meeting day, or in person; agendas 2022-2025 state emailed comments are submitted to Council but NOT read at the meeting and are not posted. No dedicated comments page, no eComment/Open City Hall portal, no correspondence document type in AgendaCenter/DocumentCenter. Only public record of comment is the clerk's third-person paraphrase of in-person speakers inside the minutes = minutes_speaker_log material (meeting-record notes), NOT the comments dataset. all_comments_clean.csv written header-only; honest empty result."}
```
