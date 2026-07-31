# transcripts/ — build method, caveats, linkage

Meeting-video transcripts (Source type 5 of `expand-city-sources`). **Additive** — does not
touch `meeting_minutes/`, `planning_commission/`, or any other dataset.

## What this dataset is (and is NOT)

- A **video→date map** of Lehi council/PC meetings to their YouTube/OpenUtah locations,
  now with **2 of 12 rows carrying recovered caption text** (2026-07-20 backfill).
- **Caption status (2026-07-20):** `2 recovered / 10 unrecovered` of the 12 mapped meetings.
  Recovered = the two 2026 meetings still on YouTube (2026-05-26 Council `GMYzejWyA2U`,
  2026-05-28 Planning Commission `ajch_vFR84k`): English auto-caption (`en-orig`) VTT pulled
  with `yt-dlp`, raw in `raw/<date>.en-orig.vtt`, cleaned sidecar in `text/<date>.md`,
  index rows completed (`format=caption`). The **ten 2025 meetings are an honest gap** — their
  videos are no longer publicly available on YouTube (absent from the "Lehi City" channel
  uploads and its City Council / Planning Commission playlists, which reach back only to
  Dec 2025; absent from the "Lehi City Public Meetings" channel; no hit on targeted yt-dlp
  YouTube search), and OpenUtah exposes no per-video id (transcript behind a
  `robots.txt`-disallowed `/api/`). All ten are ledgered in `unrecovered.csv`. See `AVAILABILITY.md`.
- Any transcript that IS obtained later (via `yt-dlp` or Whisper) is **ASR / AI-generated**:
  **expect word errors; it is NOT the official record.** The clerk's minutes in
  `meeting_minutes/` and `planning_commission/` remain authoritative.

## Files

- `index.csv` — the map. Columns:
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`
  - `caption_type` ∈ `manual` / `asr` / `none` — here all `asr` (YouTube auto-captions /
    OpenUtah AI transcripts).
  - `format` ∈ `caption` / `na` — here all `na` (no caption file retrieved).
  - `extraction_method` = `unrecovered_yt-dlp_absent` for every row this pass.
  - `path` empty (no local caption file). When a transcript is recovered, drop the raw
    `.vtt/.srt` in `raw/<date>.<ext>`, a cleaned `text/<date>.md` sidecar, and set
    `format=caption`, `path=text/<date>.md`, `extraction_method` accordingly.
- `unrecovered.csv` — every mapped-but-unrecovered meeting + the reason.
- `raw/openutah_meeting_page_sample_2025-05-13_council.html` — one retained OpenUtah meeting
  page (evidence of what the mirror exposes: AI summary + metadata, not verbatim transcript).
  `raw/_fetch_log.jsonl` — provenance (url, status, bytes, sha256, retrieved_utc).
- `AVAILABILITY.md` — hosts, caption type, tool gap, mirror coverage, Whisper proposals.

## How to recover transcripts later

1. **Install `yt-dlp`** (the sanctioned path). Then, per meeting video:
   ```
   yt-dlp --write-auto-sub --write-sub --sub-format vtt --skip-download \
     -o 'lehi_city_council/transcripts/raw/%(id)s' <youtube_video_url>
   ```
   Map each video to its meeting date by title, write `text/<date>.md` headed:
   **"AUTOMATIC TRANSCRIPTION — ASR quality, expect word errors; NOT an official record."**
2. **Whisper** (only on user's decision) for high-value meetings in `AVAILABILITY.md`; pull
   the video from the YouTube "Public Meetings" channel or the Granicus clip, transcribe,
   label identically as ASR.
3. Do **not** scrape OpenUtah's `/api/` — `robots.txt` disallows it.

## How to join by date

`date` (ISO `YYYY-MM-DD`) is the join key to everything else in the repo:
- `meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv` (meeting date),
- `weeks/<tuesday>/` bundles (council weekday grid),
- `db/lehi.db` motions/applications.
`body` (`Council` / `PlanningCommission`) disambiguates same-date meetings of different
bodies. A recovered transcript gives the verbatim deliberation behind a summarized minute.
