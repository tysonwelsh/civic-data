# transcripts/ — build method, caveats, linkage

Meeting-video transcripts (Source type 5 of `expand-city-sources`) for **Salt Lake City**.
**Additive** — does not touch `meeting_minutes/`, `planning_commission/`, `public_comments/`,
or any other dataset. Built 2026-07-05.

## What this dataset is (and is NOT)

- A **complete video→date map** (`channel_videos.csv`, 1,142 videos) of every meeting on the
  city's **SLC Live Meetings** YouTube channel, mapped to `meeting_minutes/minutes_index.csv`
  dates via a `minutes_match` flag.
- A **~10-meeting ASR caption sample** (`index.csv` + `raw/` + `text/`) — the SAMPLE-ONLY
  owner decision (2026-07-05). This is a *taste*, not the full corpus. See `AVAILABILITY.md`.
- All recovered text is **YouTube auto-caption (ASR) quality**: **expect word errors; it is
  NOT the official record.** The clerk's minutes in `meeting_minutes/` remain authoritative.
  Every `text/*.md` file carries this header.

## Files

- `channel_videos.csv` — the **full map**. Columns:
  `date,title,body,video_id,video_url,playlist,minutes_match`.
  - `date` parsed from the YouTube title (blank = undated pre-2017 upload).
  - `body` ∈ `Council` (Council + RDA/CRA/LBA, interleaved as they are in the minutes) /
    `PlanningCommission` / `PlanningDivision` / `Other`.
  - `playlist` ∈ `streams` / `videos` (which channel tab the id came from; the two are disjoint).
  - `minutes_match` = `true` when `date` is present in `meeting_minutes/minutes_index.csv`.
- `index.csv` — provenance for the **retrieved sample** (10 rows). Columns:
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,`
  `extraction_method,path,raw_path,minutes_match`.
  - `format` = `caption` (all sample rows retrieved); `caption_type` = `asr`.
  - `path` → `text/<date>_<slug>.md` (cleaned); `raw_path` → `raw/<date>_<slug>.vtt` (verbatim).
- `raw/<date>_<slug>.vtt` — verbatim WebVTT auto-captions, retained unmodified.
  `raw/_fetch_log.jsonl` — one JSON line per fetch: `video_id, url, date, title, raw_path,
  bytes, sha256, status, retrieved_utc, tool, sub_lang, caption_type`. **Trust only files
  listed here** (freshly downloaded + sha256-verified in this build).
- `text/<date>_<slug>.md` — cleaned readable transcript (timestamps/cue tags stripped, HTML
  entities unescaped, rolling-repeat de-duplicated), headed with the ASR disclaimer.
- `AVAILABILITY.md` — channels/platforms, full map stats, coverage window, Whisper proposals.

Filenames use `<date>_<slug>` (not bare `<date>`) because the SLC Council series interleaves
several bodies on one date (e.g. 2026-06-09 has a Formal, a Work Session, and a CRA video).

## How to recover more transcripts (the working recipe)

`yt-dlp` (2026.06.09) + `node` are installed. Per video from `channel_videos.csv`:

```
yt-dlp --js-runtimes node --extractor-args "youtube:player_client=android" \
  --ignore-no-formats-error --write-auto-sub --sub-format vtt --skip-download \
  --sub-langs en -o 'raw/<date>_<slug>' 'https://www.youtube.com/watch?v=<video_id>'
```

Then clean `raw/<name>.en.vtt` → `text/<name>.md` (strip `<...>` cue tags, `html.unescape`,
drop WEBVTT/timing lines, de-dup consecutive repeats), prepend the ASR header, append a row
to `index.csv`, and log to `raw/_fetch_log.jsonl` with the sha256. The build scripts used
this pass are in the session scratchpad (`slc_build_map.py`, `slc_fetch_sample.py`).

Enumerate/refresh the map:
`yt-dlp --flat-playlist --print "%(id)s|%(title)s|%(upload_date)s" <channel>/streams` (and
`/videos` — union them; they don't overlap).

**Whisper:** do NOT run by default (owner decides). Candidates in `AVAILABILITY.md`.

## How to join by date

`date` (ISO `YYYY-MM-DD`) is the join key to the rest of the repo:
- `meeting_minutes/minutes_index.csv` and `meeting_minutes/all_votes.csv` (meeting date),
- `weeks/<week-ending>/` bundles, `db/slc.db` motions/votes,
- SLC's Council adjourns/reconvenes in-session as RDA/CRA/LBA — those appear as separate
  videos here (`body=Council`), matching how the minutes `body` column walks section headers.
`body` disambiguates same-date meetings of different bodies; for same-date same-body videos,
use the `slug` in the filename / the `title`.
