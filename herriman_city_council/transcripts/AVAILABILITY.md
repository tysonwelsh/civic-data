# Herriman City — meeting-video transcripts: availability

**As of:** 2026-07-13 (channel enumerated + PrimeGov API harvested + captions sampled this date).

## Platform verdict

- **The archive is YouTube: channel "Herriman City"**
  (`https://www.youtube.com/channel/UCBFfCj0QT3f_2UfBE45al1w`). Meeting videos live
  mostly under the **live-streams tab** (626 streams) with some meeting uploads among the
  **/videos tab** (357 uploads, mostly non-meeting PR content — Herrimanology newsletter,
  business spotlights, ceremonies).
- **PrimeGov is the authoritative video→meeting map, not a video host**: each meeting in
  `ListArchivedMeetings?year=YYYY` carries a **`videoUrl` field pointing at YouTube**
  (298 meetings with videoUrl 2021–2026, resolving to 264 distinct videos + 5 videos not
  discoverable on the channel tabs, i.e. unlisted). `isMediaManagerVideo=false`,
  `swagitId=null` everywhere — no PrimeGov-native/Swagit video layer exists.
- ⚠ PrimeGov `videoUrl` is clerk-entered and has errors: 2 same-id-different-date
  copy-paste conflicts (both resolved in favor of the title-printed date; the 2024-01-10
  sample transcript literally opens "Wednesday January 10th" where PrimeGov pointed
  2024-01-24) and one garbage value (`Q:\RECORDS\Audio Recordings\2022`, a pasted local
  drive path on a 2022 meeting).
- No OpenUtah mirror was needed (YouTube captions are directly fetchable).

## What exists

- **677 meeting videos, 2015-03-11 → 2026-07-08** (channel /videos + /streams tabs +
  5 PrimeGov-only unlisted ids, deduplicated; every row date-resolved). Regular meeting
  streams start **2017-11-08**; continuous coverage from **2018**. The single 2015 row is
  a 52-second junk clip. 311 further channel videos are non-meeting PR content — excluded
  from `index.csv`, fully listed in `channel_videos.csv` (`body` ∈ NonMeeting/Other).
- Body breakdown (title keywords first, then PrimeGov committeeId):
  **Council 465 · PlanningCommission 180 · Joint 21 · Canvass 5 · HCSEA 3 · CDRA 2 ·
  HCFSA 1**. The standalone CDRA/HCSEA/HCFSA rows are the rare separately-streamed agency
  sessions (e.g. truth-in-taxation hearings); normally the agencies are **in-session inside
  the Council stream** — PrimeGov maps the same video id to Council + CDRA + HCSEA + HCFSA
  meetings on the same date (`pg_bodies` column), matching the repo's in-session `body`
  design. The sampled 2022-06-23 transcript confirms it ("we have three meetings today").
- Per year: 2017 ×7 · 2018 ×80 · 2019 ×78 · 2020 ×67 · 2021 ×83 · 2022 ×96 · 2023 ×87 ·
  2024 ×70 · 2025 ×70 · 2026 ×38 (through 2026-07-08).
- A meeting evening is often **several streams** (work meeting, work meeting 2, general
  meeting, occasional Part 1/Part 2) — `index.csv` is one row per **video**, not per
  meeting; join on `(date, video_id)`. 46 rows are junk-short (< 10 min — false starts,
  test clips, brief specials); filter with `duration_sec`.
- **Captions: YouTube automatic (ASR) English on every video checked** — 4 probed with
  `--list-subs` spanning 2017→2026, 10 fetched; **zero manual/human caption tracks** seen.
  `caption_type=asr` is asserted platform-wide from that sample (same convention as
  murray/west_valley/logan).

## Date + body provenance

- **648 of 677 dates are printed in the video title** (`date_source=title`) — Herriman
  titles its streams "City Council Meeting - July 8, 2026" (abbreviated-month and
  numeric M-D-YY variants in the 2019–2020 era). 4 rows `primegov` (PrimeGov meeting
  dateTime; title undated), 2 `title_pg_conflict` (title kept — see verdict above),
  2 `yt_release_ts_local` (release_timestamp converted to America/Denver — the murray
  UTC+1-day gotcha does not bite a timezone-converted timestamp), 1 `yt_upload_date_utc`
  (the 2015 junk clip).
