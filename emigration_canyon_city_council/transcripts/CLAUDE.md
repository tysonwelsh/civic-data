# Emigration Canyon — transcripts dataset (build + linkage guidance)

**Source type 5** (`expand-city-sources`, **audio-only branch**). Built 2026-07-14.
Additive-only; touches no existing dataset. See `AVAILABILITY.md` for the full platform
verdict, per-year audio inventory, the zero-caption finding, and the Whisper proposal.

## What this dataset is (AUDIO-ONLY inventory — ZERO transcripts)

Emigration Canyon (~1,600 pop; metro township 2017 → City 2024-05-01) has **no captioned
medium**. No government YouTube channel carries its meetings — every plausible
`@EmigrationCanyon*` handle 404s except `@emigrationcanyon`, which is a **name-collision
DECOY** (a personal account with 3 piano videos from 2009); the Utah Record mirror has 0
Emigration uploads — evidence in `raw/_emig_youtube_probe.txt`, `raw/_emig_channel_videos.txt`,
`raw/_utah_record_channel_titles.txt`. Meeting video, where it exists, is a live-only
Zoom/virtual hybrid (unarchived). So this dataset is a **link-only inventory** of the
per-meeting **audio files** that Utah Public Notice attaches to:

- **Council** — PMN body **5809**
- **Planning Commission** — PMN body **1562** (MSD-staffed; its own PC — recon §3)

**244 rows, 2017 → 2026; 211 live (21.29 GB), 33 purged (404 — pre-~mid-2018 blob rot).**
Every row is `format=na`, `caption_type=none` (audio has no caption track),
`whisper_candidate=yes` for the 211 live files. **Nothing is downloaded** — a documented
allowed exception (the bytes are public + re-fetchable from `audio_url`). Whisper is
**proposed, not run** (owner-gated). Like siblings **Copperton / Magna / White City**, this is
pure audio-only — there is **no YouTube layer at all** (unlike Kearns, which hybridizes
YouTube ASR over PMN audio).

## Files
- `index.csv` — SCHEMA_SPEC §9 transcripts contract header
  (`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`)
  + extras (`media_source,audio_url,audio_filename,media_type,pmn_body_id,pmn_file_id,notice_url,size_bytes,http_status,whisper_candidate`).
  **244 rows**, all `media_source=pmn_audio`. The `video_*` contract columns are blank
  throughout (no video source exists).
- `emig_audio_inventory.csv` — the raw PMN audio→date map (sidecar; `emig_harvest_audio.py`).
- `emig_audio_sizes.csv` — HEAD-probe per audio file (`http,content_type,bytes`) — liveness +
  the Whisper cost basis.
- `raw/_probe_5809_list.html`, `raw/_probe_1562_list.html` — the cumulative PMN notice-list
  pages (provenance for the audio harvest).
- `raw/_emig_youtube_probe.txt` — the YouTube handle-probe evidence (no government channel;
  `@emigrationcanyon` is a personal decoy).
- `raw/_emig_channel_videos.txt` — the 3 decoy videos on `@emigrationcanyon` (evidence).
- `raw/_utah_record_channel_titles.txt` — 78 Utah-Record-mirror titles (evidence: 0 Emigration).
- `text/` — **empty by design** (no captions to clean).

## Build / regenerate
```
# 1. (re)fetch the PMN cumulative notice lists into raw/ with a browser UA:
#    /pmn/list/notices.html?id=5809&page=400  -> raw/_probe_5809_list.html   (the &page=N form
#    /pmn/list/notices.html?id=1562&page=400  -> raw/_probe_1562_list.html    is REQUIRED; bare ?id= 500s)
python3 emig_harvest_audio.py    # raw/_probe_*_list.html -> emig_audio_inventory.csv
python3 emig_probe_sizes.py      # HEAD-probe audio URLs  -> emig_audio_sizes.csv
python3 emig_build_index.py      # inventory + sizes      -> index.csv
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
Audio is decided by **file extension** (mp3/m4a/wav — Emigration Canyon uses UPPERCASE `.MP3`;
case-insensitive), **not** the PMN category label. The meeting date comes from the
`MM-DD-YYYY` in the audio filename, falling back to the notice datetime. **Fetch PMN files from
`www.utah.gov/pmn/files/<id>.<ext>`** — the `pmn.utah.gov` host 302-redirects to the PMN home
HTML.

## Linkage
Join to `meeting_minutes/all_votes.csv` / `planning_commission/` and the minutes **by meeting
date** (+ `body`). Audio rows carry `body` ∈ Council / Planning Commission. **Never join by
filename** — recorder-native names and multi-part "Audio N of M" splits carry no reliable key.
**43 live dates carry more than one audio file** (council 25, PC 18) — that is expected, not a
duplicate.

## Caveats
- **`caption_type=none` on all 244 rows is a TRUE zero**, not "unrecovered" — Emigration
  Canyon has no captioned source. There are **no genuine transcripts** in this dataset today;
  only the audio inventory + Whisper leads.
- **No video anywhere.** Meeting video is a live-only Zoom/virtual hybrid; no
  YouTube/Vimeo/Granicus archive exists (verified). Do not assume a video URL — the
  `video_url`/`video_id` columns are intentionally blank.
- **2017 → 2018 audio is purged** (30 dates / 33×404, pre-~mid-2018 PMN blob rot; last purged
  date 2018-12-19) — `whisper_candidate=no`. First live audio: **council 2019-01-24, PC
  2019-07-17.** This parallels the township-era minutes purge in
  `meeting_minutes/minutes_unrecovered.csv`.
- **Whisper is proposed, not run** (owner-gated). If later run on a PMN audio file: write raw
  output to `raw/<date>.<ext>`, a cleaned `text/<date>.md` headed "AUTOMATIC TRANSCRIPTION —
  ASR, expect word errors; not an official record," set that row's `format=caption` /
  `caption_type=asr` / `path=text/<date>.md`, and rerun the validator.
