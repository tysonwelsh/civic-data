# transcripts/ — build method, caveats, linkage

Meeting-video transcripts (Source type 5 of `expand-city-sources`). **Additive** — does not
touch `meeting_minutes/`, `planning_commission/`, or any other dataset. Built **SAMPLE-ONLY**
(owner decision 2026-07-05): the full video→date map is the deliverable; only ~10 caption tracks
were downloaded as a proof-of-concept.

## What this dataset is (and is NOT)

- A **full map of Orem meeting videos → dates** (`channel_videos.csv`, 111 videos, 2016–2025) plus
  a **10-meeting sample of actually-recovered ASR captions** (`raw/*.vtt` + cleaned `text/*.md`).
- Every recovered caption is **ASR / auto-generated** (YouTube `en-orig`): **expect word errors; it
  is NOT the official record.** The clerk's **minutes** in `meeting_minutes/` and
  `planning_commission/` remain authoritative.
- It is **not** a full backfill and it recovers **no** manual/verbatim caption (none exist).

## Files

- `channel_videos.csv` — the full map, EVERY video. Columns:
  `date,body,title,video_id,video_url,playlist,minutes_match`.
  - `date` blank for 3 undated videos (title "NA" / "Election Canvassing" / "City Council Retreat").
  - `minutes_match` ∈ `yes`/`no`/blank — exact join to `minutes_index.csv` (council vs PC by `body`).
- `index.csv` — dataset index, one row per **dated** video (108). Columns:
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path,text_path,note`.
  - `format` = `caption` for the 10 downloaded, `na` for the 98 mapped-but-not-downloaded.
  - `caption_type` = `asr` everywhere (no manual tracks exist).
  - `source_url` = `video_url` = the YouTube watch URL.
  - `path` → retained raw `raw/<key>.vtt` (downloaded rows only); `text_path` → cleaned
    `text/<key>.md`. `<key>` = `<date>` for Council, `<date>_pc` for Planning Commission
    (the `_pc` suffix disambiguates a same-date Council+PC collision in a shared folder).
- `raw/<key>.vtt` — verbatim YouTube ASR caption, exactly as `yt-dlp` wrote it. **Never edit.**
- `text/<key>.md` — cleaned, readable transcript: VTT timestamps/tags stripped, YouTube's rolling
  duplicate lines de-duped, re-wrapped into paragraphs. Headed with the ASR caveat + source video.
- `AVAILABILITY.md` — channels/playlists, caption type, coverage window + cutoffs, undated videos,
  the one removed video, full-backfill path, Whisper proposals.

## How to extend the caption sample (or full backfill) later

`yt-dlp` **is** installed here (unlike Lehi). Per video, the sanctioned path:
```
yt-dlp --write-auto-sub --write-sub --sub-format vtt --skip-download --sub-langs "en-orig,en" \
  -o 'orem_city_council/transcripts/raw/tmp_%(id)s' <youtube_video_url>
# then rename tmp_<id>.en-orig.vtt -> raw/<date>.vtt (add _pc for Planning Commission),
# run the cleaner to emit text/<date>.md headed:
#   "AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official record"
# and flip that index.csv row to format=caption, path=raw/..., text_path=text/...
```
Target the `format=na` rows in `index.csv` (video URLs already there). No Whisper needed for those.

- **Whisper** — only for meetings with **no** YouTube captions (see `AVAILABILITY.md`): the 2020
  gap (Google Drive "Meeting Recordings"), the removed 2025-04-22 video, contested meetings with no
  video. Do NOT run without the owner's decision; label output identically as ASR.
- Do **not** scrape OpenUtah's `/api/` (`robots.txt` disallows it). It was not needed.

## How to join by date

`date` (ISO `YYYY-MM-DD`) is the join key to everything else in the repo:
- `meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv` (meeting date),
- `weeks/<week-ending>/` bundles, `db/orem.db` motions/applications.
`body` (`Council` / `PlanningCommission`) disambiguates same-date meetings of different bodies. A
recovered transcript gives the verbatim deliberation behind a summarized minute — e.g. **2025-05-13**
(sampled) is a contested council meeting where the audio adds the most over the minute.
