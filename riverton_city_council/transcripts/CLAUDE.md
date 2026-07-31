# transcripts/ — build method, caveats, linkage (Riverton)

Meeting-video transcripts (source type 5 of `expand-city-sources`). **Additive** — touches
nothing in `meeting_minutes/`, `planning_commission/`, or any other dataset. **Read
`AVAILABILITY.md` first** — platform verdict, the caption-less gap, and the Whisper
proposals live there.

## What this is (and is NOT)

- **IS:** the **one** sanctioned-caption Riverton meeting transcript that exists
  (*City Council, 2018-05-01*, 18,765 words, YouTube ASR) + the **complete Granicus
  video→date map** (`granicus_clips.csv`, 652 clips) that is the Whisper recovery path.
- **IS NOT:** an official record. `text/2018-05-01_city-council.md` is headed **"AUTOMATIC
  TRANSCRIPTION — ASR, expect word errors; not an official record."** ASR mis-hears names,
  case numbers, dollar figures, and tallies — for votes/outcomes use `meeting_minutes/` +
  `db/civic.db`. It is also NOT full-corpus: the whole 2020→present window has video but
  **no caption track anywhere official** (Whisper-only).

## The platform picture (the Riverton quirk)

1. **Granicus is authoritative but caption-less.** Every meeting 2015→present streams from
   `rivertoncity.granicus.com` (`view_id=1` — the same table the minutes came from).
   Its per-clip `/videos/<clip_id>/captions.vtt` serves a **40-byte empty stub for every
   clip** (25 probed, 2015→2026, both bodies; evidence
   `raw/_granicus_captions_stub_clip{811,863}.vtt`). `.srt` 404s. Full 652-clip catalog:
   `granicus_clips.csv` (`name,date,clip_id,duration_s,media_url,downloadfile_url`). The
   `downloadfile_url` 302-redirects to the direct
   `archive-video.granicus.com/rivertoncity/rivertoncity_<guid>.mp4`.
2. **No Utah Record mirror.** Unlike Draper/Sandy/Lehi, the "Utah Record - Public Meetings"
   channel (`UC5hXeD66VUV_w655ionxaSA`) carries **zero** Riverton uploads — so the mirror
   caption route that rescued those cities does not exist here.
3. **The city's own YouTube channel** (`youtube.com/rivertonutahgov`) is promo-only (152
   videos, no `/streams` tab) **except one** archived meeting — *City Council Meeting,
   May 1, 2018* (`aHEL5osaQFk`) — which has YouTube ASR auto-captions. That single track is
   the entire fetched corpus. It maps to Granicus clip **208** (Work Session + Council,
   10,320 s); the YouTube capture (7,375 s) covers the regular-meeting portion only — the
   Granicus MP4 is the fuller recording. **This meeting is below the repo's 2020 data
   floor** — kept as an ASR bonus, not part of the 2020+ record.

## Files

- `index.csv` — SCHEMA_SPEC §9 contract columns first:
  `date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,
  extraction_method,path`; then extras `word_count,youtube_duration_s,granicus_clip_id,
  granicus_media_url,granicus_downloadfile_url,note`. **1 row** (the 2018-05-01 caption).
  - `format` ∈ `caption` (1 fetched).  `caption_type` ∈ `asr`.
  - `extraction_method`: `yt-dlp --write-auto-sub … ; cleaned by clean_vtt.py`.
- `raw/2018-05-01_city-council.en.vtt` — verbatim WebVTT as YouTube served it (never edit).
- `raw/_granicus_captions_stub_clip811.vtt`, `_clip863.vtt` — the 40-byte empty stub the
  Granicus endpoint returns (evidence the captions were never populated).
- `raw/_fetch_log.csv` — url, http_status, bytes, sha256, retrieved_date, path.
- `text/2018-05-01_city-council.md` — cleaned reading copy (rolling-caption dupes collapsed,
  tags stripped) with the ASR header. Built by `clean_vtt.py`.
- `channel_videos.csv` — meeting videos on the official city YouTube channel (the 1 above).
- `granicus_clips.csv` — the full 652-clip Granicus video→date map (the Whisper recovery
  path for the whole caption-less corpus).
- `AVAILABILITY.md` — the availability audit + Whisper proposals.

## How to join by date

`date` (ISO) + `body` join to everything else: `meeting_minutes/all_votes.csv` /
`planning_commission/all_votes.csv`, `weeks/<tuesday>/` bundles (Council meets 1st/3rd
Tuesday; PC 2nd/4th Thursday), and `db/civic.db` motions. A transcript gives the verbatim
deliberation behind the clerk's summarized minute. (The one fetched date, 2018-05-01,
predates the 2020 minutes floor, so it has no minutes row to join.)

## Extending / recovering more

There are **no more sanctioned captions to fetch** — Granicus is stub-only and the mirror
carries no Riverton. The only path to more transcripts is **Whisper on the Granicus MP4s**:

```bash
# resolve the direct MP4 (302), then Whisper it — propose-only, see AVAILABILITY.md
clip=<id from granicus_clips.csv>
curl -sIL "https://rivertoncity.granicus.com/DownloadFile.php?view_id=1&clip_id=$clip" | grep -i location
# whisper output -> save as raw/<date>_<body>.vtt, then:
python3 clean_vtt.py raw/<stem>.vtt text/<stem>.md <date> '<Body>' <clip> 'Granicus clip <clip> (Whisper ASR)'
```
Label any Whisper output ASR with the standard header; never treat as the official record.
