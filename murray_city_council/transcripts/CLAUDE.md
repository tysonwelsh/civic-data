# transcripts/ — Murray City meeting-video transcripts (YouTube ASR)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 5). **Additive dataset**
— nothing in `meeting_minutes/`, `planning_commission/`, `db/`, or `weeks/` was touched.

## Source

- **Channel:** MURRAY CITY LIVE — `https://www.youtube.com/channel/UC_19hfQocAIWupAD5-h6oaw`
  (the target of the `murraycitylive.com` frameset → Wix landing page; see
  `AVAILABILITY.md` for the platform verdict, incl. why CivicMedia/TikiLive is not it).
- **Enumeration:** `yt-dlp --flat-playlist` over the channel's `/streams` (332) and
  `/videos` (7) tabs → 339 unique videos, 2019-10-01 → 2026-07-07.
- **Captions:** YouTube **automatic (ASR) English** tracks via
  `yt-dlp --write-auto-sub --write-sub --sub-lang en --sub-format vtt --skip-download`
  (official timedtext path only). No manual caption tracks exist on this channel
  (sample-verified). `caption_type=asr` everywhere.

## Files

```
index.csv           §9 contract header (date,title,body,video_url,video_id,caption_type,
                    source_url,retrieved_date,format,extraction_method,path) + extras:
                    duration_sec,date_source,body_source,minutes_match. 339 rows:
                    10 format=caption (fetched), 329 format=na (mapped_not_fetched).
channel_videos.csv  the full video→date→body map (same 339, analysis-friendly columns).
raw/                10 fetched .vtt caption tracks, named <date>_<video_id>.en.vtt.
text/<date>.md      cleaned transcripts, headed "AUTOMATIC TRANSCRIPTION — ASR…".
clean_vtt.py        the .vtt → cleaned-markdown converter (dedupes YouTube's
                    rolling-caption repetition, strips inline <c>/timestamp tags).
AVAILABILITY.md     platform verdict, caption stats, gap analysis, fetch backlog.
```

## How dates and bodies were derived (read before joining)

- **`date_source`** — `title` (236 rows: printed in the video title, trusted);
  `yt_release_date*` (103 rows: YouTube stream metadata, which is **UTC** — evening
  meetings roll into the next UTC day, so 53 rows were shifted back one day:
  `…_utc-1_minutes_match` = the shifted date matches a minutes date on disk (30),
  `…_utc-1_weekday` = Wed→Tue / Fri→Thu cadence shift only (23)).
- **`body_source`** — `title` when the title names the body, else `weekday`
  (**Tuesday = Council, Thursday = PlanningCommission** — Murray's cadence). 9
  non-Tue/Thu title-dated streams stay `Unknown`.
- **⚠ A Tuesday "Council" stream is the WHOLE evening**: typically RDA board →
  Committee of the Whole → Council meeting in one video (verified in the sampled
  transcripts). Don't assume minute-0 of a Tuesday video is the council call to order.
- **`minutes_match`** — whether the video's date appears in this repo's
  `meeting_minutes/minutes_index.csv` (Council rows) or
  `planning_commission/minutes_index.csv` (PC rows). `False` rows in 2023 (council) and
  2023–2026 (PC) are the city's known publishing gaps — **the ASR transcript is the only
  readable record for those meetings** (see AVAILABILITY.md).

## SAMPLE-ONLY policy

Per the owner decision (2026-07-05) on bulk ASR backlogs, only a 10-video representative
sample was caption-fetched (prioritizing the 2023 council TMM gap + the post-2022 PC
gap + one minutes-cross-check). The other 329 rows are honest `format=na` map rows with
live watch URLs; fetch on demand:

```
python3 -m yt_dlp --write-auto-sub --write-sub --sub-lang en --sub-format vtt \
  --skip-download -o "raw/<date>_<video_id>.%(ext)s" "https://www.youtube.com/watch?v=<video_id>"
python3 clean_vtt.py raw/<date>_<id>.en.vtt text/<date>.md <date> <Body> <id>
```

## Caveats

- **ASR, not a record**: no speaker labels, proper nouns garbled. The clerk's minutes
  (where they exist) are authoritative; transcripts fill deliberation detail + the two
  minutes gaps only.
- Two streams can share a date (CoW + Council streamed separately, false starts) —
  `index.csv` is one row per **video**, not per meeting; key joins on
  `(date, video_id)`. ~15 junk-short clips (< 10 min) are kept honestly; filter with
  `duration_sec`.
- `text/<date>.md` exists only for the 10 sampled dates; each date sampled has exactly
  one fetched video, so date-keyed filenames are unambiguous.
