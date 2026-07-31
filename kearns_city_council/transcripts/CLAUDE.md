# Kearns — transcripts dataset (build + linkage guidance)

**Source type 5** (`expand-city-sources`). Built 2026-07-13. Additive-only; touches no
existing dataset. See `AVAILABILITY.md` for the full platform verdict, per-year audio
inventory, caption stats, and the Whisper proposal.

## What this dataset is (HYBRID — captioned video + audio inventory)

Kearns has **two recording mediums**, and this dataset holds both:

1. **YouTube ASR transcripts (the only real transcripts).** The city's own channel
   **@KearnsCity ("Kearns City Government")** posts **city-era (2026+)** council live-stream
   archives. **11 of 12 carry an English automatic (ASR) caption track** — fetched with
   `yt-dlp --write-auto-sub en` and cleaned to `text/<date>_<videoid>.md`. `format=caption`,
   `caption_type=asr`. Coverage **2026-01-12 → 2026-06-08** (~154k words).
2. **PMN meeting-audio INVENTORY (no captions → Whisper leads).** Every Utah Public Notice on
   **council body 5823** + **PC body 1561** attaches a per-meeting **MP3**. 276 rows,
   **2016/2017 → 2026**; **218 live** (13.6 GB), **58 purged** (404, pre-~2019 blob rot).
   Audio has no caption track → `format=na`, `caption_type=none`, `whisper_candidate=yes`
   (live only). **Nothing is downloaded** — link-only inventory (a documented allowed
   exception; the bytes are public + re-fetchable). This is the **audio-only branch** of the
   skill, layered under the YouTube captions.

## Files
- `index.csv` — SCHEMA_SPEC §9 transcripts contract header
  (`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`)
  + extras (`media_source,audio_url,audio_filename,media_type,pmn_body_id,pmn_file_id,notice_url,size_bytes,http_status,whisper_candidate`).
  **288 rows** = 11 YouTube caption + 1 YouTube no-caption + 276 PMN audio. Split on
  `media_source` (`youtube` | `pmn_audio`) and `format` (`caption` | `na`).
- `kearns_audio_inventory.csv` — the raw PMN audio→date map (sidecar; `kearns_harvest_audio.py`).
- `kearns_audio_sizes.csv` — HEAD-probe per audio file (`http,content_type,bytes`) — liveness +
  the Whisper cost basis.
- `raw/_probe_5823_list.html`, `raw/_probe_1561_list.html` — the cumulative PMN notice-list
  pages (provenance for the audio harvest).
- `raw/cap_<date>_<videoid>.en.vtt` — the 11 raw YouTube ASR caption tracks.
- `raw/_kearnscity_streams.txt` — the 12-video channel enumeration (which have captions).
- `raw/_utah_record_channel_titles.txt` — 78 Utah-Record-mirror titles (evidence: 0 Kearns).
- `text/<date>_<videoid>.md` — the 11 cleaned ASR transcripts (ASR-quality header).

## Build / regenerate
```
# 1. (re)fetch the PMN cumulative notice lists into raw/ with a browser UA:
#    /pmn/list/notices.html?id=5823&page=300  -> raw/_probe_5823_list.html
#    /pmn/list/notices.html?id=1561&page=300  -> raw/_probe_1561_list.html
python3 kearns_harvest_audio.py     # raw/_probe_*_list.html -> kearns_audio_inventory.csv
#    (HEAD-probe the audio URLs -> kearns_audio_sizes.csv; see git history for the probe snippet)
# 2. (re)fetch YouTube ASR captions (raw/cap_*.en.vtt) + clean:
python3 kearns_clean_captions.py    # raw/cap_*.en.vtt -> text/<date>_<id>.md
# 3. assemble:
python3 kearns_build_index.py       # inventory + sizes + captions -> index.csv
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
Audio is decided by **file extension** (mp3/m4a/wav), **not** the PMN `(Audio Recording)`
category label (some notices mis-file a PDF under it). The meeting date comes from the
`MM-DD-YYYY` in the audio filename, falling back to the notice datetime.

## Linkage
Join to `meeting_minutes/all_votes.csv` / `planning_commission/` and the minutes **by meeting
date** (+ `body`). YouTube rows are all `body=Council` (city-era; the CRA is folded in-recess
into the same stream). PMN audio rows carry `body` ∈ Council / Planning Commission. **Never join
by filename** — recorder-native MP3 names and multi-part "Audio N of M" splits carry no reliable
key. Multiple rows can share a date (multi-part audio; two YouTube parts; audio + a YouTube
stream of the same meeting) — that is expected, not a duplicate.

## Caveats
- **`caption_type=none` on the 276 audio rows is a TRUE zero**, not "unrecovered" — an audio file
  has no caption track. Only the 11 YouTube ASR rows are real transcripts.
- **ASR quality.** The 11 transcripts are automatic captions — expect word errors, no speaker IDs
  beyond YouTube's `>>` turn markers, and stream-boundary cut-offs. **Not an official record**;
  the clerk's minutes in `meeting_minutes/` are canonical.
- **Coverage seam.** YouTube captions are **city-era only (2026-01→)**. The township era
  (2017–2025) has audio but no transcript — the top Whisper priority (`AVAILABILITY.md`).
- **2017–2018 council audio is purged** (58×404, pre-~2019 PMN blob rot) — `whisper_candidate=no`.
- **Whisper is proposed, not run** (owner-gated). If later run on a PMN audio file: write raw
  output to `raw/<date>.<ext>`, a cleaned `text/<date>.md` headed "AUTOMATIC TRANSCRIPTION — ASR,
  expect word errors; not an official record," set that row's `format=caption`/`caption_type=asr`/
  `path=text/<date>.md`, and rerun the validator.
