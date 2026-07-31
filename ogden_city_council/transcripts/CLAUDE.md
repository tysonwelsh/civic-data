# ogden_city_council/transcripts — meeting-video transcripts (captions)

Additive dataset. **YouTube ASR auto-captions** for Ogden City Council meeting videos,
plus a full video→date map. Built sample-only (owner decision 2026-07-05): the map is the
deliverable; 10 recent Council meetings were captioned to prove the pipeline. Read
`AVAILABILITY.md` first.

## Cardinal rule for this dataset

These are **automatic (ASR) transcriptions — expect word errors; NOT an official record.**
Every `text/*.md` is headed with that disclaimer. For anything authoritative use
`../meeting_minutes/` (the minutes are the record; captions are context/searchable color).
Never quote a caption as an official council statement without checking the minutes.

## Layout

- `channel_videos.csv` — **the full map.** All 683 videos on the Ogden City Council
  YouTube channel (both `/videos` and `/streams` tabs, which are disjoint). Columns:
  `video_id, video_url, title, channel_tab, parsed_date, is_meeting, minutes_match, slug`.
  `parsed_date` is parsed from the title; `minutes_match=Y` means that date exists in
  `../meeting_minutes/minutes_index.csv`. Blank `parsed_date` = undated placeholder clip.
- `index.csv` — provenance for the meetings we **attempted** (the 10 captioned + the 1
  observed uncaptioned). Cols: `date,title,body,video_url,video_id,caption_type,
  source_url,retrieved_date,format,extraction_method,path`. `format=caption` when a VTT was
  retrieved, `format=na` when the video has no auto-captions. `path` → `raw/…vtt`.
- `raw/<date>_<slug>.vtt` — verbatim YouTube VTT (retained, never edited).
  `<date>_<slug>` avoids same-date collisions.
- `raw/_fetch_log.jsonl` — one JSON line per attempt: video_id, date, status, caption_type,
  sha256, bytes.
- `text/<date>_<slug>.md` — cleaned plain-text render (rolling-caption dedup, HTML entities
  and `>>` speaker markers stripped), headed with the ASR disclaimer + provenance block.

## Source & recipe

Channel: <https://www.youtube.com/channel/UC5SkSjDVRckazUP4nEkYMLA>. Captions are YouTube
ASR only (`en-orig`). The working yt-dlp recipe here (the android player_client variant
returns *no* subs for this channel — use the default client):

```
yt-dlp --js-runtimes node --ignore-no-formats-error --write-auto-sub \
  --sub-format vtt --skip-download --sub-langs en-orig,en \
  https://www.youtube.com/watch?v=<id>
```

## Regenerating / extending

Idempotent scripts are not committed here (sample-only build). To extend: re-enumerate both
tabs with `yt-dlp --flat-playlist`, refresh `channel_videos.csv`, download more VTTs into
`raw/`, re-render `text/`, append to `index.csv` and `raw/_fetch_log.jsonl`. Retain every
raw VTT verbatim. Do not hand-edit `raw/`.

## Not done (see AVAILABILITY.md "Whisper candidates")

Whisper was **not** run. Uncaptioned high-value meetings (2026-05-19; June 2026 sessions)
and a full caption-availability sweep are proposed follow-ups, not part of this build.
