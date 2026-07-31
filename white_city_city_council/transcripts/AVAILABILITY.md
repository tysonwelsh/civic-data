# White City — meeting-video transcripts: availability

**As-of:** 2026-07-13 · **Source type 5** (`expand-city-sources`, audio-only-city branch) ·
dataset floor 2017 (entity history; audio only begins mid-2025).

## Verdict — AUDIO-FIRST, ZERO CAPTIONS

White City publishes **no video and no caption track anywhere.** Its only meeting-recording
medium is a **per-meeting audio file (MP3/M4A)** posted on the Streamline site alongside the
agenda/packet/minutes PDFs. There is **no captioned source to harvest** — so the deliverable is
the **audio→date inventory + a zero-caption verdict.** Whisper is **proposed, not run** (below).

| Platform | Handle / URL | Items | Range | Captions? |
|---|---|---|---|---|
| **Streamline site audio** | `whitecity.utah.gov/files/<hash>/*.MP3` (+ 1 `.m4a`) | **13** | 2025-07-10 → 2026-06-04 | **NO** (audio only — Whisper lead) |
| YouTube (dedicated channel) | — | **none found** | — | n/a (no channel exists) |
| **Utah Record** mirror | `UC5hXeD66VUV_w655ionxaSA` | 78 videos, **0 White City** | — | n/a (no White City uploads) |
| Vimeo / other | — | none found | — | n/a |

### How each platform was checked
- **Streamline (the real source):** harvested the labeled attachment anchors from the saved
  council year pages (`/council-meeting?year=2022..2026`) + the pre-2022 `/meetings-archive`
  (raw HTML retained under `raw/_page_*.html`). Audio attachments carry an `aria-label` of the
  form `"<file> attachment for <YYYY-MM-DD> …Meeting"` — the date/title come straight from that
  label, never from the opaque `/files/<hash>/`. **Audio is posted only on the 2025 and 2026
  year pages** (2025: 6 MP3 + 1 M4A; 2026: 6 MP3). The 2022/2023/2024 year pages and the
  2017–2021 archive carry **PDF only — no audio** (2023: 53 pdf/0 audio; 2024: 50 pdf/0 audio;
  archive: 213 pdf/0 audio). So the audio series is a **recent (mid-2025→) practice**, not a
  full-history record.
- **All 13 audio URLs HEAD-probed live** (`raw/`-adjacent `wc_audio_sizes.csv`): every one
  returns HTTP 200 with an audio content-type (`audio/mpeg`, one `audio/mp4a-latm`). These are
  genuine recordings, not stubs.
- **YouTube:** no dedicated White City channel exists (two web searches + recon). Do **not**
  confuse with the White City **Water** Improvement District (a separate special district) or
  same-named cities in other states.
- **Utah Record mirror** (`UC5hXeD66VUV_w655ionxaSA`): enumerated all **78** videos via
  `yt-dlp --flat-playlist` — **zero** contain "white city" (title list saved to
  `raw/_utah_record_channel_titles.txt`).

## Caption stats
- **Captioned meetings: 0.** MP3/M4A audio has no caption track by definition; no captioned
  video source exists on any platform. **No caption files were fetched** (none exist to fetch),
  so `transcripts/raw/` holds only the harvested source-page HTML + the Utah-Record title list.
- Every `index.csv` row: `caption_type=none`, `format=na`, `path` blank (nothing stored).

## MP3 audio inventory (the deliverable)

`index.csv` (13 rows) + the `wc_audio_inventory.csv` sidecar map each audio file to its meeting
date. **Total ≈ 1.34 GB across 13 files** (per-file 7–195 MB; median ~110 MB):

```
2025-07-10  115.2 MB    2025-11-18    7.3 MB    2026-03-05  139.5 MB
2025-08-07   43.6 MB    2025-12-04   70.3 MB    2026-04-02  132.3 MB
2025-09-04  104.2 MB    2026-01-08   71.5 MB    2026-05-07  107.1 MB
2025-10-02  119.4 MB    2026-02-05  194.7 MB    2026-06-04  156.5 MB
2025-11-13   83.4 MB
```

(The 2025-11-18 file is small — a short special/canvass meeting, consistent with the
`11-18-25 Canvass of Election Minutes` on the year page. Filenames vary — recorder-native
`DS######.MP3`, one `240701_0031.MP3`, one human `WC 9-4-2025 Audio.mp3`, one phone-recorded
`audio*.m4a` — so **join to minutes by date, not by filename.**)

## Whisper candidates — PROPOSED ONLY (owner-gated, NOT run)

All **13** audio files are flagged `whisper_candidate=yes`. They are a **clean, bounded Whisper
source** for this small entity:
- **Born-audio, not scanned** — direct-recorded MP3/M4A (no OCR floor), single meeting room.
- **High marginal value:** the 2025 files (2025-07-10 → 2025-12-04) fall in the **narrative-tally
  vote era** where `meeting_minutes/all_votes.csv` records *no per-member roll* — the audio is
  the **only** record of who said what and how unrecorded discussion went. The 2026 files back
  the new named-roll-call city era and would corroborate the roll calls verbatim.
- **Bounded cost:** 13 files, ~1.34 GB, ~13–15 hours of audio — a one-shot Whisper pass, not an
  open-ended crawl. Recommended priority order: the **2025 narrative-tally meetings first**
  (where minutes attribution is thinnest), then 2026.
- **Not run here** because Whisper is expensive and owner-gated (skill rule); the bytes are
  public and re-fetchable from the `audio_url` in `index.csv` at transcription time.

## Gaps / honest notes
- **Audio starts mid-2025** — no meeting audio exists for 2017–mid-2025 on the site (PDF-only
  years). The pre-audio record lives entirely in `meeting_minutes/` (minutes PDFs). Not a
  scraper miss — the city simply did not post audio before ~July 2025.
- **13 audio files ≈ every meeting since 2025-07** — consistent with the ~monthly Thursday
  cadence plus mid-month specials (e.g. the 2025-11-18 canvass alongside the 2025-11-13
  regular). No obvious missing meeting in the audio-era window.
- **`caption_type=none` is a true zero**, not "unrecovered" — there is no caption track to
  recover on an audio file.
