# Orem meeting-video transcripts — availability

**As-of:** 2026-07-05 · **Dataset:** `orem_city_council/transcripts/` · **Source type 5** (meeting-video transcripts)
**Policy for this build:** **SAMPLE-ONLY** (owner decision 2026-07-05). The durable deliverable
is the full **video→date map**; only a ~10-meeting representative sample of caption tracks was
downloaded as a proof-of-concept. This is deliberately **not** a full backfill.

## Summary

Orem posts meeting **video** to its official **YouTube** channel, and — unlike the Lehi pilot
(where `yt-dlp` was absent and nothing could be pulled) — `yt-dlp` **is installed here and the
sanctioned caption path works cleanly.** So this dataset ships with **real recovered captions**:

- A complete **map of 111 meeting videos → dates** (`channel_videos.csv`): 91 City Council + 20
  Planning Commission, spanning **2016-01-12 → 2025-06-24**. 108 are confidently dated from the
  video title; 3 are undated (see below).
- **10 sample ASR caption tracks** actually downloaded (8 recent Council 2025 + 2 recent PC 2022),
  retained verbatim as `raw/<date>.vtt` and cleaned to readable `text/<date>.md` (headed with the
  ASR caveat). `index.csv` marks these `format=caption`; the other 98 dated videos are `format=na`
  (mapped, not downloaded — sample-only).

## Where Orem video lives

- **Primary host — YouTube, channel "Orem City" (`@TheCityofOrem`)**,
  `https://www.youtube.com/@TheCityofOrem`. Relevant playlists:
  - **"Orem City Council"** — `https://www.youtube.com/playlist?list=PLrTfLjLjnfUqwLDXrZAQGIBnQmRndthY_`
    (91 videos, 2016–2025).
  - **"Planning Commission"** — `https://www.youtube.com/playlist?list=PLrTfLjLjnfUrfUiE63phUlvwZ6Mm2RS6x`
    (20 videos, 2021–2022).
  - "All City Meetings" (`...PLrTfLjLjnfUqI4Fr2YwA-9YJXVZ5_kzsV`) also exists and mixes bodies; the
    two body-specific playlists above were used as the authoritative source.
- **Google Drive archive** — root `https://drive.google.com/drive/folders/1EEBkHidmn6PrXj9ib0thApFSqmgU9QSv`
  has a **"Meeting Recordings"** subfolder (raw recordings). Not harvested here: YouTube captions are
  preferred over raw recordings, and the Drive recordings would require Whisper (see below).
- **OpenUtah** (`orem.openutah.org`, the recurring Utah transcript mirror) was noted as a possible
  meeting→video map source only; its transcript text sits behind a `robots.txt`-disallowed `/api/`
  and was **not** scraped. It was not needed — the YouTube playlists gave a cleaner, more complete map.

## Caption type: ASR (automatic), not manual

Every sampled video exposes **automatic** captions only (`en-orig` = "English (Original)", i.e.
YouTube ASR); no manually-authored/verbatim track was found. All `index.csv` rows are
`caption_type=asr`. **Expect word errors — these are NOT an official record.** The authoritative
record remains the clerk's **minutes** already in `meeting_minutes/` and `planning_commission/`.
Every `text/*.md` file is headed with this caveat.

## Coverage window & platform cutoffs (findings)

- **Video window on YouTube: 2016 → mid-2025.** Uneven by year (dated videos):
  2016 ×19, 2017 ×17, **2018–2019 ×0**, **2020 ×1** (only the 2020-02-05 Alpine School District joint
  meeting — the COVID year is essentially absent from YouTube), 2021 ×20, 2022 ×34, **2023 ×3**,
  **2024 ×3**, 2025 ×11 (through 2025-06-24; playlist not updated past then as of this build).
- **Planning Commission video effectively stops after 2022-09-21** — no PC videos 2023–2025 on the
  playlist. PC minutes continue in `planning_commission/` regardless.
- **Minutes-join:** of the 88 dated **Council** videos in the minutes-coverage era (2020+), **48
  match a `meeting_minutes/minutes_index.csv` date exactly**; the 40 "no" are the pre-2020 backlog
  (2016–2017, before minutes coverage) plus a handful of work/joint sessions (e.g. 2020-02-05 joint,
  2022-01-10 which the title dates to a Monday). **19 of 20 PC videos** match a
  `planning_commission/minutes_index.csv` date. `channel_videos.csv` carries a `minutes_match` flag
  per row (`yes`/`no`/blank).
- **One video is gone:** `H7bSl28TMS4` (titled 2025-04-22 Council) now returns *"This video is not
  available"* on YouTube (removed/private). It is kept in the map as a `format=na` row with a note;
  a replacement (2025-01-28) was sampled to keep the caption sample at 10.

## Undated videos (in `channel_videos.csv`, excluded from `index.csv`)

3 videos carry no reliable date in the title and were left with a blank date (map-only, honest gap):
`PG5nXPrxFG0` (title literally "NA"), `Viun0MCU0Ns` ("Election Canvassing"), `2bEk1pleOEk`
("City Council Retreat"). They are real videos; their exact meeting dates were not asserted.

## Full-backfill path (NOT run — sample-only by policy)

Because `yt-dlp` works here, a full backfill needs **no Whisper** for the ~88 dated videos that have
ASR captions — it is just the same `yt-dlp --write-auto-sub` loop over the remaining `format=na`
rows in `index.csv`. See `CLAUDE.md` for the exact command. Cheap and mechanical; deferred only
because the owner scoped this as a proof-of-concept.

## High-value meetings PROPOSED for Whisper (Whisper NOT run here — owner's call)

Whisper is only warranted where **YouTube ASR captions do not exist** (otherwise just use `yt-dlp`).
Those cases:

1. **The 2020 gap (highest value).** ~13 council meetings in 2020 have **no YouTube video** at all
   (only 2020-02-05 is posted). Audio/video for these likely lives in the Google Drive **"Meeting
   Recordings"** subfolder. 2020 is the COVID land-use/budget year — verbatim deliberation here is
   not otherwise recoverable. Pull the Drive recording → Whisper → label identically as ASR.
2. **2025-04-22 Council** — the one YouTube video that has been pulled/privatized; if a recording
   survives on Drive, Whisper is the only route.
3. **Contested-vote meetings that lack a YouTube video.** Contested council meetings (any
   Nay/Abstain/Recuse in `meeting_minutes/all_votes.csv`) with **no** mapped video include
   **2022-10-11, 2023-03-14, 2023-05-16, 2023-08-22, 2024-02-27, 2024-05-14, 2024-08-27, 2024-12-10,
   2025-01-14** — the divergence a transcript captures over a summarized minute. (Contested meetings
   that DO have a video — e.g. **2025-05-13** (sampled here), 2022-09-27, 2023-12-12 — need only
   `yt-dlp`, not Whisper.)

## What was checked

- WebSearch located the `@TheCityofOrem` channel + orem.gov/meetings.
- `yt-dlp --flat-playlist` enumerated both body playlists (111 videos) and the channel's playlist list.
- `yt-dlp --list-subs` confirmed ASR-only caption tracks; `--write-auto-sub ... en-orig` downloaded 10.
- Video dates parsed from titles and cross-joined to `minutes_index.csv` (council + PC).
- Google Drive "Meeting Recordings" folder noted (not harvested — Whisper territory).
