# Public comments — availability (Magna City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**

Magna City takes public comment **in person at the meeting only**: persons wishing to speak on
an item not on the public-hearing agenda **sign up on the "Public Comment" form at the meeting
entrance** and are called in sign-in order, **limited to 2 minutes each** (printed verbatim on
every agenda). A **QR code at the front entrance** lets residents send questions to city staff
during the meeting. The city publishes **no** archive of any written/emailed comments: no
dedicated comments page, no eComment / Open City Hall / Speak-Up / Peak Democracy portal, no
"correspondence received" folder, and no correspondence section inside the agendas/minutes. The
only public record of a comment is the **clerk's paraphrase of in-person speakers written into
the meeting minutes** — a speaker log, which is meeting-record notes, **NOT** public-submitted
written comments, so it does not populate `all_comments_clean.csv`.

**`all_comments_clean.csv` is HEADER-ONLY** (the 14-column collection-standard header, mirroring
South Jordan). This is an **honest empty result**, not a gap to be filled — Magna joins the 6
honest-zero comment cities (substantive published comments exist only in SLC + Park City).

## Avenues checked (comments-auditor hunt order, browser-UA GET, 2026-07-12)

1. **Dedicated published-comments page / archive** — **none.** The City Council page
   (`https://magna.utah.gov/171/City-Council`) and the CivicPlus homepage carry meeting info,
   contacts, and the Agenda Center, but **no** public-comment submission form, comment archive,
   or "correspondence received" link. Keyword scan of those pages for
   `ecomment|open city hall|public comment|correspondence|written comment|comment card` returned
   **zero** hits.

2. **eComment / Open City Hall / Speak-Up / Peak Democracy portal** — **none found.** Web search
   (Magna + each portal brand, 2026-07-12) surfaced only the CivicPlus site, the community
   (non-official) `magnautah.org`, and the Utah PMN agenda PDFs — **no** online-comment
   submission or export feed. The agendas describe only the in-person sign-up form + a QR code to
   ask staff questions — not a published-comment channel.

3. **Inside the minutes** — in-person speakers are recorded, but as clerk paraphrase (a speaker
   log, not submitted comments). The recon-verified 2026-05-26 council minutes carry a standing
   **"PUBLIC COMMENTS (Limited to 2 minutes per person)"** item, e.g. *"no individuals had signed
   up for public comment."* When present, these are the clerk's meeting-record notes → belong in
   a `minutes_speaker_log.csv` (built by the minutes pipeline, labeled NOT comments), never
   merged into `all_comments_clean.csv`.

4. **Agendas/minutes ("correspondence / written comments received")** — **none bundled.** The
   Magna agendas (PMN body 5803, `www.utah.gov/pmn/files/<id>.pdf`) and born-digital minutes are
   agenda + staff-item + minutes documents; no forwarded resident emails (`From:/Sent:/Subject:`
   blocks), no "Dear Council" letters, no petitions/comment cards, and no "the following
   correspondence was received" section.

5. **Records / transparency / correspondence archive** — none surfaced. PMN posts a **meeting
   audio MP3** per meeting (comment is **spoken, not archived as text**). Emailed comments, if
   any, would be retrievable only by a GRAMA records request (out of scope; GET-only,
   non-fabricating).

## How comments are submitted (summary)
- **In person** at the meeting (Webster Center, 8952 W Magna Main St; 2nd & 4th Tuesday, 6:00 PM):
  sign the **Public Comment form at the entrance**, 2-minute limit, called in sign-in order.
- **QR code** at the entrance to send questions to city staff during the meeting.
- **No** online comment portal; **no** published archive of any written/emailed comments.

## Sources checked (all browser-UA GET, 2026-07-12)
| Avenue | URL | Result |
|---|---|---|
| City Council page | https://magna.utah.gov/171/City-Council | HTTP 200; no comment form/archive; contacts only |
| CivicPlus Agenda Center | https://magna.utah.gov/AgendaCenter | HTTP 200; agendas/minutes only, no comment doc type |
| Elections page | https://magna.utah.gov/161/Elections | HTTP 200; no comment portal |
| Homepage nav | https://magna.utah.gov/ | HTTP 200; nav has "Contact" only — no eComment/Open City Hall |
| Council agenda (comment rule) | https://www.utah.gov/pmn/files/1408825.pdf | In-person "Public Comment" sign-up form at entrance, 2-min limit; QR code to staff |
| PMN — Magna Council (body 5803) | https://www.utah.gov/pmn/sitemap/publicbody/5803.html | Agenda + audio MP3 per meeting; no written-comment archive |
| Portal search (eComment/Open City Hall/Speak-Up/Peak Democracy) | web search | None exist for Magna |

```json
{"verdict":"SUBMIT-ONLY / NOT PUBLISHED","csv":"header-only","locations":[],"notes":"Public comment is IN-PERSON ONLY: sign the Public Comment form at the meeting entrance (2-min limit, called in sign-in order); a QR code at the entrance sends questions to staff. City publishes NO archive of written/emailed comments: no comments page, no eComment/Open City Hall/Speak-Up portal, no correspondence document type in agendas/minutes. PMN posts a meeting audio MP3 (comment is spoken, not archived as text). The only textual record is the clerk's paraphrase of in-person speakers in the minutes = a minutes_speaker_log (meeting-record notes), NOT the comments dataset. all_comments_clean.csv is header-only; honest empty result (joins the 6 honest-zero comment cities)."}
```
