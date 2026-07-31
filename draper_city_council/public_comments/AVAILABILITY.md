# Public comments — availability (Draper City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**

Draper City accepts public comment three ways — (1) **in person** at the Council (or PC)
meeting, **3-minute limit** per person, restricted to items **not** on the agenda; (2)
**email to `public.comment@draper.ut.us` by 5:00 p.m. on the day of the meeting** ("will
become part of the public record"); or (3) **written comment to the City Recorder**
(Nicole Smedley) **before noon the day before the meeting** for agenda items that can't be
covered in 3 minutes. The city publishes **no archive of those emailed/written comments**:
no dedicated comments page, no eComment / Open City Hall / Speak-Up portal, no
"correspondence received" folder, and no correspondence document type in the Granicus
meeting portal. The **only** public record of a comment is the **clerk's third-person
paraphrase of in-person speakers written into the meeting minutes** — a *speaker log*
(meeting-record notes, often with the speaker's name/address), which is **NOT
public-submitted written comment** and therefore does **not** populate
`all_comments_clean.csv`.

**No populated `all_comments_clean.csv` was built** — the file is **header-only** (14-column
standard schema, copied from South Jordan). This is an **honest empty result**, not a gap
to be filled. It matches the collection's "6 honest zeros" pattern (substantive published
written comments exist only in SLC + Park City).

## Avenues checked (comments-auditor hunt order, browser UA, 2026-07-11)

1. **Dedicated published-comments page / archive on the city site** — **none.** The
   custom Draper CMS (`https://www.draperutah.gov/`) and the Mayor-and-Council / Agendas-
   and-Minutes pages carry meeting times, agendas, minutes, video, and member contacts, but
   **no public-comment submission form, no comment archive, and no "correspondence
   received" link** (`.../city-government/mayor-and-council/agendas-and-minutes/` fetched;
   no comment portal present).

2. **eComment / Open City Hall / Speak-Up portal** — **none found.** Web search
   (2026-07-11) for Draper + each portal brand surfaced only the city CMS and the Granicus
   meeting portal. The published comment channel is a plain **email address**
   (`public.comment@draper.ut.us`) — a mailbox, not a published feed.

3. **Granicus meeting portal** (`draper.granicus.com/ViewPublisher.php?view_id=1`) —
   exposes only **Agenda / Minutes / Recap / Video / MP4 / Agenda-Packet** per meeting.
   **No "eComment" tab and no "comment"/"correspondence" document type.** (Granicus
   eComment is a paid add-on Draper has not enabled.)

4. **Agenda packets** — the Granicus Agenda-Packet download bundles the agenda + staff
   reports/exhibits; **no separate "correspondence received" or public-comment section
   surfaced.** Emailed comments enter the record via the clerk but are not published as a
   packet document.

5. **Inside the minutes** — **in-person speakers ARE transcribed inline, but as clerk
   paraphrase (a speaker log, not submitted comments).** **135 of 151** council minutes
   carry a **"Public Comments"** agenda item; speakers appear in third person with a
   `resident` tag and (often) an address — e.g. *"Todd Shoemaker, resident, stated that
   he spoke to the Point of the Mountain State Land Authority board…"*; many meetings
   record *"There were no public comments."* Two 2020 (COVID-era, remote) minutes note
   that *written comments were submitted/emailed*, but the written text itself is **not
   published** anywhere. A grep of all minutes for `correspondence received` / `eComment` /
   `letters received` / `comment card` returned **nothing**.

## If a genuine comment corpus is ever wanted

The only routes to real comment text would be (a) a **GRAMA records request** for the
`public.comment@draper.ut.us` mailbox, or (b) **transcribing the spoken comments** from the
Granicus meeting video. Neither is a published dataset today. The inline speaker paraphrase
could alternatively be harvested into a labelled **`minutes_speaker_log.csv`** (a
meeting-record artifact, explicitly *not* `all_comments_clean.csv`) — deferred; not built
in this pass.
