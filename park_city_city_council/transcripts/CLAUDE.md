# transcripts/ — Park City meeting-video map (additive dataset)

Built by `expand-city-sources` (meeting-video transcripts type), 2026-07-05. **Additive
only** — nothing here overwrites the canonical minutes/votes layer.

## What this is (and isn't)

A **video→date map**, not a transcript corpus. Park City records meetings but publishes
**no captions of any kind**, so there is nothing to extract without ASR. Read
`AVAILABILITY.md` first — it documents every source checked and the decisive finding.

- **Video source:** CivicClerk (same portal as the minutes). Recordings are MP4s on
  `https://cpmedia.azureedge.net/parkcityut/<hash>.mp4`, surfaced via the OData feed
  `https://parkcityut.api.civicclerk.com/v1/Events` (fields `mediaSourcePathMp4` /
  `mediaStreamPath`). **NOT** YouTube (the city YT channel has 0 meetings) and **NOT**
  Swagit (dead).
- **Captions:** none. `closedCaption*` and `youtubeVideoId` are empty on all 2,250 events.
- **Coverage:** 194 videos, **2023-09-27 → 2026-07-01 only** — no video before Sept 2023.

## Files

- `channel_videos.csv` — **the full map** (194 rows). Columns: `date, body, title,
  event_id, video_url, video_id, portal_url, caption_type(=none), minutes_match`.
  `minutes_match=true` ⇔ `date` equals a row in `../meeting_minutes/minutes_index.csv`
  (Council only; 85/88 Council videos match; PC/HPB/BOA/Appeal are other bodies).
- `index.csv` — provenance index, same 194 videos. Columns (§9 transcripts contract):
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,
  extraction_method,path`. `format=na`, `extraction_method=none`
  because no caption artifact was retrieved (video-only source).
- `raw/_fetch_log.jsonl` — machine-readable provenance of the investigation (channel
  enumeration, Swagit/CivicClerk probes, caption-absence verification on a sampled MP4).
  `raw/` holds no media: full MP4s were **not** downloaded (sample-only, no ASR).
- `text/` — empty. No transcripts exist until a Whisper pass is run.
- `AVAILABILITY.md` — sources checked, coverage window/cutoff, Whisper candidates.

## To transcribe later (Whisper — proposed, not run)

Pick a row from `channel_videos.csv`, download `video_url`, run Whisper, and write
`raw/<date>.vtt` + `text/<date>.md` **headed**:
`AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official record`.
Start with the 3 newest Council meetings that have **no minutes yet** (2026-06-04/-11/-25,
event_id 3929/3930/3931) — for those, video is the only record. This map stays valid; ASR
outputs are purely additive to it.

## Refresh

Re-run the CivicClerk `Events` harvest (paged via `@odata.nextLink`, page size 15), keep
rows with a real `mediaSourcePathMp4`, re-match dates to `minutes_index.csv`. New meetings
appear as MP4s within days; captions are not expected to appear (city has never published
any). Do not hand-edit these CSVs.
