# Sandy transcripts/ — meeting-video ASR captions

Additive dataset: **automatic-speech-recognition (ASR) caption tracks** for Sandy City
public-meeting videos, 2025-01-14 → 2026-06-23 (plus one 2022 no-caption video). Built by the
`expand-city-sources` skill (meeting-video transcripts source type). **Read `AVAILABILITY.md`
first** — it has the channel map, the coverage window, the 2020–2024 hole, and the Whisper
proposals.

## What this is / is NOT
- **IS**: a searchable, verbatim-*ish* record of what was *spoken* in the room — public
  comment, deliberation, staff presentations — that minutes paraphrase or drop.
- **IS NOT**: an official record, and **not** a votes/decisions source. ASR mis-hears names,
  numbers, and jargon. For rulings/tallies use `meeting_minutes/` + `db/sandy.db`. Every
  cleaned text file is headed `AUTOMATIC TRANSCRIPTION — ASR, expect word errors…`.

## Layout
```
raw/<date>_<body>.vtt   verbatim WebVTT exactly as YouTube served it (NEVER edit). Retains
                        YouTube's rolling-caption duplication and &gt;&gt; speaker markers.
text/<date>_<body>.md   cleaned reading copy: timestamps/markup stripped, rolling dupes
                        collapsed, HTML entities decoded (&gt;&gt; -> >>). ASR header on top.
index.csv               one row per VIDEO (not per meeting).
AVAILABILITY.md         coverage audit + Whisper proposals.
```
Filename stem is `<meeting-date>_<body-slug>` (`city-council` / `planning-commission` /
`board-of-adjustment`). A `-<vidid6>` suffix disambiguates a second video for the same
date+body (city re-uploads).

## index.csv columns
`date` (meeting date), `title` (verbatim video title), `source_url`, `retrieved_date`,
`format` (`caption` = track retrieved; `na` = no caption track exists), `extraction_method`,
`video_url`, `video_id`, `caption_type` (`asr` for all present rows; no `manual` tracks exist),
`body`, `word_count`, `path` (dataset-relative, includes `raw/`; empty for `na` rows).

## Provenance / source
- Videos live on the **Utah Record – Public Meetings** YouTube channel
  (`UC5hXeD66VUV_w655ionxaSA`), "Sandy City Meetings" playlist
  `PL6IaTceX1fg_4lrLVY7l8v5PX6Sf7u4pT`, and are indexed by **OpenUtah**
  (`sandy.openutah.org`). OpenUtah's `/api/` transcript text is `robots.txt`-disallowed and was
  **not** scraped — it was used only to discover the meeting→video mapping. Captions come from
  YouTube's official `timedtext` track via `yt-dlp`, not from OpenUtah.

## Reproduce
```bash
python3 -m pip install yt-dlp
# enumerate:
yt-dlp --flat-playlist --print "%(id)s|%(title)s" \
  "https://www.youtube.com/playlist?list=PL6IaTceX1fg_4lrLVY7l8v5PX6Sf7u4pT"
# captions for one video:
yt-dlp --write-auto-sub --write-sub --sub-format vtt --skip-download \
  --sub-langs "en.*" "https://www.youtube.com/watch?v=<VIDEO_ID>"
```
`date`/`body` are parsed from the title (`… on YYYY-MM-DD …` > leading `Month DD, YYYY` >
trailing date). Council meets **Tuesday**; validate dates against
`meeting_minutes/minutes_index.csv`.

## Caveats (see AVAILABILITY.md for full detail)
- **Hard source cutoff 2025-01**: no Sandy meeting video exists before then (215 of 274 minutes
  meetings, all 2020–2024, are un-transcribable). The lone 2022 council video has no captions.
- **All captions are ASR**; zero manual tracks. Expect word errors, especially names/numbers.
- `word- word` fragments in the text (e.g. "develop- development") are **verbatim speaker
  false-starts/self-corrections from the ASR**, not a cleaning bug — retained faithfully.
- Some texts **end mid-sentence** (video/caption cut short) — advisory, expected.
- Additive only: this dataset never modifies minutes, votes, comments, elections, or `db/`.
