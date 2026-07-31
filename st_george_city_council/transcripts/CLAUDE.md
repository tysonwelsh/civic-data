# transcripts/ — St. George council meeting video transcripts (ASR)

Additive dataset (Source 5 of `expand-city-sources`). **ASR-quality YouTube auto-captions**
of St. George **Utah** City Council meetings, keyed by meeting date so they join to
`meeting_minutes/all_votes.csv`, the minutes, and `weeks/<thursday>/`.

> **These are AUTOMATIC transcriptions.** Every `text/<date>.md` is headed
> "**AUTOMATIC TRANSCRIPTION — ASR quality, expect word errors; NOT an official record.**"
> Names, addresses, ordinance numbers, and cross-talk are frequently mis-heard. The clerk's
> **minutes** (`meeting_minutes/`) are the authoritative record; use transcripts only to read
> the *deliberation* the minutes summarize away.

## Layout

```
raw/<video_id>.en-orig.vtt   raw YouTube ASR caption track, verbatim as downloaded
text/<date>.md               cleaned, de-duplicated transcript (ASR-warning header)
index.csv                    date,title,body,video_url,video_id,caption_type,
                             source_url,retrieved_date,format,extraction_method,path
unrecovered.csv              meetings with video but no retrieved transcript + reason
clean_vtt.py                 .vtt -> cleaned .md (strips tags, collapses rolling captions)
build_transcripts.py         (re)builds index.csv + unrecovered.csv; idempotent
AVAILABILITY.md              channels, ASR-vs-manual, availability-by-year, Whisper candidates
```

## Source

Council meetings are on **YouTube**, split across two channels (see `AVAILABILITY.md`):
Community Education Channel (`UCYqm-7xA_iN8IlX4uX3HtNg`, 2021–mid-2025) and City of St. George
(`UCssI3y3sYbIAySKA8M_8dRw`, mid-2025→present, meetings under `/streams`). **Planning
Commission is not on video** — minutes/PMN only.

## Method

1. **Discover/enumerate** with `yt-dlp --flat-playlist` against each channel's `/streams` +
   playlists (the `/videos` tab is PR clips; the JS-rendered pages can't be WebFetched).
2. **Probe captions** with the yt-dlp Python API (`extract_info`, `automatic_captions` key) —
   more reliable than the CLI, which intermittently drops caption formats when YouTube's JS
   "n-challenge" solver is skipped. A `node` JS runtime is passed as `js_runtimes={'node':{}}`.
3. **Retrieve caption tracks only** (no media):
   `yt-dlp --write-auto-sub --sub-lang en-orig --sub-format vtt --skip-download
   -o 'transcripts/raw/%(id)s' <url>` (official timedtext path; no ToS-violating scraping).
4. **Map video→date** by parsing the meeting date out of the video title.
5. **Clean** each `.vtt` with `clean_vtt.py`: strips `<c>`/`<timestamp>` inline tags and
   collapses YouTube's rolling-caption line duplication into flowing text + the ASR header.
6. **Build** `index.csv`/`unrecovered.csv` with `build_transcripts.py` (idempotent — re-run to
   pick up any captions fetched later).

## index.csv columns

`caption_type` ∈ `asr` (retrieved) / `none` (no ASR track or download blocked) — no `manual`
tracks exist. `format` ∈ `caption` (asr) / `na` (none). `path` (for asr rows) is
dataset-relative **including** `raw/` (e.g. `raw/HvhkphWhCP0.en-orig.vtt`).
`extraction_method` records the yt-dlp+clean_vtt pipeline.

## Join-by-date

`date` is the meeting date (`YYYY-MM-DD`), the same key used across the repo. Join to
`meeting_minutes/all_votes.csv`, minutes markdown, and `weeks/<thursday>/summary.md`. St.
George council meets **1st & 3rd Thursday** (+ work meetings), so most transcript dates land
on the `weeks/` Thursday grid directly.

## Caveats

- **ASR only** — never treat as verbatim; do not extract vote counts or exact names/dollar
  figures from a transcript (use minutes/votes for those).
- **Sparse coverage** — 2023–2024 has almost no captions (Whisper candidates, see
  `AVAILABILITY.md`); 2021–2022 and 2026 are fully captioned.
- **Rate-limit** — heavy enumeration triggers YouTube's bot check; throttle and retry, don't
  hammer. `build_transcripts.py` is safe to re-run.
- **OpenUtah** (`stgeorge.openutah.org`) offers an alternative AI transcript set behind
  `robots.txt Disallow: /api/` — summary/metadata only under the polite rule; not scraped.
