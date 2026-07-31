# Public-Comment Availability — St. George, Utah

**Verdict: PUBLISHED.** Genuine public-submitted **written/online** comments are available
online for **2023 → present (2026)** via the city's public-comments page
(`https://sgcityutah.gov/government/city_council/public_comments.php`). Residents submit
through a JotForm web form / email to `public-comments@sgcity.org`; the City Recorder
batches each roughly-weekly **noon-to-noon window** into one PDF ("Public Comments Received
noon on <date> – noon on <date>.pdf") and posts it. These are the public's own submitted
words — exactly the SLC-style weekly public-comment PDFs the standard targets — and they
populate `all_comments_clean.csv` (`source=written_published`).

## Per-year availability (genuine written/online comments)

| year | status | published PDFs (raw/) | clean comment rows |
|---|---|---|---|
| pre-2023 | **NOT published online** (gap — see below) | 0 | 0 |
| 2023 | PUBLISHED (partial; intake began mid-2023) | 13 | 32 |
| 2024 | PUBLISHED | 13 | 39 |
| 2025 | PUBLISHED | 18 | 40 |
| 2026 | PUBLISHED (partial, through ~June) | 9 | 25 |
| **total** | | **53** | **136** |

- Within published years, coverage is **windows-with-comments only** — empty windows
  ("No comments received") are not posted, so a missing window means none were received/
  published, not a gap in capture.
- All 53 PDFs linked on the city page were captured to `raw/<year>/`. A completeness
  re-scan of the live page (June 2026) found **no additional published written-comment
  files** that we were missing. Some page links are duplicate hrefs (e.g. two labels for
  the Dec 2025 window resolve to the same file); these collapse to the 53 distinct PDFs on
  disk.

## The pre-2023 gap

There is **no online archive of written/email public comments before 2023.** The
`public_comments.php` page only begins in 2023, and there is no separate pre-2023
written-comment archive on the city site or the state Public Notice portal. St. George
began publishing its JotForm written-intake in 2023 (public comment was restructured with
new rules that year). For pre-2023 the only public-comment trace is the **in-person speaker
record** captured from the meeting minutes — and the minutes do **not** transcribe what
speakers actually said; they record only the speaker's name, date, and (sometimes) topic
with a video timestamp. Those records live in `minutes_speaker_log.csv` (e.g. 2022 is
covered by in-person speaker names only). **They are meeting-record notes, not
public-submitted written comments**, and are intentionally kept out of
`all_comments_clean.csv`.

## Deferred future option

Spoken in-person public comment (2022+ and ongoing) exists **only as video** — the verbatim
words are not in the minutes. **Transcribing the council-meeting recordings** to recover
the actual content of in-person comments is a possible future enrichment, but it is **out
of scope** here and has not been done. If pursued, it would be the only way to obtain
pre-2023 (and in-person 2023+) comment *text*.

## Files

- `all_comments_clean.csv` — **136** genuine written/online public comments
  (`source=written_published`), 2023→2026. THE canonical comments dataset.
- `all_comments_dropped.csv` — 11 audit rows removed from the clean set, each with a
  `_drop_reason` (petition signature sheets, attachment-only pages, duplicate forwards).
- `minutes_speaker_log.csv` — **132** in-person speaker record-notes from the minutes
  (NOT public-submitted comments; names/dates/topics only).
- `raw/<year>/` — the 53 immutable source PDFs downloaded from `public_comments.php`.
