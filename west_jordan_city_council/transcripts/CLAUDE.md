# transcripts/ — build & linkage notes

**Dataset:** ASR (automatic-speech-recognition) caption tracks of West Jordan City Council
and Planning Commission meetings, pulled from the city's official YouTube channel.
**As-of:** 2026-07-03. **Additive only** — does not touch `meeting_minutes/`, `db/`, etc.

## What this is (and is NOT)
Every file here is a machine transcript. The `en-orig` track is **YouTube automatic
captions** — verbatim-ish but **word-error-prone** (proper nouns, ordinance numbers,
crosstalk, and dollar amounts are frequently wrong). Every cleaned `text/*.md` is headed
with the mandatory banner:

> **AUTOMATIC TRANSCRIPTION — ASR quality, expect word errors; NOT an official record.**

The authoritative record is `meeting_minutes/` (clerk PDFs). Use transcripts to recover the
*deliberation* the minutes summarize away — not for exact quotes, numbers, or votes.

## Source
- **Channel:** West Jordan City — `https://www.youtube.com/channel/UC7Up4AfoWj0KebppgTvnLSg`
  (vanity `https://bit.ly/WestJordan`).
- Meeting videos live under **two tabs**: `/streams` (live-streamed meetings, 2017→Apr 2023)
  and `/videos` (uploaded meetings mixed with promo content, ~mid-2023→**Feb 4 2025**).
  **After 2025-02-04 the city stopped posting meetings to YouTube** and publishes video only
  via Swagit / the OpenUtah mirror — so YouTube captions are unavailable for meetings after
  that date. See `AVAILABILITY.md`.

## How the caption tracks were pulled
`yt-dlp` 2026.06.09 (installed at `/Users/tysonwelsh/anaconda3/bin/yt-dlp`; `pip install -U
yt-dlp` reported already-current). A JS runtime is required for the current YouTube
extractor — Node v23 is present and passed via `--js-runtimes node`.

```
yt-dlp --js-runtimes node --write-auto-sub --sub-lang en-orig --sub-format vtt \
       --skip-download -o 'raw/%(id)s' <video_url>
```

- **`--sub-lang en-orig`** (English *Original*), NOT `en` — `en` is YouTube's machine
  *translation* of the original track and is lower quality. Both exist on these videos; we
  keep the original ASR.
- Downloads were spaced **≥33 s apart** to stay under YouTube's bot-check; ~25 total probes
  this run (well under the ~100 throttle threshold). No rate-limit block hit.
- Channel/video enumeration via `yt-dlp --flat-playlist` against the `/streams` and `/videos`
  tab URLs (those tabs are JS-rendered — a plain WebFetch sees only the footer).

## Cleaning (`clean_vtt.py`)
YouTube auto-caption VTT uses a rolling 2-line window (each cue repeats the previous line
plus one new line) with inline `<timestamp><c>` word-timing tags, so naive extraction
triples every line. `clean_vtt.py`:
- strips the WEBVTT header, cue-timing lines, and all `<...>` inline tags;
- collapses rolling duplicates to one ordered stream of unique lines (4-line lookback);
- **does not alter wording** — ASR errors are preserved verbatim (extraction discipline;
  implausibly clean text would be a hallucination signal).

Re-run: `python3 clean_vtt.py raw/<id>.en-orig.vtt text/<date>_<body>.md <date> "<Label>" <url> <id>`

## index.csv schema
`date, title, body, video_url, video_id, caption_type, source_url, retrieved_date, format,
extraction_method, path, text_path, raw_bytes`
- `caption_type` ∈ `manual` / `asr` / `none` — all rows here are **`asr`** (no
  human-uploaded caption tracks were found on any WJ meeting video).
- `format` = `caption` for retrieved rows.
- `body` ∈ `council` / `planning_commission`.
- `path` is dataset-relative and **includes `raw/`** (e.g. `raw/pdEd-AGK5SQ.en-orig.vtt`) so
  the validator resolves it; `text_path` points at the cleaned markdown.

## channel_videos.csv — the full video→date universe
`channel_videos.csv` is the complete `yt-dlp --flat-playlist` enumeration of **both** channel
tabs (647 rows: `video_id, title, channel_tab` ∈ streams/videos, `title_date_raw`,
`video_url`). It is the map for extending this sample: filter titles to "City Council" /
"Planning Commission", parse the date, and re-run the caption pull (recipe above). Not every
row has captions — older years are spotty (see `AVAILABILITY.md`); confirm per-video with
`--list-subs`.

## Linkage to existing data
Join to `meeting_minutes/` and `all_votes.csv` by **`date` + `body`**. West Jordan council
meets 2nd & 4th Tuesdays; Planning Commission on the intervening weeks — so a transcript
date maps 1:1 to a minutes date. A same-day "Committee of the Whole" work session is a
*separate* video (not pulled in this sample) and would key to the same date with a distinct
body label if added.

## Provenance
`raw/*.en-orig.vtt` are the untouched caption files. `raw/_fetch_log.jsonl` records url,
source video page, byte count, and **sha256** per file (built manually — the fetch went
through `yt-dlp`, not `polite_fetch.py`, because caption retrieval needs the yt-dlp
timedtext path). `screen_corpus.py` on `text/` was clean (dict_ratio ~0.86, zero mojibake /
artifacts; only the advisory "ends_mid" flag, expected because caption tracks stop when the
stream ends).

## Whisper
`AVAILABILITY.md` *proposes* high-value untranscribed meetings for Whisper. **Whisper was
NOT run** — it is expensive and the user decides.
