# public_comments/ — Riverton City (HONEST-EMPTY, submit-only)

## Verdict: SUBMIT-ONLY / NOT PUBLISHED
Riverton City publishes **no** written-comment archive. `all_comments_clean.csv` is
**header-only by design** — a legitimate honest zero, **not** a gap to fill. Full audit (avenues
checked, browser-UA, with the JSON verdict block) is in **`AVAILABILITY.md`** — read it before
asserting anything about Riverton public comment.

## Files
- `AVAILABILITY.md` — the SUBMIT-ONLY determination + every avenue checked (city site, Granicus
  publisher, minutes, agenda packets, records archive) with URLs and results.
- `all_comments_clean.csv` — the standard comment schema **header only** (no rows). Kept so
  cross-city tooling that expects the file finds a valid empty table.

## How comment is taken (none archived)
1. **In person** at the meeting (Riverton City Hall, 12830 S 1700 W): Council 15 min total /
   3 min per speaker; PC comment restricted to public-hearing items.
2. **eComment** — a live per-agenda **submission button** on the Granicus meeting portal
   (`rivertoncity.granicus.com`, `js/ecomment.buttons.js`). A submission channel, **not** an
   archive — Granicus does not publish the submissions back (the publisher lists Agenda / Minutes
   / Video only).
3. **Written, in advance** — emailed to the City Recorder (`recorder@rivertonutah.gov`). Not
   published.

## What the minutes DO carry (labeled correctly, NOT merged here)
Both bodies transcribe in-person / public-hearing speakers **inline** as the recorder's
third-person paraphrase (named speakers, near-verbatim, e.g. Council 2025-12-16 "Citizen Comment"
and PC public-hearing sections). Per the collection's extraction standard this is a
**`minutes_speaker_log`** (meeting-record notes), **explicitly NOT** public-submitted written
comments — so it does **not** populate `all_comments_clean.csv`. If a labeled speaker log is ever
built from the minutes markdown, it stays a separate artifact.

Treat the empty comments dataset as a truthful honest zero — like Taylorsville / South Jordan /
West Valley, and unlike SLC / Park City (which do publish substantive written comment).
