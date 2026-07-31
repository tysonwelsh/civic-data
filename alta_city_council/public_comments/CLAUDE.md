# public_comments/ — Town of Alta — HONEST ZERO (submit-only)

Alta publishes **no** standalone written-comment archive (no eComment archive, no
correspondence page, no downloadable comment log). `all_comments_clean.csv` is therefore
**header-only by design** — a legitimate honest zero, not a data gap. Full audit + probe
table (browser-UA, 2026-07-11) in **`AVAILABILITY.md`** — read it before making any claim
about Alta public comment.

## What's here
- `AVAILABILITY.md` — the SUBMIT-ONLY verdict + the URL probes behind it (the town's only
  comment affordance is a submit form on an external host `heygov`; `/public-comment/` 404s).
- `all_comments_clean.csv` — the collection-standard 14-column header, **0 data rows**.
- `raw/` — retained originals (none; nothing to retain for an honest zero).

## How comment actually enters the record (do NOT re-mine it here)
Public comment at Alta is taken **in person at meetings** (also streamed on YouTube / posted to
SoundCloud) and **paraphrased inline in the meeting minutes** by the clerk (e.g. the 2026-06-17
minutes transcribe speakers such as Mark Haik and Margaret Bourke). Those are **meeting-record
speaker notes, not genuine standalone written comments** — they live in `meeting_minutes/`, not
here. Do **not** re-mine minutes speaker paraphrase into `all_comments_clean.csv`; it would
misrepresent clerk summary as verbatim public comment. This matches Taylorsville / South Jordan /
Riverton.

## If this ever changes
If Alta stands up an eComment portal or publishes a written-comment archive, harvest it into
`all_comments_clean.csv` using the 14-column schema (header already in place) and update
`AVAILABILITY.md`. Until then the honest-zero verdict stands and `coverage.json` correctly shows
0 comments for Alta.
