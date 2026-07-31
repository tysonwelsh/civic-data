# Public comments — availability (Taylorsville City)

**Audit date:** 2026-07-06 · **Auditor pass:** comments-availability (GET-only, browser
UA via `polite_fetch.py`; no fabrication).

**VERDICT: `SUBMIT-ONLY / NOT PUBLISHED`.**

Taylorsville City takes public comment **in person at the meeting** (via a
**"Citizen/Public Hearing Comment Form"** handed to the City Recorder or Council
Coordinator before speaking) and — for specific federally-mandated processes (HUD/CDBG) —
during a formal **written-comment period**. The city publishes **no standalone archive of
written/online public comments**: there is **no dedicated comments/correspondence page, no
eComment / Open City Hall / Speak-Up portal, and no "correspondence received" document
category**, and the meeting **packets do not bundle written correspondence**. The **only**
public record of a comment is the **clerk's third-person paraphrase of in-person speakers
inside the meeting minutes** — a speaker log, which per `extraction_standards.md` is
meeting-record notes, **NOT** public-submitted written comments, so it does **not**
populate `all_comments_clean.csv`.

**No `all_comments_clean.csv` was built** — no genuine published written/online-comment
corpus exists. This is an honest empty result, not a gap to fill.

---

## The bar (what counts)
`all_comments_clean.csv` may hold ONLY **genuine public-submitted written/online comments**
— text a resident actually wrote and submitted (letter / email / form) that the city
published verbatim. **Clerk third-person paraphrases of in-person speakers in the minutes
do NOT count** (they are a `minutes_speaker_log`). This audit applies that bar.

---

## Avenues checked (item-by-item, all GET-only 2026-07-06)

### 1. Dedicated comment / correspondence page or document category — NONE
- The CivicEngage Central site (`www.taylorsvilleut.gov`, 403s bare bots — fetched with a
  browser UA) has **no public-comment page, no "Correspondence / Communications Received"
  document category, and no comment archive**. The Council agendas-&-minutes landing
  (`/government/elected-officials/city-council-agendas-minutes`) exposes only three
  columns — **Agendas / Minutes / Audio Recordings** — no comment/correspondence column.
- The one comment artifact on the Council landing page is a button linking to a blank
  **"CITY COUNCIL COMMENT FORM"** (`/home/showpublisheddocument/4187`) — a **submission
  form**, not an archive (see §6).
- **False positive noted:** the token "eComment" appears in the page source only as the
  CivicEngage CSS class `reComment` (`$(".reComment[comment]")…`), **not** an eComment
  product. No eComment feature is present.

### 2. Inside the minutes — inline clerk SPEAKER LOG, not comments
Minutes are born-digital clean text. The **"Citizen Comments"** section and each
**Public Hearing** transcribe in-person speakers as **named, third-person clerk
paraphrase** — rich but **not the citizen's own submitted text**. When no one speaks the
minutes say so.
- `2025-09-03` (PMN `1321911.pdf`): *"The Chair opened the time for citizen comments.
  However, there was no one who expressed a desire to speak, so she closed the citizen
  comment period."*
- `2026-06-03` draft (PMN `1448701.pdf`): three named speakers paraphrased in the third
  person, e.g. *"The first speaker, Alexis Wilden, addressed the council regarding
  concerns about the use of fireworks during Taylorsville Dayzz. She noted that large
  fireworks displays could be harmful to veterans…"*; *"The second speaker, Shane
  Manwaring, introduced himself as a Bluffdale resident and candidate for Salt Lake County
  Sheriff…"*
- **Fidelity:** named speaker + detailed third-person paraphrase; **not verbatim**, not
  the resident's submitted text. → This is `minutes_speaker_log.csv` material (built by the
  minutes pipeline, labeled NOT comments), never `all_comments_clean.csv`.

### 3. Agenda packets — checked; NO correspondence bundled
Taylorsville "packets" are **not** Millcreek/Provo-style single mega-PDFs with appended
resident letters. Both the on-portal packet pages and the PMN per-meeting attachment sets
were checked:
- **Portal packet pages** (`/government/elected-officials/council-packet`,
  `/government/planning-commission/planning-commission-packet`): the archive is
  JS-rendered; the featured/current documents retrieved are **1–2 page image-only scans**
  (e.g. doc `12091` = *"July 1, 2026 City Council Cancellation"*) — agenda/notice covers,
  no correspondence.
- **PMN body 720** (`utah.gov/pmn/sitemap/publicbody/720.html`) lists every meeting's
  attachments **as separate item PDFs**: Agenda, Minutes, and per-item staff documents
  (`Item 6.1 - Resolution No. 26-18.pdf`, `Property Tax Impact Schedule.pdf`, budget PDFs,
  etc.). Across the 10 most-recent meetings there is **no** document titled
  comment / correspondence / letter / citizen / petition (the only "Email" strings are the
  site's subscribe widget). → **Packets carry staff/legislative items, not written public
  correspondence.**

### 4. eComment / Open City Hall / Speak-Up / portal feature — NONE
Web search (2026-07-06) for Taylorsville + each portal brand surfaced only the CivicEngage
site and PMN — **no online-comment submission or export feed**. Comment is taken in person
via the citizen comment form (confirmed on the agenda boilerplate and the form itself).

### 5. Records / transparency / GRAMA — no comment archive
The site has a **Records Request (GRAMA)** page (`/government/records-requests`) but **no
open-data portal or "council correspondence" archive**. Submitted written comments would
be retrievable only by a records request (out of scope; GET-only, non-fabricating).

### 6. Submission mechanism — in-person form to the City Recorder (SUBMIT-ONLY)
The blank **"City of Taylorsville — Citizen/Public Hearing Comment Form"**
(`/home/showpublisheddocument/4187`) states: *"Anyone desiring to address the Council at
the Citizen Comment portion… must complete a 'Citizen Comment' form and submit it to the
City Recorder or Council Coordinator before addressing the Council"* (≈2 min per
individual / 5 min per group representative), and *"In lieu of, or in addition to verbal
comments, citizens may submit written comments."* These forms/written submissions go to the
**City Recorder** and are **not published**.

