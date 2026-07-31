# public_comments/ — Lehi, UT

## TL;DR
Lehi publishes genuine written public comments **only in one place: the 2020 COVID-era
council minutes**, where residents' own submitted written/online/email/eComment text was
reproduced **verbatim**. Those **42 comments** are in `all_comments_clean.csv`. The
ongoing Granicus **SpeakUp eComment** portal (`lehi.granicusideas.com`) is **submit-only**
— residents submit a position + comment per agenda item, but nothing is publicly displayed
or archived (closed meetings show only "the online Comment window has expired").

→ Verdict: **IN-MINUTES-ONLY** for genuine published comments; **SUBMIT-ONLY** for the
live portal. See `AVAILABILITY.md` for every avenue checked (with URLs).

## The distinction (read this before touching the CSVs)
- `all_comments_clean.csv` = **residents' OWN verbatim written/online text** that the city
  published (the 2020 minutes appendices/inline online comments). These are genuine
  public-submitted comments.
- `minutes_speaker_log.csv` = the clerk's **third-person PARAPHRASE** of who spoke in
  person during Citizen Input ("Casey Glade expressed concerns with …"). These are
  **meeting-record notes, NOT** the public's own written words. Per
  extraction_standards.md they are kept strictly separate and must **never** be moved into
  `all_comments_clean.csv`.

## Files
| File | What it is |
|---|---|
| `all_comments_clean.csv` | **42** genuine verbatim written/online/email/eComment comments published in the 2020 minutes (4 meetings: 2020-03-30, 04-13, 06-08, 06-22). SLC schema. 32 named, 10 anonymous. |
| `all_comments_dropped.csv` | 9 dropped segmentation artifacts (minutes attest blocks + email signature tails). |
| `minutes_speaker_log.csv` | **160** in-person Citizen-Input speakers, 2020–2026. Clerk paraphrases; `quality_flag = clerk_paraphrase_not_written_comment`. First line is a header note saying so. |
| `extract_comments.py` | Rebuilds `all_comments_clean.csv` + `all_comments_dropped.csv` (copies text verbatim from the minutes; best-effort name from email `From:` header or sign-off; no fabrication). |
| `extract_speaker_log.py` | Rebuilds `minutes_speaker_log.csv` from the minutes' Citizen Input sections. |
| `raw/` | Raw text pulled from the minutes (2020 comment appendices + the two inline online comments). |
| `AVAILABILITY.md` | Full hunt (SpeakUp portal, Granicus archive/packets, city site, minutes, records) + verdict. |

## Why most of the dataset is 2020 only
Lehi only reproduced submitted written comments in the minutes during the **virtual-meeting
period**. Once in-person meetings resumed, written comments moved to the SpeakUp eComment
tool (submit-only) or direct email to officials, and the minutes reverted to merely
**paraphrasing** in-person speakers. There is no city-published written-comment or
correspondence archive for 2021–present (a GRAMA request would be needed for raw eComment
submissions).

## Reproduce
```bash
python3 extract_comments.py      # -> all_comments_clean.csv (42), all_comments_dropped.csv (9)
python3 extract_speaker_log.py   # -> minutes_speaker_log.csv (160)
```

## Don't
- Don't move speaker-log paraphrases into `all_comments_clean.csv`.
- Don't treat the SpeakUp portal as a published archive — it is submit-only (verified:
  open meetings show only empty submission forms, closed meetings show "comment window has
  expired", no public read API).
- Don't assume the comments CSV should cover 2021+. It is intentionally 2020-only because
  that is the only period the city published residents' written text.
```json
{"verdict":"in-minutes-only","genuine_comments":42,"speaker_log_rows":160,"ecomment_public":false}
```
