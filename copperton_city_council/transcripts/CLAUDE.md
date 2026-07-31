# Copperton — transcripts dataset (build + linkage guidance)

**Source type 5** (`expand-city-sources`, **audio-only branch**). Built 2026-07-14.
Additive-only; touches no existing dataset. See `AVAILABILITY.md` for the full platform
verdict, per-year audio inventory, the zero-caption finding, and the Whisper proposal.

## What this dataset is (AUDIO-ONLY inventory — ZERO transcripts)

Copperton (Town of ~800; metro township 2017 → Town 2024-05-01) has **no captioned medium**.
No YouTube channel carries its meetings (every `@Copperton*` handle 404s; the Utah Record
mirror has 0 Copperton — evidence in `raw/_copperton_youtube_probe.txt` +
`raw/_utah_record_channel_titles.txt`); meeting video, where it exists, is a live-only Zoom
hybrid (unarchived). So this dataset is a **link-only inventory** of the per-meeting **audio
files** that Utah Public Notice attaches to:

- **Council** — PMN body **5831**
- **Planning Commission** — PMN body **1560** (MSD-staffed; sparse — most PC meetings cancelled)

**160 rows, 2017 → 2026; 120 live (12.5 GB), 40 purged (404 — pre-~mid-2018 blob rot).** Every
row is `format=na`, `caption_type=none` (audio has no caption track), `whisper_candidate=yes`
for the 120 live files. **Nothing is downloaded** — a documented allowed exception (the bytes
are public + re-fetchable from `audio_url`). Whisper is **proposed, not run** (owner-gated).
Like siblings **Magna** and **White City**, this is pure audio-only — there is **no YouTube
layer at all** (unlike Kearns, which hybridizes YouTube ASR over PMN audio).

## Files
- `index.csv` — SCHEMA_SPEC §9 transcripts contract header
  (`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`)
  + extras (`media_source,audio_url,audio_filename,media_type,pmn_body_id,pmn_file_id,notice_url,size_bytes,http_status,whisper_candidate`).
  **160 rows**, all `media_source=pmn_audio`. The `video_*` contract columns are blank
  throughout (no video source exists).
- `copperton_audio_inventory.csv` — the raw PMN audio→date map (sidecar; `copperton_harvest_audio.py`).
- `copperton_audio_sizes.csv` — HEAD-probe per audio file (`http,content_type,bytes`) — liveness +
  the Whisper cost basis.
- `raw/_probe_5831_list.html`, `raw/_probe_1560_list.html` — the cumulative PMN notice-list
  pages (provenance for the audio harvest).
- `raw/_copperton_youtube_probe.txt` — the YouTube handle-probe evidence (no city channel).
- `raw/_utah_record_channel_titles.txt` — 78 Utah-Record-mirror titles (evidence: 0 Copperton).
- `text/` — **empty by design** (no captions to clean).

## Build / regenerate
```
# 1. (re)fetch the PMN cumulative notice lists into raw/ with a browser UA:
#    /pmn/list/notices.html?id=5831&page=400  -> raw/_probe_5831_list.html
#    /pmn/list/notices.html?id=1560&page=400  -> raw/_probe_1560_list.html
python3 copperton_harvest_audio.py    # raw/_probe_*_list.html -> copperton_audio_inventory.csv
python3 copperton_probe_sizes.py      # HEAD-probe audio URLs  -> copperton_audio_sizes.csv
python3 copperton_build_index.py      # inventory + sizes      -> index.csv
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
Audio is decided by **file extension** (mp3/m4a/wav), **not** the PMN category label. The
meeting date comes from the `MM-DD-YYYY` in the audio filename, falling back to the notice
datetime. **Fetch PMN files from `www.utah.gov/pmn/files/<id>.<ext>`** — the `pmn.utah.gov`
host 302-redirects to the PMN home HTML.

## Linkage
Join to `meeting_minutes/all_votes.csv` / `planning_commission/` and the minutes **by meeting
date** (+ `body`). Audio rows carry `body` ∈ Council / Planning Commission. **Never join by
filename** — recorder-native names and multi-part "Audio N of M" splits carry no reliable key.
Multiple rows can share a date (12 live dates have >1 audio file) — that is expected, not a
duplicate.

## Caveats
- **`caption_type=none` on all 160 rows is a TRUE zero**, not "unrecovered" — Copperton has no
  captioned source. There are **no genuine transcripts** in this dataset today; only the audio
  inventory + Whisper leads.
- **No video anywhere.** Meeting video is a live-only Zoom hybrid; no YouTube/Vimeo/Granicus
  archive exists (verified). Do not assume a video URL — the `video_url`/`video_id` columns are
  intentionally blank.
- **2017 → Nov-2018 audio is purged** (34 dates / 40×404, pre-~mid-2018 PMN blob rot) —
  `whisper_candidate=no`. Note the audio purge boundary runs **later** than the council-minutes
  one: minutes survive from 2018-07-18, but the audio for 2018-07..2018-11 is still 404 (those
  meetings have minutes but no recoverable audio). First live council audio: **2018-12-19**.
  See `meeting_minutes/minutes_unrecovered.csv` for the parallel minutes gap.
- **Whisper is proposed, not run** (owner-gated). If later run on a PMN audio file: write raw
  output to `raw/<date>.<ext>`, a cleaned `text/<date>.md` headed "AUTOMATIC TRANSCRIPTION —
  ASR, expect word errors; not an official record," set that row's `format=caption` /
  `caption_type=asr` / `path=text/<date>.md`, and rerun the validator.
