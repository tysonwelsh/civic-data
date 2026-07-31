# Meeting-video transcripts — availability (as-of 2026-07-02)

Source 5 of `expand-city-sources`. St. George, **Utah** (Washington County) — the Louisiana
city of the same name was hard-filtered out (no LA channel touched).

## Where St. George posts meeting video

St. George City Council meetings are livestreamed to **YouTube** (the city site
`sgcityutah.gov` links "Watch Council Meetings" out to YouTube/Facebook; Revize also serves
audio-only `.mp3` "Recordings", but this dataset is about **video captions**). Two YouTube
channels host the council video, split by era:

| Channel | ID | Role | Council coverage |
|---|---|---|---|
| **City of St. George** | `UCssI3y3sYbIAySKA8M_8dRw` | Current official channel (meetings under the `/streams` tab + a "City Council Meetings (2026)" playlist) | ~**Jul 2025 → present** |
| **Community Education Channel** | `UCYqm-7xA_iN8IlX4uX3HtNg` | Prior/primary host — a regional gov-access channel with a dedicated **"St. George City Council"** playlist (100 videos) | **2021 → mid-2025** |

The channel changeover happened mid-2025 (both carry some overlapping 2025 meetings). Council
meetings on the current channel are in `/streams`, not `/videos` (the `/videos` tab is PR
clips only) — enumerate with `yt-dlp --flat-playlist` against `/streams` and the playlists.

## Planning Commission — NOT on video

**No Planning Commission meeting videos exist on YouTube** (searched both channels + all
playlists). PC is available only as **minutes/PMN** (already in `planning_commission/`). This
is a publishing gap, not a scraper miss — the city does not livestream PC.

## Caption type: AUTOMATIC (ASR) only

Every caption track retrieved is **YouTube auto-generated (ASR)** — `Kind: captions`,
`Language: en` / `en-orig`. **No human/manual caption track exists on any meeting.** ASR is
verbatim-ish but **word-error-prone** (proper names, addresses, ordinance numbers, cross-talk
are frequently wrong). Every cleaned sidecar is headed with that warning. **Not an official
record** — the clerk's minutes (`meeting_minutes/`) remain authoritative.

## ASR caption availability is sparse and era-dependent

YouTube did **not** auto-caption every meeting. Probed 106 council/State-of-the-City videos
across both channels; **50 have an ASR `en-orig` track, 56 do not:**

| Year | Has ASR captions | No captions |
|---|---|---|
| 2021 | 11 | 0 |
| 2022 | 17 | 4 |
| **2023** | **1** | **19** |
| **2024** | **0** | **18** |
| 2025 | 7 | 14 |
| 2026 | 12 | 0 |

**The 2023–2024 council year is a near-total ASR gap** (1 of ~38 meetings captioned) — the
single highest-value target for Whisper. 2021–2022 and 2026 are fully captioned; 2025 is
partial. Whether a track exists is deterministic per video (re-probing is stable), so a "no
captions" result is a real absence, not a transient extraction failure.

## What was retrieved this run

- **10 recent council meetings, caption tracks only** (`--write-auto-sub --skip-download`,
  `en-orig`, vtt), cleaned to `text/<date>.md`. Sample = the recent meetings that actually
  have ASR captions: **2025-03-06, 03-20, 04-03, 04-24, 05-01, 12-04, 12-18 and 2026-01-08,
  01-15, 01-22** (Mar–May 2025 + Dec 2025 from the two channels, extended into Jan-2026
  because **2024 has zero captioned meetings**). ~106k words of ASR text total.
- Raw `.vtt` retained verbatim in `raw/<video_id>.en-orig.vtt`; see `index.csv`
  (`caption_type=asr`, 10 rows) for the retrieved set and `unrecovered.csv` (37 rows) for the
  no-caption gap meetings.
- **yt-dlp rate-limit note:** after enumerating/probing ~110 videos, YouTube began returning
  "Sign in to confirm you're not a bot" (IP throttle). Retrieval was paused ~15 min to stay
  polite, then the remaining 5 downloads completed cleanly with 45s spacing. `index.csv` is
  produced by the idempotent `build_transcripts.py` — re-run it after any further fetch.

## OpenUtah mirror finding

`https://stgeorge.openutah.org/` **is** a live OpenUtah mirror for St. George: it indexes
**24 meetings, 21 transcribed**, and states *"Transcripts sourced from official city
recordings. AI-generated content may contain errors"* — i.e. the same ASR-quality caveat,
plus topic watchlists and a decision log. Its verbatim transcript text is served client-side
behind `robots.txt Disallow: /api/`, so per the polite rule it was used as a
**summary/metadata source only** — the API was **not** scraped. It is a viable
cross-reference/alternative transcript source if the user wants it pursued deliberately.

## HIGH-VALUE untranscribed meetings — PROPOSED for Whisper (NOT run)

Whisper is expensive and **was not run** — these are candidates for the user to approve. All
have public video on YouTube but **no ASR caption track**; Whisper would recover the
deliberation the clerk's minutes summarize away.

1. **All of 2024 (18 council meetings, 0 captioned)** — the top priority. A full election-year
   of council deliberation with zero transcript. Includes 2024-05-02, 2024-08-01, 2024-10-17,
   2024-12-05, etc. (see `unrecovered.csv`, `caption_type=none`, 2024 rows).
2. **2023 council year (19 meetings, only 1 captioned)** — second full-year gap.
3. **Contested 2025 meetings without captions** (e.g. 2025-06-19, 2025-01-16, 2025-02-06) —
   pair with `weeks/<thu>/summary.md` to prioritize meetings that had Nay/Abstain votes or
   heavy public comment.
4. **Planning Commission (all dates)** — never on video at all; if the user wants PC
   deliberation, audio would have to come from the Revize `.mp3` "Recordings" + Whisper, not
   YouTube.

There are also ~26 fully-captioned **2021–2022** council meetings available on the Community
Education Channel that were out of this run's 2024–2025 scope but can be pulled with the same
`build_transcripts.py` pipeline if a deeper backfill is wanted (no Whisper needed — captions
already exist).
