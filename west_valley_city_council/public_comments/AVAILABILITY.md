# Genuine written public comments — availability hunt (West Valley City)

**Target** (per `extraction_standards.md` "What counts as a public comment"): genuine
public-submitted **written / online** public comments — the resident's own submitted text,
*published* by the city (like SLC's weekly public-comment PDFs). Clerk paraphrases of
in-person speakers recorded in the minutes do **not** count.

**Hunt date:** 2026-06-24. Every avenue below was probed directly.

## Verdict (one line)

**WVC does NOT publish a dataset of genuine public-submitted written/online comments.**
The only public-comment channel is **in-person at the meeting**; the City Recorder
**paraphrases** each speaker in the Regular-meeting minutes. Those paraphrases live in
`minutes_speaker_log.csv` (clearly labeled as meeting-record notes, NOT comments). The one
exception — a handful of COVID-era written submissions the Recorder read **verbatim** into
the record — is tiny (2 instances) and is published *only* as quotes embedded in the
minutes, not as a separate written-comment dataset. `all_comments_clean.csv` is therefore
correctly **empty** (header only). See "COVID-era exception" below for why those 2 are not
broken out.

---

## Avenues checked

### 1. OnBase document types (`ob.wvc-ut.gov/OnBaseAgendaOnline/`) — **only Agenda + Minutes**
- Portal serves City Council meetings under meeting-type IDs `109,110,111`.
- Per-meeting documents are exposed **only** as two document types:
  - `documentType=1` = **Agenda**
  - `documentType=2` = **Minutes**
- Confirmed by parsing the full meeting-search HTML for **both 2020 and 2026**:
  - 2026 (Jan–Jun): 52× `doctype=1`, 42× `doctype=2`; document labels seen = only
    `Agenda` / `Minutes`.
  - 2020 (full year): 186× `documentType=1`, 168× `documentType=2`; labels = only
    `Agenda` / `Minutes`.
- The `&doctype=N` query param on `ViewMeeting?id=<id>&doctype=N` is **client-side only** —
  values 1–6 all return the identical 14 KB JS shell (the param just tells the SPA which
  tab to open). It does **not** select a hidden document type. There is **no**
  public-comment / correspondence / "written comments received" document type.
- Download mechanism (for the record): the SPA's `DownloadFile/...` URL is a JS bouncer
  that rewrites to `DownloadFileBytes/...`; the real PDF is at
  `…/Documents/DownloadFileBytes/<MeetingType>_<id>_Agenda_<date>.pdf?documentType=1&meetingId=<id>`
  (browser User-Agent + a `ViewMeeting` referer required, else 403/redirect).

  **Verdict: PUBLISHED — but only Agenda + Minutes. No written-comment doc type.**

### 2. Agenda packets — **thin outline, no "correspondence" / "written comments" section**
- Downloaded a recent Regular-meeting agenda (meeting 8345, 2026-06-09):
  `Regular_Meeting_8345_Agenda_6_9_2026_6_30_00_PM.pdf` — **3 pages**, a bare agenda
  outline (Call to Order, Roll Call, Approval of Minutes, **Public Comment Period**,
  Public Hearings, Consent, Action items, Adjourn). No attachments bundle, **no**
  "Correspondence", "Written Comments Received", or "Public Input" attachment section.
- The agenda's Public-Comment paragraph spells out the **process** and confirms it is
  **in-person only**:
  > "Any person wishing to comment during the comment period shall request recognition by
  > the Mayor. Upon recognition, the citizen shall approach the microphone. All comments
  > shall be directed to the Mayor."

  No email address, no online-form link, no written-submission option.
- Rendered agenda (`Documents/ViewAgenda?meetingId=8345`) shows agenda items load via
  `loadAgendaItem(<id>)`; the item endpoint (`ViewMeetingAgendaItem`) requires the SPA's
  AJAX context and 302s/500s on a direct GET — but the *agenda outline itself* has no
  public-correspondence item, so there is nothing to bundle.

  **Verdict: IN-PACKETS = NO. Packets are agenda outlines + staff reports, not public mail.**

### 3. City website (`wvc-ut.gov`) — **no published-comments page, no live eComment portal**
- **`/15/City-Council`** — explains meetings are open & streamed; directs questions to the
  City Recorder (801-963-3203). **No** comment form, email-for-comment, or comments archive.
- **`www.wvc-ut.gov/PublicComment`** — surfaced in search as a COVID-era electronic-
  participation shortcut ("to participate … electronically, visit www.wvc-ut.gov/PublicComment
  prior to 2:30 PM on the day of the meeting"). It **now returns HTTP 404** and **was never
  captured by the Wayback Machine** (`archived_snapshots: {}`). It was a transient live-
  participation redirect (to join/speak remotely during electronic meetings), **not** a
  written-comment archive — and it is gone.
- **`/837/View-Online`** — 302-redirects straight to the YouTube livestream
  (`youtube.com/@wvctv2290/streams`). Live video only; no comment intake or archive.
- **Wayback CDX** for the whole domain: no `/publiccomment`, `/ecomment`, `/correspondence`,
  or council-comment-archive page ever existed. The only "comment" URLs in the archive are
  **Facebook social-widget artifacts** (`comment.create`, `comments.add`, `xfbml.comments`)
  and old CivicPlus "Community Voice / Community Connection" engagement-widget images —
  a general civic-idea module, **not** council public comment, and long dead.
- **GRAMA / Records** (`/260/Administrative-Government-Records-Reques`, `/135/Records-Division`)
  — a **request-only** Online Records Portal (submit a request, 10-business-day response).
  It does **not** publish an archive of council correspondence or public comments.
- **Government Transparency** (`/1033`) — financial/admin only (budget, property tax,
  lobbyists, officials' schedules, Truth-in-Taxation). **No** public-comment archive.

  **Verdict: SUBMIT-ONLY / NOT-PUBLISHED. No portal, no published written-comment archive.**

### 4. Utah Public Notice Website (PMN, body id 398) — **Minutes + agenda handouts only**
- `utah.gov/pmn/sitemap/publicbody/398.html` posts only **"Meeting Minutes"** and
  **"Public Information Handout"** (the agenda) per meeting. **No** correspondence or
  written-comments document type. (Useful as a minutes mirror; irrelevant for written comments.)

  **Verdict: PUBLISHED — minutes/agendas only. No written comments.**

---

## COVID-era exception (why it is NOT broken into the clean CSV)

During the 2020 **electronic** meetings, the City Recorder occasionally read a resident's
**written/emailed** submission **verbatim** into the public-hearing record. An exhaustive
scan of every 2020–2021 Regular-meeting minutes file found **exactly 2** such verbatim
written submissions:

1. **2020-07-13** — "Nichole Camac, City Recorder, **read the following comments submitted
   by Monica Dixon**: '… we do not want the zoning to change at 1580 W. Whitlock Ave. …'"
   (Chesterfield neighborhood, full quote in the minutes).
2. **2020-07-27** — "Nichole Camac, City Recorder, **read a statement from Fattima Ahmed**
   with UCA as follows: …" (Utah Community Action, CDBG public hearing).

These are genuine resident-written text. **But:**
- They are **not published as a separate written-comment dataset** — they exist *only* as
  quotes embedded inside two minutes PDFs, indistinguishable in delivery from the in-person
  paraphrases around them.
- They are **n = 2** out of ~222 Regular meetings — not a dataset, an anecdote.
- Pulling exactly 2 rows into `all_comments_clean.csv` and calling it "the WVC written
  public-comments dataset" would badly **misrepresent the source** (it would imply WVC
  publishes written comments). The honest representation is: WVC does **not** publish written
  comments; these two verbatim reads are noted here in `AVAILABILITY.md` and remain in the
  minutes text. They are therefore documented but **not** extracted as the clean dataset.

(Also seen, but correctly excluded as *not* city-collected written submissions: residents/
councilmembers reading a letter from a community organization **during in-person comment** —
e.g. 2022-11-21, 2023-02-06, 2024-09-16. These are in-person testimony, already in the
speaker log, not written submissions to the city.)

Public hearings sometimes invite written comment by a deadline (e.g. the CDBG/CAPER hearing
2025-10-13: "citizens' comments may be submitted in writing until 5:00 p.m. …"), but in
every instance checked the minutes record **"No comments were received."**

---

## Final dispositions

| Avenue | URL | Verdict |
|---|---|---|
| OnBase document types | `ob.wvc-ut.gov/OnBaseAgendaOnline/Meetings/Search` | PUBLISHED — Agenda + Minutes only; no comment doctype |
| Agenda packets | `…/Documents/DownloadFileBytes/Regular_Meeting_<id>_Agenda_<date>.pdf` | IN-PACKETS = NO (outline only) |
| City Council page | `wvc-ut.gov/15/City-Council` | SUBMIT-ONLY (in-person), NOT-PUBLISHED |
| `/PublicComment` shortcut | `wvc-ut.gov/PublicComment` | DEAD (404, never archived) — was live-participation, not an archive |
| View-Online | `wvc-ut.gov/837/View-Online` | Livestream redirect only |
| eComment / Speak-Up / OpenGov / Granicus | — | DOES NOT EXIST (no portal ever found) |
| GRAMA / Records portal | `wvc-ut.gov/260/...`, `/135/Records-Division` | SUBMIT-ONLY (records *request*); not a comment archive |
| Government Transparency | `wvc-ut.gov/1033/Government-Transparency` | Financial only; no comment archive |
| Utah PMN (body 398) | `utah.gov/pmn/sitemap/publicbody/398.html` | Minutes/agendas only |
| COVID verbatim reads in minutes | 2020-07-13, 2020-07-27 minutes | GENUINE but n=2, embedded-in-minutes-only → documented here, not extracted |

**Bottom line:** No genuine written/online public-comment dataset is published by West
Valley City. `all_comments_clean.csv` stays empty (header only). The in-person speaker
paraphrases are preserved separately and labeled in `minutes_speaker_log.csv`.
