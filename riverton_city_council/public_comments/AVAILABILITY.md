# Public comments — availability (Riverton City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**

Riverton City accepts public comment three ways — (1) **in person** at the Council or
Planning Commission meeting (Council: 15 minutes total, 3 minutes/speaker; PC comment
restricted to public-hearing items), (2) **eComment** submitted online through the Granicus
meeting portal (a live per-agenda submission button, `ecomment.buttons.js`), or (3)
**written comment emailed in advance** to the City Recorder at **`recorder@rivertonutah.gov`**
(per the city's `meetings/public-comment.php` guidance). The city publishes **no** archive
of eComment or emailed written comments: no dedicated comments page, no downloadable
comment/correspondence document type on the Granicus publisher, and no "correspondence
received" section in the agenda packets. The **only** public record of a comment is the
**recorder's third-person paraphrase of in-person speakers written into the meeting
minutes** — a speaker log, which per the collection's extraction standard is
**meeting-record notes, NOT public-submitted written comments**, so it does not populate
`all_comments_clean.csv`.

**`all_comments_clean.csv` is header-only** (no genuine published written-comment corpus
exists). This is an honest empty result, not a gap to be filled.

## Avenues checked (browser-UA audit, 2026-07-11)

1. **Dedicated published-comments page / archive** — **none.** The City Meetings landing
   (`https://www.rivertonutah.gov/meetings/index.php`) and the Public-Comment-Procedure page
   (`https://www.rivertonutah.gov/meetings/public-comment.php`, a JS-rendered Revize page)
   describe *how* to comment but expose no comment archive, no "correspondence received"
   link, and no downloadable submissions. No SLC-style weekly comment PDFs.

2. **eComment / online submission portal** — **exists as a SUBMISSION channel only, not an
   archive.** The Granicus publisher (`rivertoncity.granicus.com/ViewPublisher.php?view_id=1`)
   carries the **eComment** feature (`js/ecomment.buttons.js`, "eComment" buttons per
   agenda). eComment collects comments live against a specific agenda during the open
   window; Granicus does **not** publish them back as a downloadable archive or a
   comment/correspondence document type (the publisher lists Agenda / Minutes / Video only —
   grep for `comment`/`correspondence`/`written` document links returned none).

3. **Inside the minutes** — **in-person speakers are transcribed inline, but as recorder
   paraphrase (a speaker log, not submitted comments).** Both bodies do this systematically:
   - **Council** (`2025-12-16` minutes, PMN `1380299.pdf`): a **"Citizen Comment"** section —
     *"Mayor Staggs called for public comments; Jason Richman spoke in opposition to closing
     the skate park, citing personal experience …"* — named speakers, third-person
     near-verbatim paraphrase, then *"there being none, he closed the Citizen Comment
     period."*
   - **Planning Commission** (`2026-06-11` minutes, PMN `1455569.pdf`): public hearings
     record *"Chair Park opened the public hearing. There were no comments…"* or paraphrase
     those who spoke — *"Lacy Uhl gave her address as 12418 South Redwood Road and stated
     that…"*.
   **Fidelity: named speakers + rich paraphrase, third-person, not the citizen's own
   submitted text.** No emailed/eComment submissions are reproduced or listed anywhere in the
   minutes. → This is `minutes_speaker_log.csv` material (a labeled speaker log built by the
   minutes pipeline, explicitly NOT merged into `all_comments_clean.csv`).

4. **Agenda packets ("correspondence / written comments received")** — **none surfaced.**
   Riverton distributes agendas/minutes/video through Granicus + the Utah PMN mirror; no
   packet document type carries a forwarded-email/correspondence section (unlike West Jordan,
   which forwards resident emails into its PrimeGov packet).

5. **Records / transparency archive** — none. Emailed/eComment submissions would be
   retrievable only by a GRAMA records request (out of scope; GET-only, non-fabricating).

## What the minutes DO carry (for downstream, labeled correctly)
In-meeting Public-Comment / public-hearing speakers are named + paraphrased in both the
Council and PC minutes. When the minutes corpus is extracted to markdown, that material
belongs in a labeled **`minutes_speaker_log.csv`** (meeting-record notes), explicitly **not**
merged into `all_comments_clean.csv`. The minutes-markdown layer for Riverton is now fully
extracted (128 council + 119 PC docs), but a labeled `minutes_speaker_log.csv` was **not**
built — it remains an optional, deferred artifact; finding only this inline speaker material is
**not** "PUBLISHED," so `all_comments_clean.csv` stays header-only.

## How comments are submitted (summary)
- **In person** at the meeting (Riverton City Hall, 12830 S 1700 W): Council 15 min total /
  3 min per speaker; PC comment restricted to public-hearing items.
- **eComment** online via the Granicus meeting portal (live per-agenda button).
- **Written, in advance:** email the City Recorder `recorder@rivertonutah.gov`.
- No published archive of the eComment or emailed comments.

## Sources checked (all GET-only, browser UA, 2026-07-11)
| Avenue | URL | Result |
|---|---|---|
| City Meetings landing | https://www.rivertonutah.gov/meetings/index.php | Schedule/links only; no comment archive |
| Public-comment procedure | https://www.rivertonutah.gov/meetings/public-comment.php | Describes how to comment (in-person/eComment/email); no archive |
| Granicus publisher | https://rivertoncity.granicus.com/ViewPublisher.php?view_id=1 | eComment SUBMISSION button present; NO comment/correspondence doc type or archive |
| Council minutes sample | https://www.utah.gov/pmn/files/1380299.pdf | Named in-person speakers, third-person paraphrase (speaker log) |
| PC minutes sample | https://www.utah.gov/pmn/files/1455569.pdf | Public-hearing speakers named + paraphrased (speaker log) |

```json
{"verdict":"SUBMIT-ONLY / NOT PUBLISHED","locations":[],"notes":"Riverton takes comment three ways: in person (Council 3 min/speaker, 15 min total; PC public-hearing items only), eComment via the Granicus meeting portal (a live per-agenda SUBMISSION button, js/ecomment.buttons.js), and written email to the City Recorder (recorder@rivertonutah.gov). The city publishes NO archive of eComment or emailed comments: no comments page, no downloadable comment/correspondence document type on Granicus, no correspondence section in packets. The only public record of comment is the recorder's named, third-person near-verbatim paraphrase of in-person / public-hearing speakers inside the Council and PC minutes = a minutes_speaker_log (meeting-record notes), NOT the comments dataset. all_comments_clean.csv is header-only; honest empty result. Inline speaker paraphrase is systematic in both bodies; a labeled minutes_speaker_log.csv is deferred to the minutes-markdown pipeline (not yet extracted for Riverton)."}
```
