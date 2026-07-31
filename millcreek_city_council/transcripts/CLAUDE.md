# transcripts/ — Millcreek meeting-video ASR captions (expand-sources #5)

Additive dataset: YouTube ASR caption tracks for Millcreek City Council & Planning
Commission meeting videos. **Built SAMPLE-ONLY by owner policy** — the full channel is
mapped in `index.csv`; only 10 caption tracks are stored on disk. Never modifies the
existing `meeting_minutes/` / `planning_commission/` layers. See `AVAILABILITY.md` for the
source verdict; this file is the build/linkage detail.

## Source

- **Meeting video:** the third-party mirror **`@UtahRecord`** ("Utah Record - Public
  Meetings"), playlist **"Millcreek City Meetings"**
  `https://www.youtube.com/playlist?list=PL6IaTceX1fg-0pvUGP_x4hs-qhgd23d6-`. Same operator
  as `millcreek.openutah.org` (the searchable transcript front-end; its meeting pages embed
  these YouTube IDs). **The city's own YouTube (`@millcreekutah3408`) is PR-only** and has no
  meeting video — do not look there.
- **Coverage:** 2025-01-06 → 2026-06-22 · 92 videos (58 Council + 34 PC). ASR auto-captions
  only. This is the entire video record; the pre-2025 record is minutes-PDF only.

## Build

1. Map the playlist (video→date):
   ```
   python3 -m yt_dlp --flat-playlist --print "%(id)s | %(title)s" \
     "https://www.youtube.com/playlist?list=PL6IaTceX1fg-0pvUGP_x4hs-qhgd23d6-"
   ```
   Parse the meeting date + body straight from each title
   ("Millcreek City Council - Millcreek City - YYYY-MM-DD") → `index.csv`.
2. Retrieve a sample caption (per video):
   ```
   python3 -m yt_dlp --skip-download --write-auto-sub --sub-lang en-orig \
     --sub-format vtt -o "<date>_<body>_<video_id>.%(ext)s" \
     "https://www.youtube.com/watch?v=<video_id>"
   ```
   → `raw/<date>_<body>_<video_id>.en-orig.vtt`.
3. Clean vtt → `text/<date>_<body>_<video_id>.md`: strip `WEBVTT`/`Kind:`/`Language:`
   headers, `-->` timestamp cues, inline `<...>` timing/color tags; HTML-unescape entities
   (`&gt;&gt;` → `>>` speaker markers); drop YouTube's rolling-caption duplicate/prefix
   lines. Each file is headed with the **"AUTOMATIC TRANSCRIPTION — ASR …"** disclaimer.
   (Build scripts were run from the session scratchpad; re-derivable from the two yt-dlp
   commands above + the cleaner logic here.)
4. Provenance: `raw/_fetch_log.jsonl` — one row per retrieved vtt (url, tool, http_status,
   bytes, sha256, caption_type, retrieved_utc, saved_as).

Retrieving the remaining 82 videos later = re-run step 2/3 for those rows and flip
`stored_locally` to `yes` + fill `path`/`text_path`. Idempotent (yt-dlp skips existing files
per output template).

## index.csv schema

`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,
extraction_method,path,source,stored_locally,text_path`

- Required minimum cols present: `date,title,source_url,retrieved_date,format,extraction_method`.
- `format` = `caption` (all rows). `caption_type` = `asr` (all rows — no manual tracks exist).
- `body` = the mirror's title label (`CityCouncil` / `PlanningCommission`) — **not a verified
  body.** The council also sits as CRA / URCA; e.g. the 2026-06-01 "CityCouncil" video is
  actually a URCA board meeting. Verify against the matching minutes doc before joining.
- `stored_locally` = `yes` for the 10 samples (with `path` = raw vtt, `text_path` = cleaned
  md), `no` for the other 82 (link-only rows — the video/caption is re-fetchable via
  `video_url`). This link-only-for-most posture is the **documented sample-only exception** to
  "retain every raw original" (owner policy; files are public + re-fetchable).

## Linkage to the existing data

Join to `meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv` and the
`weeks/` bundles **by meeting date** (council = Monday grid; PC = its own Wednesday date).
The ASR transcript is **contextual/color only** — it captures the spoken deliberation the
clerk's minutes summarize away. **Never extract votes, tallies, or verbatim member quotes
from ASR text**; the authoritative vote record is the minutes layer. Same-day council work +
regular sessions produce two rows/videos for one date — expected, not a duplicate defect.

## Validate

```
python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py \
  millcreek_city_council/transcripts        # PASS
python3 .claude/skills/audit-city-data/scripts/screen_corpus.py \
  millcreek_city_council/transcripts/text   # clean; dict_ratio ~0.855 (normal for ASR)
```
