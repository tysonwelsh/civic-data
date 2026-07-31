# public_comments/ — Murray City

## What's here

| File | What it is |
|---|---|
| `all_comments_clean.csv` | **Header-only (an honest empty)** — the 14-column SCHEMA_SPEC standard for a city that publishes no comments dataset. Murray is a **submit-only** city; there is no genuine written-comment corpus to materialize. |
| `AVAILABILITY.md` | The 6-target availability hunt (2026-07-11, browser UA) + verdict: **NO published written-comment archive**. Read this first. |

## The verdict — HONEST-EMPTY (submit-only)

Murray City accepts public comment only **live at meetings** (in person / via the
`murraycitylive.com` livestream) and **by email** to council/commission staff. It does
**not** operate an eComment / Open City Hall / "correspondence received" portal, and posts
**no** written-comment or letters-received archive anywhere on its site. Its CivicPlus
agenda-packet archives (Council `AMID=83`, PC `AMID=32`) bundle agenda + staff reports only —
a sampled 303-page packet carried **zero** correspondence/public-comment sections.

This is a **legitimate honest zero**, not a scraping gap — like the submit-only SLCo siblings
(south_jordan / taylorsville). Per the collection's no-invention rule, no comments table is
fabricated.

## Schema (header row only)

`all_comments_clean.csv`:
`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`

The file holds **only this header** and no data rows.

## Inline speaker notes are NOT comments

Every regular Council (and PC) minutes doc carries a **`Citizen Comments:`** block and, per
noticed item, a **`Public Hearings:`** block recording — in the clerk's words — who approached
and a one-line paraphrase (e.g. *"No comments were given."*). These are **meeting-record
speaker notes, NOT public-submitted written comments** (no author text, subject, or
attachment), so they are deliberately **not** reconstructed into `all_comments_clean.csv`.
They live in the minutes bodies (`../meeting_minutes/minutes/`) and are searchable there;
building a labeled `minutes_speaker_log.csv` from them is a possible future enhancement (noted
in `../recon.md`), deliberately not done here.

## Don't

- Don't treat the inline minutes speaker paraphrases as public comments, or synthesize a
  comments table from them.
- Don't re-download CivicPlus agenda packets expecting correspondence — a full packet was
  sampled and confirmed to contain none (see `AVAILABILITY.md`).
- Don't read the empty CSV as a gap to be filled — Murray publishes no comments dataset.
