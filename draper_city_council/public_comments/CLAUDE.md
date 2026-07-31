# public_comments/ — Draper City (HONEST-EMPTY, submit-only)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED — this is a legitimate honest zero, not a gap.**

Draper accepts public comment (1) **in person** at Council/PC meetings (3-min limit), (2) by **email
to `public.comment@draper.ut.us`** by 5:00 p.m. on the meeting day, and (3) by **written comment to
the City Recorder** before noon the day prior. The city publishes **no archive** of those
emailed/written comments — no dedicated comments page, no eComment / Open City Hall / Speak-Up
portal, no "correspondence received" folder, and no comment document type in the Granicus meeting
portal. The only public record of a comment is the **clerk's third-person paraphrase of in-person
speakers inside the minutes** — a *speaker log* (meeting-record notes), which is **NOT
public-submitted written comment** and therefore does **not** populate `all_comments_clean.csv`.

## Files
- `AVAILABILITY.md` — the full audit (avenues checked, browser-UA, 2026-07-11): city CMS, eComment
  portals, Granicus portal, agenda packets, and inside-the-minutes speaker paraphrase. **Read this
  before assuming any comment data exists.**
- `all_comments_clean.csv` — **header-only** (14-column standard schema, copied from South Jordan).
  Deliberately unpopulated. This is the honest-empty result, matching the collection's "6 honest
  zeros" pattern (substantive published written comments exist only in SLC + Park City).
- `raw/` — retained artifacts from the availability hunt (if any).

## Do NOT
- Do **not** harvest the clerk's inline speaker paraphrase into `all_comments_clean.csv` — it is a
  meeting-record speaker log, not submitted comment. (If ever wanted, it would go into a separately
  labelled `minutes_speaker_log.csv`, explicitly *not* the comments table — deferred, not built.)
- Do **not** treat the header-only CSV as a build failure. The only routes to real comment text are a
  **GRAMA request** for the `public.comment@draper.ut.us` mailbox or **transcribing meeting video** —
  neither is a published dataset today.
