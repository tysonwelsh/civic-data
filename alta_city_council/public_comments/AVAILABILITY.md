# Public comments — Town of Alta — HONEST ZERO (submit-only)

**Verdict: SUBMIT-ONLY / no published written-comment archive.** Alta publishes **no**
standalone public-comment corpus (no eComment archive, no correspondence page, no
downloadable comment log). `all_comments_clean.csv` is therefore **header-only by design**
— this is a legitimate honest zero, not a data gap. (Matches Taylorsville / South Jordan.)

## Audit (browser-UA, 2026-07-11)
| Probe | Result |
|---|---|
| `https://townofalta.utah.gov/public-comment/` | **404** |
| `https://townofalta.utah.gov/public-comments/` | **404** |
| `https://townofalta.utah.gov/comment/` | **404** |
| `https://townofalta.utah.gov/public-comment-form` | **301 → external form host** (heygov) |
| `/meetings/` page comment affordance | a single **"PUBLIC COMMENT FORM"** dropdown link → the submit form above |

The only public-comment affordance on the town site is a **submit form** (a resident fills it
in to have a comment read / to sign up to speak). It writes to an external form provider and
exposes **no archive of prior submissions**. There is no page, feed, or document that lists
past written comments.

## How comment actually enters the record
Public comment at Alta is taken **in person at meetings** (the town also streams meetings on
YouTube / posts audio to SoundCloud) and is **paraphrased inline in the meeting minutes** by
the clerk (e.g. the 2026-06-17 minutes transcribe speakers such as Mark Haik, Margaret Bourke,
and an Alta Ski Area representative). Those are **meeting-record speaker notes, not genuine
standalone written comments**, and they live in `meeting_minutes/` — not here. Do **not**
re-mine minutes speaker paraphrase into this file; it would misrepresent clerk summary as
verbatim public comment.

## If this ever changes
If Alta stands up an eComment portal or publishes a written-comment archive, harvest it into
`all_comments_clean.csv` using the collection-standard 14-column schema (header already in
place) and update this file. Until then the honest-zero verdict stands.
