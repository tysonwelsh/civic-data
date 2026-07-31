# White City — transcripts dataset (build + linkage guidance)

**Source type 5** (`expand-city-sources`, the **audio-only-city branch**). Built 2026-07-13.
Additive-only; touches no existing dataset.

## What this dataset is (and is NOT)

White City is **audio-first with zero captions.** Its Streamline site posts a **per-meeting
audio file (MP3/M4A)** next to the agenda/packet/minutes PDFs. There is **no video and no
caption track on any platform** (no YouTube channel; absent from the Utah Record mirror). So:

- This is an **audio→date INVENTORY**, not a transcript corpus. **No transcripts exist** because
  there are no captions and Whisper has not been run.
- **Nothing was downloaded** — the audio bytes (~1.34 GB) are public + re-fetchable; the dataset
  is a **link-only inventory** (a documented allowed exception; `raw/` holds the harvested
  source-page HTML as provenance, not the media).
- See `AVAILABILITY.md` for the platform verdict, per-platform checks, caption stats (0), the
  full MP3 size inventory, and the Whisper proposal.

## Files

- `index.csv` — SCHEMA_SPEC §9 transcripts contract header
  (`date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path`)
  + extras (`audio_url,audio_filename,media_type,size_bytes,whisper_candidate,source_page_year`).
  13 rows, 2025-07-10 → 2026-06-04. Per row: `video_url` blank (audio, not video),
  `caption_type=none`, `format=na`, `path` blank (not stored), `source_url`/`audio_url` = the
  live audio file.
- `wc_audio_inventory.csv` — the raw audio→date map (sidecar, human-first columns).
- `wc_audio_sizes.csv` — HEAD-probe result per file (`bytes,content_type,http`) — proof the
  URLs are live audio + the Whisper cost basis.
- `raw/_page_*.html` — the harvested Streamline council year pages + `/meetings-archive`
  (provenance for the anchor harvest). `raw/_utah_record_channel_titles.txt` — the 78 Utah
  Record mirror titles (evidence: 0 White City).
- `text/` — empty (no captions to clean; ASR-header transcripts would land here only if Whisper
  is run).

## Build / regenerate

```
# 1. (re)fetch the Streamline year pages into raw/ with a browser UA, then:
python3 wc_harvest_audio.py     # raw/_page_*.html -> wc_audio_inventory.csv (parses aria-labels)
python3 wc_build_index.py       # wc_audio_inventory.csv + wc_audio_sizes.csv -> index.csv
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```

Date/title come from each attachment anchor's `aria-label`
(`"<file> attachment for <YYYY-MM-DD> …Meeting"`) — **never** from the opaque `/files/<hash>/`.
Audio is present only on the 2025 + 2026 year pages (2022–2024 + the 2017–2021 archive are
PDF-only).

## Linkage

Join to `meeting_minutes/all_votes.csv` / minutes **by meeting date** (all rows `body=Council`;
White City is a single-body, all-at-large entity). Do **not** join by filename — recorder-native
`DS######.MP3` names carry no meeting date.

## Caveats

- **`caption_type=none` is a true zero, not "unrecovered."** There is no caption track on an
  audio file to recover.
- **Audio coverage starts ~2025-07** — the pre-audio record (2017–mid-2025) is minutes-only in
  `meeting_minutes/`. Not a gap in this dataset's method; the city didn't post audio earlier.
- **Whisper is proposed, not run** (owner-gated). All 13 files are clean born-audio Whisper
  candidates; prioritize the 2025 narrative-tally meetings (thinnest minutes attribution). See
  `AVAILABILITY.md`.
- If Whisper is later run: write raw output to `raw/<date>.<ext>`, a cleaned
  `text/<date>.md` headed "AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an official
  record," set that row's `format=caption`/`caption_type=asr`/`path=text/<date>.md`, and rerun
  the validator.