---

## Nuance — federally-mandated CDBG written-comment period (still inside minutes only)
For the annual **HUD / CDBG** action plan, the city runs a formal **written public-comment
period** and *receives* written comments — but they surface only as a **clerk summary
inside the minutes**, never as a published citizen-text corpus. Per the `2026-05-20` draft
minutes (PMN `1441569.pdf`): *"a written public comment period had been open from April 12
through May 12, 2026. One written public comment was received from an individual associated
with the organization Upwards… Four additional public comments had been received at the
April 1 hearing and had been included in the minutes from that meeting."* This is a
narrow federal-process exception and is **clerk-summarized in the minutes**, not a standalone
published corpus — it does not change the verdict.

## What the minutes DO carry (for downstream, labeled correctly)
In-person Citizen Comment / public-hearing speakers are named and paraphrased in the
minutes. When the minutes are extracted, that belongs in a **`minutes_speaker_log.csv`**
(meeting-record notes), explicitly **not** merged into `all_comments_clean.csv`. Finding
only this is **not** "PUBLISHED."

## How comments are submitted (summary)
- **In person** at the meeting (Council Chambers, Room 140, 2600 W Taylorsville Blvd),
  via a **Citizen Comment Form** to the City Recorder / Council Coordinator; ~2 min per
  individual, 5 min per group representative.
- **Written comments** accepted *in lieu of / in addition to* verbal, submitted to the
  City Recorder (and, for CDBG, during a posted written-comment window). **Not published.**
- **No** online comment portal; **no** published archive of written/emailed comments.

## Sources checked (all GET-only, 2026-07-06)
| Avenue | URL | Result |
|---|---|---|
| Council agendas & minutes landing | https://www.taylorsvilleut.gov/government/elected-officials/city-council-agendas-minutes | Agendas/Minutes/Audio only; no comment column |
| Citizen Comment Form (submission) | https://www.taylorsvilleut.gov/home/showpublisheddocument/4187 | Blank in-person form → City Recorder; "may submit written comments" |
| Council packet page | https://www.taylorsvilleut.gov/government/elected-officials/council-packet | JS archive; featured doc = 1-pg cancellation notice; no correspondence |
| PC packet page | https://www.taylorsvilleut.gov/government/planning-commission/planning-commission-packet | Featured docs = 1–2 pg image scans; no correspondence |
| PMN council body (attachment types) | https://www.utah.gov/pmn/sitemap/publicbody/720.html | Per-meeting Agenda/Minutes/staff-item PDFs; NO comment/correspondence doc type (10 meetings) |
| Council minutes (no speakers) | https://www.utah.gov/pmn/files/1321911.pdf (2025-09-03) | "no one… desire to speak" |
| Council minutes (named speakers) | https://www.utah.gov/pmn/files/1448701.pdf (2026-06-03 draft) | 3 named speakers, third-person paraphrase (speaker log) |
| Council minutes (CDBG written-comment note) | https://www.utah.gov/pmn/files/1441569.pdf (2026-05-20 draft) | Written comments received → summarized in minutes only |
| Records Request (GRAMA) | https://www.taylorsvilleut.gov/government/records-requests | No comment archive; request-only |
| Portal search (eComment/Open City Hall/Speak-Up) | web search 2026-07-06 | None exist for Taylorsville |

```json
{"verdict":"SUBMIT-ONLY / NOT PUBLISHED","locations":[],"packets_carry_comments":false,"minutes_carry_comments":"inline clerk third-person paraphrase of named in-person speakers = minutes_speaker_log, NOT genuine written comments","submit_how":"in-person Citizen Comment Form to City Recorder/Council Coordinator (~2 min individual / 5 min group); written comments accepted in lieu of/in addition to verbal, submitted to City Recorder; formal written-comment period only for HUD/CDBG (clerk-summarized in minutes). No online portal.","artifact_written":"AVAILABILITY.md (no all_comments_clean.csv built — honest empty)","checked":["CivicEngage council agendas/minutes landing (no comment/correspondence category or column)","blank Citizen Comment Form doc 4187 (submission only)","council + PC packet pages (JS archive; featured docs are 1-2pg image agenda/notice scans, no correspondence)","PMN body 720 per-meeting attachment sets across 10 meetings (Agenda/Minutes/staff-item PDFs only; no comment/correspondence doc type)","3 council minutes incl. named-speaker + CDBG written-comment cases (inline paraphrase / clerk summary only)","Records Request GRAMA page","web search for eComment/Open City Hall/Speak-Up (none)"],"notes":"eComment token in page source is the CivicEngage CSS class 'reComment', not an eComment product. CDBG federal process has a written-comment window whose received comments are summarized inside the minutes only — not a standalone published corpus."}
```
