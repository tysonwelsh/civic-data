# transcripts/ — build method, caveats, linkage (Draper)

Meeting-video transcripts (source type 5 of `expand-city-sources`). **Additive** — touches
nothing in `meeting_minutes/`, `planning_commission/`, or any other dataset. **Read
`AVAILABILITY.md` first** — platform verdict, caption stats, the 2020–2025 caption gap, and
the Whisper proposals live there.

## What this is (and is NOT)

- **IS:** a sample of **YouTube ASR auto-caption transcripts** (10 meetings, 179,852 words,
  2026-01→2026-04: all 8 mirrored Council meetings + 2 long PC meetings) + the complete
  **video→date maps** for both platforms.
- **IS NOT:** an official record. Every `text/*.md` is headed **"AUTOMATIC TRANSCRIPTION —
  ASR, expect word errors; not an official record."** ASR mis-hears names, case numbers, and
  tallies — for votes/outcomes use `meeting_minutes/` + `db/civic.db`. It is also NOT
  full-corpus: everything before 2026 has video but **no caption track anywhere official**.

## The two-platform picture (the Draper quirk)

1. **Granicus is authoritative but caption-less.** Every meeting 2012→present streams from
   `draper.granicus.com` (MediaPlayer + direct `archive-video.granicus.com` MP4 — same
   `view_id=1` table the minutes came from). Its per-clip `/videos/<clip_id>/captions.vtt`
   endpoint serves a **40-byte empty stub for every clip** (14 probed, 2020→2026, both
   bodies). Full 1,426-clip catalog: `granicus_clips.csv`
   (`name,date,clip_id,duration_s,media_url,mp4_url`).
2. **Captions come only from a third-party mirror** — the "Utah Record - Public Meetings"
   YouTube channel (`UC5hXeD66VUV_w655ionxaSA`), Draper window **2026-01-06 → 2026-04-15**,
   25 unique meetings (`channel_videos.csv`), ASR auto-captions on 23. Many meetings are
   **uploaded twice** (duplicate ID in `index.csv duplicate_video_id`; caption presence can
   differ between twins — PC 2026-03-12's primary upload has none, its twin does). Two
   Council mirror captures (2026-02-03, 2026-03-24) are **shorter than the Granicus clip**
   (see `note`) — prefer the Granicus MP4 for completeness-sensitive work.
3. The city's **own** YouTube channel is promo-only (no meetings). OpenUtah's Draper site is
   robots.txt-disallowed for transcript pages — not used.

## Files

- `index.csv` — one row per unique meeting video (25 rows). SCHEMA_SPEC §9 contract columns
  first: `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,
  extraction_method,path`; then extras `word_count,youtube_duration_s,duplicate_video_id,
  granicus_clip_id,granicus_media_url,granicus_mp4_url,note`.
  - `format` ∈ `caption` (10 fetched) / `na` (15 not fetched).
  - `caption_type` ∈ `asr` (23) / `none` (2 — no track exists on the source).
  - `extraction_method`: `yt-dlp --write-auto-sub …` (fetched) /
    `not_retrieved_sample_policy` (captioned but outside the sample) /
    `no_caption_track_on_source` (the 2 caption-less videos).
  - `body` tokens: `Council`, `PlanningCommission`, `HistoricPreservationCommission`,
    `AppealsVarianceOfficer`, `CommunityEngagementEventsCommittee`,
    `ParksTrailsRecreationCommittee`, `TreeCommittee`.
- `raw/<date>_<body>.en.vtt` — verbatim WebVTT as YouTube served it (never edit); plus
  `raw/_granicus_captions_stub_clip1826.vtt` (evidence of the empty Granicus endpoint) and
  `raw/_fetch_log.csv` (url, bytes, sha256, retrieved date).
- `text/<date>_<body>.md` — cleaned reading copy (rolling-caption dupes collapsed, tags
  stripped) with the ASR header. Built by `clean_vtt.py`.
- `channel_videos.csv` — all 40 Draper uploads on the mirror (incl. duplicates).
- `granicus_clips.csv` — the full Granicus video→date map (the recovery path for Whisper).
- `AVAILABILITY.md` — the availability audit + Whisper proposals.

## How to join by date

`date` (ISO) + `body` join to everything else: `meeting_minutes/all_votes.csv` /
`planning_commission/all_votes.csv`, `weeks/<tuesday>/` bundles (Council), and `db/civic.db`
motions. All 14 Council+PC mirror dates verified present in the minutes indexes. A transcript
gives the verbatim deliberation behind the clerk's summarized minute (Council meets Tuesday,
PC Thursday).

## Extending the sample / recovering more

```bash
# remaining captioned mirror videos (index.csv format=na, caption_type=asr):
yt-dlp --write-auto-sub --sub-langs en --sub-format vtt --skip-download \
  -o 'raw/<date>_<body-slug>' 'https://www.youtube.com/watch?v=<video_id>'
python3 clean_vtt.py raw/<stem>.en.vtt text/<stem>.md <date> '<Body>' <video_id>
```
Then set that row's `format=caption`, `path`, `word_count`, `extraction_method`. If a video
"has no automatic captions", try its `duplicate_video_id` twin before giving up. For
**pre-2026 meetings** the only path is **Whisper on the Granicus MP4** (propose-only —
candidates ranked in `AVAILABILITY.md`); label any output ASR, never as the official record.