- **Cadence note:** the PC met **Thursday** through ~2022 and **Wednesday** after (108 Thu
  vs 72 Wed PC videos) — both are title-dated, so no weekday inference was ever needed.
  Do not assume the current 1st/3rd-Wednesday cadence for the early era.

## What was fetched (SAMPLE-ONLY policy, owner decision 2026-07-05)

**10 caption files** (6.4 MB VTT → ~133k words cleaned text), chosen for spread + probes:

| date | body | why |
|---|---|---|
| 2017-11-08 | Council | earliest full meeting stream (pre-data-floor era depth) |
| 2019-08-14 | Council | pre-floor era, numeric-date title style |
| 2020-02-12 | Council | minutes cross-check (recon-verified minutes exist on disk) |
| 2020-05-13 | Council | **no-minutes date** (4.4 h COVID-era meeting) |
| 2021-09-02 | PlanningCommission | PrimeGov-only unlisted video (fetch path proven) |
| 2022-05-11 | Council | **no-minutes date** (2022 minutes-publishing gap) |
| 2022-06-23 | Council | multi-body special evening (Council+CDA+HCSEA verified) |
| 2024-01-10 | Council | title-vs-PrimeGov date conflict (title verified correct) |
| 2026-07-01 | PlanningCommission | newer than PC minutes on disk (publishing lag) |
| 2026-07-08 | Council | most recent council; newer than minutes on disk |

The other 667 rows are honest `format=na` map rows (`extraction_method=mapped_not_fetched`)
with live watch URLs; fetch on demand (see `CLAUDE.md`).

## Gaps these videos can fill (high-value backlog)

Cross-referencing `minutes_match` (video date present in `meeting_minutes/minutes_index.csv`
/ `planning_commission/minutes_index.csv`):

1. **41 distinct date/body meeting days in 2020→2025 have video but NO minutes on disk**
   (51 substantive ≥10-min videos; see `minutes_match=False` within the minutes window).
   Concentrations: **2022 council** (2022-01-11, 2022-01-25 WM2, 2022-03-23, 2022-05-11,
   2022-08-10), scattered 2020–2021 council dates (2020-03-25, 2020-09-23, 2020-10-14,
   2020-12-09…), **8 joint CC/PC sessions 2020–2025** (no joint minutes dataset exists),
   ~15 PC dates, the 2023-08-22 truth-in-taxation hearing, and the 2023-12-15 emergency
   meeting. For these the ASR transcript is the only readable record in this repo.
   (Some may be minutes the city never published on PrimeGov rather than meetings that
   produced no minutes — a publishing gap either way.)
2. **9 rows post-2026-05-27** are newer than the newest minutes on disk — normal
   publishing lag, self-healing via `fetch_new.py`.
3. **166 pre-2020 rows (2015/2017–2019)** are below the repo's data floor — the channel
   holds ~2.5 years of pre-floor meetings (back to 2017-11-08) if the floor is ever
   lowered; minutes for that era would come from the legacy S3 bucket/PMN.

## Whisper candidates — NONE needed; propose bulk ASR-caption fetch instead

Every video checked already has a YouTube ASR caption track, so **no meeting is
caption-less → the Whisper candidate list is empty**. The actionable proposal (owner
decision, not run) is a **bulk yt-dlp caption fetch of the 51 substantive no-minutes
videos** (~2–3 s/video, est. ~35 MB VTT). Any video found caption-less at fetch time
becomes the Whisper candidate.

## Honest limits

- ASR quality: no speaker labels; proper nouns (member names, plat/case numbers)
  frequently misrecognized. Never quote ASR text as the official record.
- `caption_type=asr` on `format=na` rows is a platform-pattern assertion (sampled, not
  per-video verified).
- `minutes_match` for Joint rows checks both minutes indexes; a Joint `True` may mean
  only one body's minutes exist.
- Streams before 2017-11 don't exist on this channel (channel floor, not a collection
  miss); no second/legacy video platform was found (herriman.gov embeds this channel).
- `screen_corpus.py` on `text/` (2026-07-13): **0 hard flags**; 7/10 `ends_mid`
  advisories — expected for ASR (caption track stops when the broadcast cuts), not an
  extraction defect. dict_ratio median 0.864, stable 2017→2026.
