# Public comments — Emigration Canyon (HONEST-EMPTY / submit-only)

**Verdict: NO published written-comment corpus. `all_comments_clean.csv` is header-only
(an honest zero), not a gap to backfill.** As-of 2026-07-12.

## What was checked (browser UA)
- **Official city site** (`https://emigration.utah.gov/`): **no eComment portal, no
  "submit a comment" form, no correspondence archive.** Public engagement is **in-person
  (or Zoom)** at the monthly council meeting, plus **email/phone** (`emigrationcanyon@utah.gov`,
  main line (385) 240-1400). Verified 2026-07-12.
- **Utah Public Notice (PMN), council body 5809 / PC body 1562** — the canonical document
  source (no city CMS). Meeting notices carry Agenda, Approved Minutes, Supporting Docs, and
  audio (.MP3). There is **no separate written-comment / correspondence dataset**.
- **Minutes** carry a **`PUBLIC COMMENTS`** section that **paraphrases in-person speakers**
  (e.g., 2026-05-19: resident Willie Stockman on the watershed plan / green-waste dumpsters).
  Per collection standards these are **meeting-record speaker notes, NOT genuine written
  public comments** — they belong to the minutes/votes layer, and are **not** promoted into
  `all_comments_clean.csv`.

## Why header-only (not a defect)
Emigration Canyon publishes **no channel of citizen-authored written comments** (no eComment,
no emailed-correspondence packet archive). Comment is taken **live** at meetings and captured
only as paraphrase in the minutes. This is the same **submit-only / honest-empty** pattern
documented for south_jordan, taylorsville, west_valley, etc. Filling this file would require
fabricating or mis-labeling minutes speaker-paraphrase as written comment — prohibited.

## If this ever changes
If a future PMN "Supporting Docs" packet bundles genuine written correspondence, or the city
stands up an eComment portal, extract to the standard 14-column schema
(`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`)
and set `district='At-Large'` (Emigration Canyon has no council districts). Until then, the
honest zero stands.
