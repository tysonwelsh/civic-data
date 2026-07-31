# Magna — transcripts dataset (build + linkage guidance)

**Source type 5** (`expand-city-sources`, **audio-only branch**). Built 2026-07-13.
Additive-only; touches no existing dataset. See `AVAILABILITY.md` for the full platform
verdict, per-year audio inventory, the zero-caption finding, and the Whisper proposal.

## What this dataset is (AUDIO-ONLY inventory — ZERO transcripts)

Magna has **no captioned medium**. Meeting VIDEO is a live-only Zoom webinar (unarchived),
and **no YouTube channel carries Magna meetings** (`@MagnaCity` is empty; `@MagnaUtah` /
`@magnautah` are a Cyprus High School decoy; Utah Record mirror has 0 Magna — evidence in
`raw/_magna_youtube_probe.txt` + `raw/_utah_record_channel_titles.txt`). So this dataset is a
**link-only inventory** of the per-meeting **audio MP3s** that Utah Public Notice attaches to:

- **Council** — PMN body **5803**
- **Planning Commission** — PMN body **1559** (MSD-staffed)

**457 rows, 2016 → 2026; 370 live (26.5 GB), 87 purged (404 — pre-~2018 blob rot).** Every row
is `format=na`, `caption_type=none` (audio has no caption track), `whisper_candidate=yes` for
the 370 live files. **Nothing is downloaded** — a documented allowed exception (the bytes are
public + re-fetchable from `audio_url`). Whisper is **proposed, not run** (owner-gated). Unlike
sibling **Kearns** (a HYBRID: YouTube ASR captions layered over PMN audio), Magna has **no
YouTube layer at all** — it is pure audio-only, like White City.

## Files
- `index.csv` — SCHEMA_SPEC §9 transcripts contract header
  (`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`)
  + extras (`media_source,audio_url,audio_filename,media_type,pmn_body_id,pmn_file_id,notice_url,size_bytes,http_status,whisper_candidate`).
  **457 rows**, all `media_source=pmn_audio`. The `video_*` contract columns are blank
  throughout (no video source exists).
- `magna_audio_inventory.csv` — the raw PMN audio→date map (sidecar; `magna_harvest_audio.py`).
- `magna_audio_sizes.csv` — HEAD-probe per audio file (`http,content_type,bytes`) — liveness +
  the Whisper cost basis.
- `raw/_probe_5803_list.html`, `raw/_probe_1559_list.html` — the cumulative PMN notice-list
  pages (provenance for the audio harvest).
- `raw/_magna_youtube_probe.txt` — the YouTube handle-probe evidence (no city channel).
- `raw/_utah_record_channel_titles.txt` — 78 Utah-Record-mirror titles (evidence: 0 Magna).
- `text/` — **empty by design** (no captions to clean).

## Build / regenerate
```
# 1. (re)fetch the PMN cumulative notice lists into raw/ with a browser UA:
#    /pmn/list/notices.html?id=5803&page=400  -> raw/_probe_5803_list.html
#    /pmn/list/notices.html?id=1559&page=400  -> raw/_probe_1559_list.html
python3 magna_harvest_audio.py    # raw/_probe_*_list.html -> magna_audio_inventory.csv
python3 magna_probe_sizes.py      # HEAD-probe audio URLs  -> magna_audio_sizes.csv
python3 magna_build_index.py      # inventory + sizes      -> index.csv
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
Audio is decided by **file extension** (mp3/m4a/wav), **not** the PMN `(Audio Recording)`
category label (some notices mis-file a PDF under it). The meeting date comes from the
`MM-DD-YYYY` in the audio filename, falling back to the notice datetime. **Fetch PMN files from
`www.utah.gov/pmn/files/<id>.<ext>`** — the `pmn.utah.gov` host 302-redirects to the PMN home
HTML.

## Linkage
Join to `meeting_minutes/all_votes.csv` / `planning_commission/` and the minutes **by meeting
date** (+ `body`). Audio rows carry `body` ∈ Council / Planning Commission. **Never join by
filename** — recorder-native MP3 names and multi-part "Audio N of M" splits carry no reliable
key. Multiple rows can share a date (multi-part audio) — that is expected, not a duplicate.

## Caveats
- **`caption_type=none` on all 457 rows is a TRUE zero**, not "unrecovered" — Magna has no
  captioned source. There are **no genuine transcripts** in this dataset today; only the audio
  inventory + Whisper leads.
- **No video anywhere.** Meeting video is a live-only Zoom webinar; no YouTube/Vimeo/Granicus
  archive exists (verified). Do not assume a video URL — the `video_url`/`video_id` columns are
  intentionally blank.
- **2016–2018 audio is purged** (87×404, pre-~2019 PMN blob rot) — `whisper_candidate=no`. Those
  meetings' record lives in `meeting_minutes/` (many also 404-purged there — see
  `meeting_minutes/minutes_unrecovered.csv`).
- **Whisper is proposed, not run** (owner-gated). If later run on a PMN audio file: write raw
  output to `raw/<date>.<ext>`, a cleaned `text/<date>.md` headed "AUTOMATIC TRANSCRIPTION —
  ASR, expect word errors; not an official record," set that row's `format=caption` /
  `caption_type=asr` / `path=text/<date>.md`, and rerun the validator.
