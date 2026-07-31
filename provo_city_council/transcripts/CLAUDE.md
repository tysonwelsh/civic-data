# transcripts/ — Provo meeting video transcripts (ASR captions)

**Additive dataset** (Source 5 of `expand-city-sources`). ASR caption tracks of Provo
Municipal Council / Work meetings from the city's YouTube channel, keyed by meeting date.
Modifies no existing dataset. **Everything here is AUTOMATIC (ASR) transcription — expect
word errors; NOT an official record.** The authoritative record remains
`meeting_minutes/` (clerk minutes) and the source video.

## Layout

```
transcripts/
  raw/<video_id>.en-orig.vtt   raw YouTube auto-caption VTT, verbatim as downloaded
  text/<date>_<body>.md        de-duplicated, human-readable transcript (ASR-labeled header)
  channel_videos.csv           FULL channel map: every video (740) w/ date,body,tab,duration,id,url
  index.csv                    the retrieved sample (schema below)
  unrecovered.csv              sampled videos with no caption returned (currently empty → not written)
  sample.txt                   the 10 video_ids pulled this run (date body id)
  clean_vtt.py                 VTT rolling-window de-dup -> markdown
  build_index.py               clean all sampled VTTs + build index.csv
  AVAILABILITY.md              channel, ASR-vs-manual, per-year coverage, OpenUtah, Whisper candidates
```

## Channel

- `https://youtube.com/ProvoCityCouncil` → channel ID **`UC1yR7j8igrjxXOR0XsCasfw`**,
  uploads playlist `UU1yR7j8igrjxXOR0XsCasfw`. Meetings are under BOTH `/videos` and
  `/streams` — enumerate both.

## index.csv schema

`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`

- `caption_type` ∈ `manual` / `asr` / `none` — **always `asr` here** (no manual tracks exist).
- `format` ∈ `caption` / `na` — `caption` for every retrieved row.
- `path` is dataset-relative and INCLUDES `raw/` (e.g. `raw/wMfBXiT4zXM.en-orig.vtt`) so the
  validator resolves it.
- `body`: "Municipal Council" (regular, 5:30 PM Tue) vs "Municipal Council Work Meeting"
  (same-day afternoon). Join to `meeting_minutes/all_votes.csv` and `weeks/<tuesday>/` by
  `date` — both share the Tuesday meeting-weekday join key.

## How to (re)build / extend

1. **Enumerate** (already saved to `channel_videos.csv`):
   ```
   yt-dlp --flat-playlist --js-runtimes node -J \
     https://www.youtube.com/channel/UC1yR7j8igrjxXOR0XsCasfw/videos  > videos.json
   yt-dlp --flat-playlist --js-runtimes node -J \
     https://www.youtube.com/channel/UC1yR7j8igrjxXOR0XsCasfw/streams > streams.json
   ```
   (dates parse from the title; `--flat-playlist` returns `upload_date=NA`).
2. **Pull captions** (throttle ≥33s between videos; pause on any bot-check):
   ```
   yt-dlp --write-auto-sub --sub-lang en-orig --sub-format vtt --skip-download \
     --js-runtimes node -o 'raw/%(id)s' <video_url>
   ```
   **Use `--sub-lang en-orig`** (the ASR "Original" track), NOT `en.*` (a machine-translation
   of the ASR). **`--js-runtimes node` is required** — the 2026 YouTube extractor needs a JS
   runtime; Node is present at `/opt/homebrew/bin/node`. (ffmpeg-not-found and impersonation
   warnings are harmless for caption-only pulls.)
3. **Clean + index:** add rows to `sample.txt` then `python3 build_index.py`.

## De-duplication (clean_vtt.py) — important

YouTube ASR VTT uses a **rolling window**: each spoken line appears ~2–3×, once WITH inline
`<HH:MM:SS><c>word</c>` word-timing tags (the freshly-spoken version) and again as plain
context in following cues. `clean_vtt.py` keeps **only the tag-carrying lines**, strips the
tags, HTML-unescapes (`&gt;&gt;` → `>>`, YouTube's speaker-turn marker), and collapses to
~60-word paragraphs; a trailing consecutive-dup pass guards the rare untagged line. This
removes the triplication cleanly — verify a new file's word count is ~1/3 of the raw VTT line
count, not equal to it.

## Caveats

- **ASR word errors** are pervasive on proper nouns — councilor surnames come through as
  "Hoben" (Hoban), "Bogden" (Bogdin), "Hanley/Hamley" (Handley), "McKay" (MacKay). Do NOT
  treat transcript name spellings as roster truth — use `meeting_minutes/` / election results.
- **Not an official record.** Every `text/*.md` is headed with the ASR warning. For votes,
  legal actions, and attributions, the minutes and the source video are authoritative.
- **This is a 10-meeting SAMPLE** (2024–2025). The full ~575-meeting backfill is mapped in
  `channel_videos.csv` and pulls identically. See `AVAILABILITY.md` for per-year coverage,
  the Planning-Commission absence, the OpenUtah robots block, and Whisper candidates.
- **Politeness:** official caption path only (yt-dlp timedtext), ≥33s throttle, no headless
  scraping, no auth. OpenUtah transcript text is `robots.txt`-disallowed for our agent →
  metadata/summary only, never bulk-grabbed.
