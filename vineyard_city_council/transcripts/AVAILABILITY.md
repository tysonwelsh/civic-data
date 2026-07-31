# Vineyard City — meeting-video transcripts: availability

_As-of 2026-07-05. Additive dataset. Sample-only by owner decision (see below)._

## Source found

- **Channel:** **Vineyard City** on YouTube — handle `@vineyardcity7475`,
  channel id `UC_IoRhVzIR3LJPp7V9i-lqw`
  (`https://www.youtube.com/channel/UC_IoRhVzIR3LJPp7V9i-lqw`).
  This is the city's own channel; meeting recordings live on the **`/streams`** tab
  (33 items); the **`/videos`** tab (14 items) holds a few meeting recordings plus
  outreach content (LIVE episodes, ceremonies, candidate nights, PSAs).
- **No other video source.** OpenUtah/OpenCity (`vineyard.openutah.org`) exists but is
  empty for Vineyard — "0 meetings indexed · 0 transcribed" as of 2026-07-05. The city
  website, CivicClerk portal, and SuiteOne host expose documents only, no video. No
  Vimeo/Granicus presence found.

## What was mapped

- **`channel_videos.csv`** — the durable deliverable: **all 47 channel videos**
  (33 streams + 14 videos) → date, body, duration, `minutes_match`.
  - **34 are dated meeting videos**; 13 are non-meeting (undated) outreach clips.
  - Bodies among dated: city_council 19, planning_commission 10, rda 3, joint 2.
  - **17 of 34** dated videos match a date in `../meeting_minutes/minutes_index.csv`
    (the rest are pre-2020, before the minutes index begins 2020-01-08).
- **`index.csv`** — the 34 dated meeting videos, `format=caption` for the 10 downloaded,
  `format=na` for the 24 mapped-only.

## Coverage window & cutoff

- **Meeting video exists only 2019-09-25 → 2020-12-09.** Plus one undated outreach clip
  from 2017 (candidate debate). That is the whole of the channel's meeting history.
- **Hard cutoff after 2020-12-09.** The city stopped posting meeting recordings to
  YouTube. Minutes continue through 2026-06 (160+ later meetings) with **no
  corresponding video** on this channel. The task's nominal 2014–2026 window therefore
  has video for **~15 months only** — this is a short-history, fast-growing city that
  livestreamed briefly during the COVID period and then discontinued the YouTube uploads.
- Captions are **YouTube ASR** (auto-generated `en`; `en` and `en-orig` are identical).

## Sample retrieved (owner policy: SAMPLE-ONLY)

Per owner decision 2026-07-05, only a ~10-meeting representative sample of ASR caption
tracks was downloaded (recent Council); the full map above is the deliverable.

**10 City Council caption tracks** in `raw/*.vtt` (+ cleaned `text/*.md`):
2019-12-11, 2020-01-08, 2020-02-12, 2020-03-11, 2020-04-08, 2020-08-26, 2020-09-09,
2020-09-23, 2020-10-14, 2020-10-28. These span the full active-video window (the two
most-recent council meetings, 2020-11-24 and 2020-12-09, were the intended top of the
sample but have **no ASR captions** — see below — so 2019-12-11 backfills the tenth slot).

The remaining 24 dated videos are mapped-only (`format=na`); their caption tracks were
not downloaded under the sample-only policy. Spot checks show ASR captions **do** exist
for the 2019 council meetings and can be pulled the same way if a full harvest is later
authorized.

## Meetings with NO ASR captions (verified 2026-07-05)

These returned "no subtitles for the requested languages" on a real download attempt —
YouTube never generated ASR for them:

| date | video_id | body | duration | note |
|------|----------|------|----------|------|
| 2020-12-09 | aKJbZe6yZI4 | city_council | 5217s | year-end meeting; most recent council video |
| 2020-11-24 | WOQmXEW__Uo | city_council | 841s  | short (~14 min) |
| 2020-04-01 | SobmGviO-Bo | joint PC+Council | 12814s | longest video on the channel; early-COVID joint session |

## Whisper candidates (PROPOSED ONLY — not run)

Whisper is warranted only for the three **no-ASR** meeting videos above, since every
other mapped video already has an ASR track that merely needs downloading. Highest value:

1. **2020-04-01 joint City Council + Planning Commission** (`SobmGviO-Bo`, 3h33m) — the
   single longest, wholly untranscribed, early-COVID joint session.
2. **2020-12-09 City Council** (`aKJbZe6yZI4`, 1h27m) — most recent council video; the
   only 2020 year-end meeting on video with no captions.
3. **2020-11-24 City Council** (`WOQmXEW__Uo`, 14m) — short, lower priority.

## How captions were retrieved (reproducible)

yt-dlp 2026.06.09. The default YouTube client returned "no captions"; the working recipe
routes JS through node and uses the `android` player client:

```
yt-dlp --js-runtimes node --extractor-args "youtube:player_client=android" \
  --ignore-no-formats-error --write-auto-sub --sub-format vtt --skip-download \
  --sub-langs "en" -o "raw/<date>.%(ext)s" <video_url>
```

Enumeration: `yt-dlp --flat-playlist <channel>/streams` and `.../videos`. Per-fetch
provenance in `raw/_fetch_log.jsonl` (incl. the no-caption records).
