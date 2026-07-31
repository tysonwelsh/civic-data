# transcripts/ — build method, caveats, linkage

Meeting-video transcripts (Source type 5 of `expand-city-sources`). **Additive** — does not
touch `meeting_minutes/`, `planning_commission/`, or any other dataset. **SAMPLE-ONLY**
build (owner decision 2026-07-05): the durable deliverable is the FULL video→date **map**;
only a ~10-meeting representative sample of ASR captions was downloaded.

## What this dataset is (and is NOT)

- A **FULL video→date map** of the "City of Logan" YouTube channel (155 videos) →
  `channel_videos.csv` + `index.csv`, each flagged against `meeting_minutes/minutes_index.csv`.
- A **sample** of **10** recovered ASR caption transcripts (recent Council, 2026-01-20 →
  2026-06-02) in `raw/*.vtt` (verbatim) + `text/*.md` (cleaned).
- **NOT** a full caption backfill, and **NOT** an official record. Every transcript is
  **ASR (YouTube auto-caption) — expect word errors.** The clerk's **minutes** in
  `meeting_minutes/` remain authoritative.

## Files

- `channel_videos.csv` — FULL map, every channel video. Columns:
  `date,video_id,video_url,title,body,minutes_match,caption_sampled`.
  - `minutes_match` ∈ `yes` (date in `minutes_index.csv`) / `no` (dated non-meeting event
    or minutes not yet published) / `nodate` (undated video).
  - `caption_sampled` ∈ `yes` (ASR track downloaded this pass) / `no`.
- `index.csv` — meeting-anchored provenance (undated videos excluded). Columns:
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`.
  - `caption_type` = `asr` (all rows — no manual track exists).
  - `format` = `caption` for the 10 downloaded, `na` for mapped-not-downloaded.
  - `extraction_method` = `yt-dlp_auto_sub_vtt` (downloaded) / `mapped_not_downloaded`.
  - `path` = `text/<date>.md` for downloaded rows, empty otherwise.
- `raw/<date>.vtt` — verbatim YouTube ASR caption track (WEBVTT, inline word timings).
- `raw/_fetch_log.jsonl` — one line per download: `video_url, timedtext_lang, tool,
  raw_path, bytes, sha256, retrieved_utc, chars_cleaned`.
- `text/<date>.md` — cleaned transcript (tags/timestamps stripped, rolling-caption
  duplicates collapsed, HTML entities unescaped), **headed with the ASR caveat**.
- `AVAILABILITY.md` — host, caption type, coverage window + 2020 cutoff, sample rationale,
  Whisper proposals.

## How to recover more transcripts later (the map makes this mechanical)

Pick any `caption_sampled=no` row from `channel_videos.csv`, then:
```
yt-dlp --write-auto-sub --write-sub --sub-format vtt --skip-download \
  --sub-langs "en" -o 'logan_city_council/transcripts/raw/<date>' <video_url>
# → raw/<date>.en.vtt ; rename to raw/<date>.vtt
```
Then re-run the cleaner to emit `text/<date>.md` (strip `<...>` tags + `-->` cue lines,
collapse consecutive duplicate lines, `html.unescape`, prepend the ASR header) and flip the
row's `format`→`caption`, `path`→`text/<date>.md`, `extraction_method`→`yt-dlp_auto_sub_vtt`.
`en` and `en-orig` are identical ASR tracks — keep `en`.

- **Whisper** (only on owner's decision — cost): for the **2020 video gap** (no YouTube
  video that year), the source is **PMN meeting audio** (`.m4a`/`.mp3`). For contested-vote
  and budget/Truth-in-Taxation meetings, see `AVAILABILITY.md`. Label any Whisper output
  identically as ASR.
- Enumerate the channel: `yt-dlp --flat-playlist <channel>/streams` (meetings live under
  `/streams`, not `/videos`). Do **not** WebFetch the `/videos` page — it is JS-rendered.

## How to join by date

`date` (ISO `YYYY-MM-DD`) is the join key to the rest of the repo:
- `meeting_minutes/all_votes.csv` and `meeting_minutes/minutes_index.csv` (meeting date),
- `weeks/<week-ending>/` bundles, `db/logan.db` motions.
A recovered transcript gives the verbatim deliberation behind a summarized minute. `body`
disambiguates non-council events (BudgetWorkshop / TruthInTaxation / Canvass / CandidateForum).
