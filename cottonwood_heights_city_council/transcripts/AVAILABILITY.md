# Cottonwood Heights City — meeting-video transcripts: availability

**As of:** 2026-07-13 (channel enumerated + undated videos timestamp-probed + captions sampled this date).

## Platform verdict

- **The archive is YouTube: channel "Cottonwood Heights"** (`@CottonwoodHeights`,
  channel id **`UCcOhqM97RmMrEpUz_6L84Cw`**). The city livestreams every council / planning
  commission / CDRA / architectural-review meeting here and archives the streams.
  Confirmed by the city's own "video streaming now available" / "meetings now available on
  YouTube" press notes (Cottonwood Heights Journal, 2018–2019) and the meeting-titled videos.
- **Meeting videos live mostly under the `/streams` tab** (556 items) with the rest among
  `/videos` (139 uploads — a mix of meeting recordings and PR/community content). 695 unique
  videos across both tabs, deduplicated.
- **No PrimeGov/Legistar/Swagit video map exists** — the city portal is Granicus/CivicPlus
  **CivicEngage Central** (a document CMS, `showpublisheddocument`), which hosts minutes PDFs,
  **not** video. YouTube is the only video host. The video→meeting map here is therefore
  **derived from the video titles + a timestamp probe**, not from a portal API (contrast
  herriman, whose PrimeGov `videoUrl` field was authoritative).
- **The city also lists "audio recordings … on Mixlr"** (per its meeting notices) — an
  audio-only mirror, not a transcript source; not pursued (YouTube captions are directly
  fetchable and are the higher-value text).
- **"Utah Record" third-party mirror (`UC5hXeD66VUV_w655ionxaSA`) — checked, no Cottonwood
  Heights content** (sampled its `/videos` and `/streams` tabs; CH is absent — CH runs its own
  comprehensive channel, so the mirror is moot).

## What exists

- **511 meeting videos, 2018-08-28 → 2026-07-07** (every row date-resolved). 184 further
  channel videos are non-meeting/PR content (business spotlights, celebrations, emergency-prep
  clips, recurring-placeholder "…: 1st Tue 7PM" schedule stubs, tests) — excluded from
  `index.csv`, fully listed in `channel_videos.csv` (`is_meeting=no`, `body` ∈ NonMeeting/Other).
- **Body breakdown** (title keyword → CDRA/Joint/PC/ARC/Council, in that precedence):

  | body | n | range | note |
  |---|---|---|---|
  | Council | 372 | 2018-08-28 → 2026-07-07 | 1st & 3rd Tuesday; Work Session + Business Meeting are usually **separate videos** the same day |
  | PlanningCommission | 93 | 2021-01-06 → 2026-07-01 | Wednesday; channel PC coverage starts 2021 |
  | CDRA (Community Development & Renewal Agency) | 32 | 2020-10-20 → 2026-01-20 | the council's in-session redevelopment agency — sometimes streamed as its own video |
  | Joint (Council + Planning Commission) | 2 | 2024-10-29, 2025-10-21 | joint work sessions |
  | ARC (Architectural Review Commission) | 12 | 2020-12-17 → 2025-12-18 | **out of the core minutes/vote scope** — catalogued for completeness, not in `meeting_minutes/`/`planning_commission/` |

- **Per year (meeting videos):** 2018 ×7 · 2019 ×48 · 2020 ×50 · 2021 ×69 · 2022 ×80 ·
  2023 ×76 · 2024 ×60 · 2025 ×85 · 2026 ×36 (through 2026-07-07).
- A meeting day is often **two videos** (Work Session + Business Meeting/Session) — `index.csv`
  is one row per **video**, not per meeting; join on `(date, video_id)`, then disambiguate the
  same-day pair by the title (Work Session vs Business Meeting).

## Caption availability

- **Every video checked carries YouTube automatic (ASR) English captions** — `en` + `en-orig`
  tracks, `vtt`/`srt`/`ttml`/`json3`. **`--list-subs` on 2018 and 2026 council videos both
  reported "no subtitles" (no human/manual track) but full automatic captions.** All 10 sampled
  videos (2018→2026, spanning Council/CDRA/PC/Joint) fetched captions on the first try with the
  default `android_vr` player client — **no `player_client` iteration was needed** and **no
  Whisper is required**. `caption_type=asr` is asserted platform-wide from this sample.
- **No manual/human caption track was found on any video.**

## What was fetched (SAMPLE-ONLY policy, owner decision 2026-07-05 on bulk ASR backlogs)

**10 caption files** (5.2 MB VTT → ~108.7k words cleaned text), chosen for era + body + date-source spread:

