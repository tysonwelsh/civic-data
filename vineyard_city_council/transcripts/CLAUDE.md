# transcripts/ — Vineyard meeting-video transcripts (ASR captions)

Additive dataset. **Automatic (ASR) transcripts of Vineyard City meeting recordings**
from the city's YouTube channel. NOT an official record — the official record is the
minutes in `../meeting_minutes/`. Built under the expand-city-sources skill, source
type 5 (meeting-video transcripts). Read this before analyzing anything here.

## What this is / is not

- **Is:** YouTube auto-generated English captions (ASR) for meeting livestreams, plus a
  full video→date map of the channel. Word errors are expected; treat text as a search
  aid and a paraphrase, never a quotable transcript.
- **Is not:** a complete transcript archive. Per owner decision 2026-07-05 this is
  **SAMPLE-ONLY** — 10 caption tracks downloaded; the map is the durable deliverable.

## Layout

- `channel_videos.csv` — **the deliverable.** Every video on the channel (47) →
  `date, title, body, video_id, video_url, tab, duration_s, minutes_match`.
  Includes non-meeting/undated clips (blank date). `minutes_match` = does the date hit
  `../meeting_minutes/minutes_index.csv`.
- `index.csv` — the 34 **dated meeting** videos. `format=caption` = track downloaded
  (`path`/`text_path` point to files); `format=na` = mapped-only (sample-only policy).
  Cols: `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,
  format,extraction_method,path,minutes_match,text_path`. `caption_type=asr` always.
- `raw/<date>.vtt` — verbatim YouTube ASR caption track (WebVTT, kept exactly as fetched).
- `raw/_fetch_log.jsonl` — one JSON line per fetch attempt (incl. `no_caption` misses).
- `text/<date>.md` — cleaned readable text (timestamps + inline word-timings stripped,
  rolling-window duplicates collapsed), each **headed** with the ASR-warning banner.
- `AVAILABILITY.md` — channel found, coverage window + cutoff, no-caption meetings,
  Whisper proposals, reproducible recipe. Read it first.

## Coverage & cardinal facts

- **Video exists only 2019-09-25 → 2020-12-09** (plus a 2017 candidate debate). The city
  discontinued YouTube meeting uploads after Dec 2020; 160+ later minutes have no video.
- **Downloaded (10, all City Council):** 2019-12-11 and 2020-{01-08, 02-12, 03-11, 04-08,
  08-26, 09-09, 09-23, 10-14, 10-28}.
- **No ASR available (verified):** 2020-12-09, 2020-11-24, 2020-04-01 — Whisper candidates
  (proposed in AVAILABILITY.md; not run).
- Dates are parsed from video titles; a date here identifies the recording, and lines up
  with the minutes only where `minutes_match=yes` (17 of 34).

## Rules (do not violate)

- **Never quote ASR text as a member's exact words.** For what was actually said/decided,
  use the minutes. ASR is lower-confidence than every other corpus in this repo.
- **Raw `.vtt` is verbatim — never edit.** Regenerate `text/` from raw if the cleaner
  changes; never hand-edit `text/`.
- Additive only. This dataset does not feed `db/`, `weeks/`, or votes.

## Refresh / extend

To pull a mapped-only track, or re-map the channel, use the recipe in AVAILABILITY.md
(`yt-dlp --js-runtimes node --extractor-args "youtube:player_client=android" ...`).
The plain default yt-dlp YouTube client reports "no captions" — the node+android combo
is required in this environment.
