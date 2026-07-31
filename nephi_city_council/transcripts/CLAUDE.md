# transcripts/ — build method, caveats, linkage

Meeting-video transcripts (Source type 5 of `expand-city-sources`). **Additive** — does not
touch `meeting_minutes/`, `planning_commission/`, or any other dataset.

## What this dataset is (and is NOT)

- A **video→date map** of every Nephi City YouTube video (both channels), plus **recovered
  ASR captions** for the council meetings that have video.
- Nephi began streaming council meetings only in **May 2026**. Coverage is therefore
  **4 meetings, 2026-05-05 → 2026-06-16** — the tail of the 2020–2026 window. Everything
  earlier has **no published video** (source gap, documented in `AVAILABILITY.md`).
- All recovered text is **ASR / auto-generated: expect word errors; it is NOT the official
  record.** The clerk's minutes in `meeting_minutes/` remain authoritative. (The raw stream
  also captures pre-gavel chit-chat before the meeting is called to order.)

## Files

- `index.csv` — the meeting-video map. Columns:
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path,raw_path,minutes_match`
  - `caption_type` ∈ `asr` / `none`. `format` ∈ `caption` / `na`.
  - 4 rows `format=caption` (retrieved) + 1 row `format=na` (scheduled, not yet aired).
  - `path` → cleaned `text/<date>.md`; `raw_path` → verbatim `raw/<date>.vtt`.
  - `minutes_match` = does a `meeting_minutes/minutes_index.csv` row share this date.
- `channel_videos.csv` — **full inventory of both Nephi channels** (13 videos). Council
  meetings (`is_meeting=true`) on the new channel `UCbTtTpWfekf00N_w-_houEw`; 8 informational
  clips (`is_meeting=false`) on the old channel `UCsX4gp2ARaP6cmTMYFeTiBg`.
- `raw/<date>.vtt` — verbatim YouTube auto-caption download (unmodified; HTML entities kept).
  `raw/_fetch_log.jsonl` — provenance per file (url, bytes, sha256, yt-dlp cmd, retrieved UTC).
- `text/<date>.md` — cleaned sidecar (tags/timestamps stripped, rolling duplication collapsed,
  entities unescaped), headed with the ASR warning.
- `AVAILABILITY.md` — every source checked, the honest gap, and the Whisper (non-)decision.

## How to refresh / recover more later

Council meetings post to the **new** channel. yt-dlp caption recipe that works in this env:

```
yt-dlp --js-runtimes node --extractor-args "youtube:player_client=android" \
  --ignore-no-formats-error --write-auto-sub --sub-format vtt --sub-langs en \
  --skip-download -o 'raw/<date>.%(ext)s' <youtube_video_url>
```

1. Enumerate `https://www.youtube.com/@NephiCity/streams` (meetings are on **/streams**, not
   /videos). Map each video to its meeting date by title; council meets **Tuesdays**.
2. Drop `raw/<date>.vtt`, write cleaned `text/<date>.md` headed
   **"AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official record,"** and add
   an `index.csv` row (`format=caption`, `caption_type=asr`).
3. Re-run the recipe on `_6V__cJJ8XM` (Truth in Taxation) once it airs — it will auto-caption.
4. **Whisper** only on the user's decision, for a high-value *uncaptioned* meeting — none
   exists today (see `AVAILABILITY.md`).

## How to join by date

`date` (ISO `YYYY-MM-DD`) is the join key to the rest of the repo:
- `meeting_minutes/all_votes.csv` (meeting date), `weeks/<tuesday>/` bundles, `db/` tables.
A recovered transcript gives the verbatim deliberation behind a summarized minute. Note Nephi
council minutes are **mostly tally-only** (majority of voters honestly unnamed) — a transcript
can name who actually spoke, but is ASR and must not be treated as an official vote record.
