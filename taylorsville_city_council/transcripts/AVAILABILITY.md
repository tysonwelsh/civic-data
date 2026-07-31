# Meeting-video transcripts — availability (Taylorsville)

**As-of:** 2026-07-06 · **Source type:** meeting-video transcripts (expand-city-sources §5)
· **Mode:** SAMPLE-ONLY (owner policy — map the channel, retrieve only a small sample).

## Verdict: AUDIO-ONLY city / PR-ONLY YouTube channel — NO archived meeting VIDEO

Taylorsville **streams** its City Council and Planning Commission meetings live, but it does
**not** post the recorded meetings as videos on YouTube. The city's YouTube channel is a
**public-relations channel, not a meeting-video archive**. Therefore this is the skill's
"audio but no YouTube meeting video" branch: the honest structural gap is recorded here, the
full channel is mapped, and **Whisper was NOT run** (owner decides — leads below).

## What was checked (2026-07-06)

| Source | Result |
|---|---|
| YouTube channel `youtube.com/taylorsvillecity` (`--flat-playlist`) | **141 videos**, enumerated in `channel_map.csv`. Content is festivals ("Taylorsville Dayzz"), "Year in Review" recaps, museum tours, "Tombstone Tales", PSAs, recruitment videos. **1** genuine meeting video; **4** community-event livestreams (Wreaths Across America, Get Healthy, Softball honors — not council/PC business); **136** promotional. |
| Channel **Streams/Live** tab | Does not exist ("This channel does not have a streams tab") — no archive of past live meeting streams. |
| Channel **Playlists** | 3 playlists, all PR (Tombstone Tales 2022/2025, Heritage Museum Virtual Tours). No council/PC playlist. |
| City **livestream page** (`/government/elected-officials/city-council-livestream`) | Live-only embed (CivicPlus/Granicus SPA; also links `facebook.com/TaylorsvilleCity`). Streams meetings in real time; **no on-page archive of past meeting video**. |
| City **agendas-minutes portal** | Publishes an **"Audio Recordings"** column alongside Agendas & Minutes (per `recon.md` §1) → the city posts **meeting AUDIO**, which is the true raw source for transcription. |
| **OpenUtah** (`taylorsville.openutah.org`) | **EXISTS** — see leads below. |

## The one genuine meeting video (retrieved as the sample)

- **`0ui3x38KRRo` — "Planning Commission Livestream", 2024-05-15, 2h22m.** The only full
  meeting recording on the channel. YouTube auto-generated (ASR) English captions are
  available; retrieved via `yt-dlp --write-auto-sub`:
  - `raw/2024-05-15_planning-commission.en.vtt` (raw caption track, verbatim)
  - `text/2024-05-15.md` (cleaned, rolling-window dedup, headed "AUTOMATIC TRANSCRIPTION — ASR")
  - indexed in `index.csv` (the sole retrieved-content row).
- This is a stray archived stream; the channel has **no** City Council meeting videos and no
  other PC meeting videos. It is not the basis of a bulk transcript layer — it is the sample.

## Leads (owner decides — NOT executed)

1. **OpenUtah — `taylorsville.openutah.org`** (Whisper-based civic-intelligence mirror).
   Landing page reports **"9 meetings indexed · 8 transcribed"**, transcripts "sourced from
   official city recordings" (i.e. the city audio, Whisper-transcribed). Treat as a
   **summary/metadata source only**: its `robots.txt` disallows `/api/` (where the verbatim
   transcript text is served) and blocks GPTBot from `/*/meetings` and `/*/trans…`. Do **not**
   bulk-scrape it; it is a per-meeting summary/lead, not a caption grab. It also confirms the
   city audio is transcribable and that a small (~9-meeting) transcript set already exists
   externally.
2. **Whisper on the city "Audio Recordings"** — the city's own audio archive
   (agendas-minutes portal "Audio Recordings" column) is the authoritative raw for true
   verbatim transcripts of Council (Wed) and PC (Tue) meetings. High-value candidates =
   contested rezone / budget public-hearing meetings (see `db v_contested`, 73 motions).
   **Whisper was deliberately NOT run** (expensive; owner's call, per skill §5 + task).

## Honest-gap summary

- **Meeting VIDEO archive on YouTube:** none (PR-only channel).
- **Meeting AUDIO:** published by the city (portal "Audio Recordings").
- **ASR captions retrieved:** 1 (the single archived PC meeting, 2024-05-15).
- **External transcript mirror:** OpenUtah (~9 meetings), metadata-only under robots.txt.
- **Whisper:** not run (leads recorded above).