| date | body | why |
|---|---|---|
| 2018-08-28 | Council | earliest meeting video on the channel (pre-data-floor depth) |
| 2019-10-01 | Council | **undated "…Meeting - Live" title → date recovered via release_timestamp** (probe-path proof) |
| 2020-07-07 | Council | data-floor year; COVID/Zoom-era meeting; minutes exist on disk (cross-check) |
| 2020-10-20 | CDRA | earliest CDRA (in-session redevelopment agency) video |
| 2022-01-04 | Council | minutes exist on disk; portal-decayed-window year |
| 2023-01-04 | PlanningCommission | PC body sample (Wednesday cadence) |
| 2024-01-02 | Council | minutes exist on disk (2024 audited layer) |
| 2025-10-21 | Joint | one of only 2 Joint Council+PC sessions; has `>>` speaker-change markers |
| 2026-07-01 | PlanningCommission | most recent PC; newer than PC minutes on disk |
| 2026-07-07 | Council | most recent council; **newer than newest council minutes on disk** (publishing lag) |

The other **501 rows are honest `format=na` map rows** (`extraction_method=mapped_not_fetched`)
with live watch URLs; fetch on demand (see `CLAUDE.md`).

## Date + body provenance

- **467 of 511 dates come straight from the video title** — CH titles almost every meeting
  video with a date: modern ISO-prefixed ("2026-07-07 Council Business Meeting", 111) and the
  2018–2023-era "Cottonwood Heights City Council Meeting 8-28-18 #1" M-D-YY style (333), plus
  "Aug. 3, 2021" month-name (22) and one "2025 05 07" space-YMD.
- **44 dates were recovered by a per-video `release_timestamp` probe** (`date_source=
  yt_release_ts_local`) — these are the early-era "Cottonwood Heights City Council Meeting -
  Live" streams whose title has no date. The epoch is converted to **America/Denver (UTC-7)**
  before formatting, so a near-midnight UTC timestamp does not roll to the wrong calendar day
  (the murray gotcha). `release_timestamp` (stream start) is preferred over the publish
  `timestamp`.
- **Cadence:** Council = **Tuesday (1st & 3rd)**, PC = **Wednesday** — matches the repo's known
  weekdays; both bodies are title-dated so no weekday inference was needed.

## Gaps these videos can fill (high-value backlog)

1. **The channel reaches back to 2018-08-28** — ~55 meeting videos in **2018–2019 predate the
   repo's 2020 data floor**. If the floor is ever lowered, the ASR transcript is a readable
   record for that era (minutes would come from PMN/GRAMA).
2. **2026-07-07 council + 2026-07-01 PC are newer than the newest minutes on disk** — normal
   publishing lag; the transcript is the only readable record until minutes post.
3. **CDRA / Joint / ARC standalone videos** capture bodies whose deliberation the terse
   council minutes summarize away.

## Whisper candidates — NONE needed

Every video checked already has a YouTube ASR caption track (2018→2026 sample, all 10 fetched
first-try), so **no meeting is caption-less → the Whisper candidate list is empty**. The
actionable proposal (owner decision, not run) is a **bulk `yt-dlp` caption fetch of the 501
un-fetched meeting videos** (~4 s/video throttled, est. ~260 MB VTT). Any video found
caption-less at fetch time becomes the Whisper candidate.

## Honest limits

- **ASR quality**: no speaker labels (except the `>>` change markers some tracks carry),
  proper nouns garbled ("Cottonwood"→"Conwood", "Weichers"→"Wickers", ordinance/case numbers
  misheard). Never quote ASR text as the official record — the clerk's minutes under
  `meeting_minutes/` / `planning_commission/` are authoritative.
- `caption_type=asr` on the 501 `format=na` rows is a platform-pattern assertion (sampled, not
  per-video verified).
- One meeting day = up to two videos (Work Session + Business Meeting) — `index.csv` is one row
  per video.
- `channel_videos.csv` `is_meeting` classification is title-keyword based; a handful of oddly
  titled meetings could be miscategorized as NonMeeting (conservative — a body keyword is
  required). ARC rows are meetings but sit outside the core council/PC vote scope.
- `screen_corpus.py` on `text/` (2026-07-13): **0 hard flags**; dict_ratio median 0.865
  (stable 0.853–0.884 across 2018→2026), 0 split-word / weird-char outliers — normal ASR.
- yt-dlp warned "No supported JavaScript runtime" + "ffmpeg not found" (2026-06 build
  deprecation) — caption fetches still succeed; a future bulk refresh may want `deno` installed.
