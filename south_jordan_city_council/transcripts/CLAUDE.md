# transcripts/ — meeting video transcripts (source type #5)

**Additive dataset. SAMPLE-ONLY by owner policy. As-of 2026-07-06.**

## What this is
A map of South Jordan City's YouTube presence plus a small sample of retrieved ASR caption
tracks. **Read `AVAILABILITY.md` first** — the headline is that **South Jordan does not post
council/Planning-Commission meeting *video* to YouTube**; the official channel is
PR/promotional only, and meetings exist as **audio + minutes** elsewhere. So this dataset is
**not** a corpus of meeting deliberation transcripts; it honestly maps what YouTube offers
and samples it.

## Layout
```
raw/
  _channel_videos.jsonl    yt-dlp --flat-playlist dump of the channel /videos (134 rows) — provenance
  _channel_streams.jsonl   /streams tab dump (1 row)
  _videos_full.jsonl       per-video --dump-json metadata (125 available; 9 unavailable) — caption detection
  _ids.txt                 the 134 video ids
  *.vtt                    the 10 retrieved sample ASR caption tracks (named <upload_date>__<video_id>.vtt)
  _dl_samples.log / _enum_err.log / _full_err.log   yt-dlp run logs
text/
  <upload_date>__<video_id>.md   cleaned transcript text, each headed
                                 "AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official record"
index.csv                 channel map — 125 available videos (see schema below)
unrecovered.csv           9 videos that are removed/private (yt-dlp "not available")
AVAILABILITY.md           what was checked, the meeting-video gap, Whisper candidates
CLAUDE.md                 this file
```

## Source
- **Channel:** "City of South Jordan" — `https://www.youtube.com/channel/UCvt-dQqGhbNgvPFomcQBFQw`
  (found via web search; confirmed the only official SJ channel).
- Enumerated with `yt-dlp --flat-playlist` (channel `/videos`, `/streams`, `/playlists`).
- Per-video caption availability from `yt-dlp --skip-download --dump-json`
  (`subtitles` = manual, `automatic_captions` = ASR).

## Build method
```
# enumerate
python3 -m yt_dlp --flat-playlist --dump-json <channel>/videos      > raw/_channel_videos.jsonl
python3 -m yt_dlp --skip-download --dump-json -a raw/_ids.txt       > raw/_videos_full.jsonl
# retrieve a sample caption track (per video)
python3 -m yt_dlp --write-auto-sub --write-sub --sub-langs "en.*,en" \
    --sub-format vtt --skip-download -o "<date>__<id>.%(ext)s" <video_url>
```
VTT → text cleaning: strip `WEBVTT`/`Kind:`/`Language:` headers, cue timestamps, inline
`<...>` timing tags; HTML-unescape; drop `>>` speaker carets; collapse YouTube's rolling
duplicate cue lines. (Inline script, not committed — the raw `.vtt` is the retained original.)

## index.csv schema
`date, title, body, video_url, video_id, caption_type, source_url, retrieved_date, format,
extraction_method, path, upload_date, stored_locally`
- `date` / `upload_date` = YouTube upload date (YYYY-MM-DD); **not** a meeting date — these
  are not meetings.
- `caption_type` ∈ `manual` (19) / `asr` (65) / `none` (41). The 9 `unavailable` (removed/private)
  videos are in `unrecovered.csv`, not `index.csv` (they have no resolvable date).
- `format` = `caption` when a caption track exists, else `video`, else `na` (unavailable).
- `stored_locally` = `yes` for the 10 retrieved samples (with a `path` into `raw/`), else `no`
  (index-only; re-fetchable from `source_url`).

## Sample selection (10)
Chose the most governance-adjacent ASR videos so the sample is maximally useful despite the
meeting-video gap: Oath of Office 2026, Economic Development (2021 & 2024), General Plan
"City in a Minute", Property-Tax + Truth-in-Taxation explainers, "How SoJo Handles Traffic",
SoJo News Now, City-Manager Community Roundtable, Economic Update 2020.

## Linkage
**None to `all_votes.csv`** — these are not meetings, so there is no meeting-date join.
If real meeting transcripts are later derived (OpenUtah reuse or Whisper over city audio),
they would join to minutes/votes by meeting date on the Tuesday weekly grid.

## Caveats / non-negotiables honored
- Raw `.vtt` retained verbatim; enumeration JSONL kept as provenance.
- ASR text is machine transcription — headers warn of word errors; not an official record.
  Source artifacts (music cues, `[music]`, mis-hearings) are preserved, not "cleaned up".
- `screen_corpus.py text/` → 0 outliers (dict_ratio 0.79–0.90, normal for ASR speech).
- No Whisper, no bulk harvest, no OpenUtah scrape — sample-only by owner policy.
