# transcripts/ — meeting-video transcripts (Taylorsville)

Additive dataset built by `expand-city-sources` §5 (meeting-video transcripts), **SAMPLE-ONLY**
per owner policy. Does not modify any existing dataset.

## Bottom line (read `AVAILABILITY.md` first)

Taylorsville is an **audio-only city with a PR-only YouTube channel**. It streams Council/PC
meetings live but does **not** archive them as YouTube videos; `youtube.com/taylorsvillecity`
is 141 promotional/event videos, **not** a meeting archive. Exactly **one** genuine meeting
video exists on the channel (a 2024-05-15 Planning Commission livestream); its YouTube ASR
caption was retrieved as the single sample. Whisper was NOT run.

## Files

```
raw/2024-05-15_planning-commission.en.vtt   raw YouTube ASR caption track (verbatim), the sample
text/2024-05-15.md                          cleaned transcript, headed "AUTOMATIC TRANSCRIPTION — ASR"
index.csv                                   provenance for RETRIEVED content (1 row = the sample)
channel_map.csv                             FULL channel inventory (141 videos) — the full-channel map
AVAILABILITY.md                             what was checked, the audio-only verdict, OpenUtah/Whisper leads
CLAUDE.md                                   this file
```

## index.csv vs channel_map.csv

- **`index.csv`** — the standard dataset provenance file (`date,title,body,video_url,video_id,
  caption_type,source_url,retrieved_date,format,extraction_method,path,duration_sec,category`). One row: the
  retrieved 2024-05-15 PC sample (`format=caption`, `caption_type=asr`). This is the only
  content actually stored in the dataset.
- **`channel_map.csv`** — the full 141-video channel inventory (`video_id,title,upload_date,
  duration_sec,category,captions_available,video_url`). Enumerated with `yt-dlp --flat-playlist`
  (reliable for id/title/duration); `upload_date` merged from a full metadata pass (**102/141**
  resolved — the JS-runtime-less extraction failed on 41 videos, dates left blank there; these
  are all promotional, so the missing dates are non-analytic). `category` ∈
  `meeting_planning_commission` (1) / `event_livestream` (4, community events, not meetings) /
  `promotional` (136). This file proves the PR-only verdict; it is NOT validator-gated (the
  minimum-schema provenance lives in `index.csv`).

## How the sample was built

```
yt-dlp --skip-download --write-auto-sub --sub-lang en --sub-format vtt \
       -o "raw/2024-05-15_planning-commission.%(ext)s" \
       "https://www.youtube.com/watch?v=0ui3x38KRRo"
# clean (rolling-window dedup, strip inline word-timing tags), head with the ASR banner:
python3 <cleaner> raw/2024-05-15_planning-commission.en.vtt 2024-05-15 \
       "Planning Commission Meeting" 0ui3x38KRRo > text/2024-05-15.md
```

The cleaner strips VTT cue timestamps + `<hh:mm:ss.mmm><c>` inline word tags and de-duplicates
YouTube's rolling-window caption overlap (append a line only when it differs from the last).

## Caveats / linkage

- **ASR quality:** these are automatic captions, not an official record — proper nouns (member
  names, street addresses, land-use case numbers `<SEQ><LETTER><YY>`) are frequently
  misrecognized, and there are **no speaker labels**. The authoritative record is the clerk's
  minutes under `planning_commission/` / `meeting_minutes/`. Do not quote a name/number from the
  transcript without checking the minutes.
- **Linkage:** the PC sample joins to `planning_commission/` by **meeting date** (2024-05-15, a
  Tuesday — PC meets 2nd & 4th Tuesday). Council transcripts would join on Wednesday dates, but
  none exist on YouTube.
- **Refresh:** re-run `yt-dlp --flat-playlist` on the channel to rebuild `channel_map.csv`; a
  new genuine meeting video would appear with a meeting-length duration and a "…Livestream" /
  "…Meeting" title (rare on this PR channel). The real growth source is the city **Audio
  Recordings** archive via Whisper (owner's call) or the **OpenUtah** mirror (metadata-only,
  robots-limited) — see `AVAILABILITY.md`.
```
