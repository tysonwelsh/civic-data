# transcripts/ — build method, caveats, linkage

Meeting-video transcripts (Source type 5 of `expand-city-sources`). **Additive** — does not
touch `meeting_minutes/`, `planning_commission/`, or any other dataset. Built **SAMPLE-ONLY**
per owner decision 2026-07-05: full video→date map + a 10-meeting recent ASR caption sample.

## What this dataset is (and is NOT)

- A **full video→date map** of the WVC YouTube channel (WVCTV, `@wvctv2290`) plus a small
  sample of recovered **ASR captions**. The map is the deliverable.
- Recovered captions are **YouTube ASR (automatic speech recognition)** — **expect word
  errors; NOT the official record.** The clerk's **minutes** in `meeting_minutes/` remain
  authoritative. Every `text/*.md` carries that header.

## Files

- **`channel_videos.csv`** — the FULL channel enumeration (1,133 videos, both the `/streams`
  and `/videos` tabs, in + out of window, meetings + non-meetings). Columns:
  `video_id, tab, title, date, date_source, upload_date_raw, is_meeting, body, meeting_kind,
  in_window_2020_2026, minutes_match, video_url`.
  - `date_source` ∈ `title` / `upload_date_snapped` / `upload_date_approx` / `` (see
    AVAILABILITY.md "Date provenance"). `upload_date_snapped` = bare-titled livestream dated
    from its YouTube upload date snapped ±1 day to a minutes date (VOD posts the day after
    the Tuesday meeting).
  - `minutes_match` = exact-date join to `meeting_minutes/minutes_index.csv`.
- **`index.csv`** — the civic dataset index: the **461 in-window (2020–2026) council-family
  meetings** (Council / RDA / BA / HA / study / budget-retreat), one row per video. Columns:
  `date, title, body, video_url, video_id, caption_type, source_url, retrieved_date,
  format, extraction_method, path, meeting_kind, minutes_match, date_source, raw_path`.
  - `caption_type` = `asr` for all (YouTube auto-captions available on the livestreams).
  - `format` ∈ `caption` (10 sampled rows, have files) / `na` (mapped, not fetched).
  - `extraction_method` = `yt-dlp_auto_sub` (sampled) / `mapped_not_fetched` (rest).
  - `path` → cleaned `text/*.md`; `raw_path` → raw `raw/*.en.vtt` (both empty for `na` rows).
- **`raw/<date>_council-regular-meeting.en.vtt`** — the 10 sampled raw ASR VTTs, verbatim.
  `raw/_fetch_log.jsonl` — per-file provenance (video_url, sha256, bytes, word count, recipe,
  retrieved date).
- **`text/<date>_council-regular-meeting.md`** — cleaned running text (VTT tags + timings
  stripped, rolling-window duplicates collapsed), headed with the ASR caveat.
- **`AVAILABILITY.md`** — channels/tabs found, caption type, OpenUtah mirror, coverage +
  cutoff, date provenance, Whisper proposals, what-was-checked.

## How the sample was built

```
# enumerate (both tabs are disjoint — do both):
yt-dlp --flat-playlist --print "%(id)s|%(upload_date)s|%(title)s" \
  "https://www.youtube.com/@wvctv2290/streams"   # and .../videos
# captions (DEFAULT client works on this channel):
yt-dlp --write-auto-sub --write-sub --sub-format vtt --skip-download --sub-langs "en.*" \
  -o 'raw/<date>_council-regular-meeting' "https://www.youtube.com/watch?v=<id>"
```
The android-player-client fallback recipe was NOT needed here.

## How to recover MORE transcripts later

1. Pick rows from `index.csv` where `format=na` (or any `channel_videos.csv` meeting row),
   run the caption recipe above on each `video_url`, then clean to `text/<date>_<slug>.md`
   headed **"AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official record,"**
   and flip that index row to `format=caption` with `path`/`raw_path` filled.
2. **Whisper** (only on the user's decision) for the high-value contested meetings listed in
   `AVAILABILITY.md` — label the output identically as ASR.
3. Do **not** scrape OpenUtah's `/api/` — `robots.txt` disallows it.

## How to join by date

`date` (ISO `YYYY-MM-DD`) is the join key to the rest of the repo:
- `meeting_minutes/all_votes.csv` / `minutes_index.csv` (meeting date; 96% exact match),
- `weeks/<tuesday>/` bundles, `db/` motions/applications.
`body` (`Council` / `RDA` / `BA` / `HA`, or `+`-joined for combined meetings) disambiguates
same-date meetings. A recovered transcript gives the verbatim deliberation behind a
summarized minute — especially the contested votes (WVC is a case-number, high-consensus
council; splits are the signal).
