# Public comments — availability (White City)

**Verdict: SUBMIT-ONLY / IN-MEETING — NOT PUBLISHED.**

White City takes public comment **in person at the meeting** (a standing "PUBLIC COMMENTS"
agenda item). The city publishes **no** archive of written/submitted comments: no dedicated
public-comment page, no eComment / Open City Hall / Speak-Up portal, and no
"correspondence received" document category on the Streamline site. The **only** public
record of a comment is the **clerk's paraphrase of in-person speakers written into the
meeting minutes** — a speaker log, which is meeting-record notes, **NOT** public-submitted
written comments. It therefore does **not** populate `all_comments_clean.csv`.

**`all_comments_clean.csv` is header-only** (the sibling-standard 14-column schema, zero
data rows). This is an **honest empty result**, not a gap to be filled.

## Avenues checked (browser-UA, GET-only, 2026-07-12)

1. **Dedicated published-comments page / archive — none.** Probed the Streamline site for
   comment endpoints: `/public-comment`, `/public-comments`, `/comment`, `/contact` all
   return **404**; only `/contact-us` (200) exists — a staff contact page, not a comment
   form or archive. No SLC-style weekly comment PDFs, no St. George-style comment feed.

2. **eComment / Open City Hall / Speak-Up / Peak Democracy portal — none found.** The
   `whitecity.utah.gov` homepage (Streamline SPA) surfaces only template `form`/`contact`
   artifacts; no online-comment submission or export feed is present or linked, and none
   surfaced for "White City" + each portal brand.

3. **Inside the minutes — in-person speakers are paraphrased inline** (clerk third-person
   paraphrase under the "PUBLIC COMMENTS" agenda item; e.g. the 2023-06-01 resident
   complaint about park parking noted in `recon.md`). **This is a `minutes_speaker_log`,
   not submitted written comments** → never merged into `all_comments_clean.csv`.

4. **Agenda packets — no correspondence container.** White City's per-meeting docs are
   Agenda + Packet + Minutes + audio MP3 (Cloudfront `/files/<hash>/`); no forwarded-email
   / "correspondence received" section is bundled (consistent with the submit-only form).

5. **Streamline SPA note.** The site renders content client-side, so page HTML is template
   CSS/JS; the verdict rests on the actual **minutes** (read during recon), which carry the
   in-meeting speaker log and no reproduced written comments.

## How comments are submitted (summary)
- **In person** at the meeting (White City Water Improvement District building, 999 E
  Galena Dr — the rented meeting venue), under the "PUBLIC COMMENTS" agenda item.
- No online comment portal; no published archive of any written/emailed comments.

```json
{"verdict":"SUBMIT-ONLY / IN-MEETING — NOT PUBLISHED","locations":[],"csv":"header-only","notes":"White City (Streamline CMS, whitecity.utah.gov) takes public comment in person at the meeting (standing PUBLIC COMMENTS agenda item). No published written-comment archive: /public-comment /public-comments /comment /contact all 404 (only /contact-us 200, a staff contact page); no eComment/Open City Hall/Speak-Up portal; no correspondence document category; per-meeting docs are Agenda+Packet+Minutes+audio MP3 with no forwarded-email section. The only public record of comment is the clerk's third-person paraphrase of in-person speakers inside the minutes = a minutes_speaker_log (meeting-record notes), NOT submitted written comments. all_comments_clean.csv is header-only; honest empty result."}
```
