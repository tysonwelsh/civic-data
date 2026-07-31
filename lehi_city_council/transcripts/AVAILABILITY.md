# Lehi meeting-video transcripts — availability

**As-of:** 2026-07-02 · **Caption backfill:** 2026-07-20 · **Dataset:** `lehi_city_council/transcripts/` · **Source type 5** (meeting-video transcripts)

## Summary

Lehi posts meeting **video** on YouTube, and a third-party site (OpenUtah) publishes
**AI-generated transcripts** of those recordings. The dataset is a **video→date map**
(12 sample meetings, 2025–2026) in `index.csv`.

**Caption backfill (2026-07-20): 2 recovered / 10 unrecovered.** `yt-dlp` is now installed,
so the two mapped meetings whose videos remain public on YouTube were fetched — English
auto-caption (`en-orig`) VTT in `raw/<date>.en-orig.vtt`, cleaned `text/<date>.md` sidecar,
index rows completed:

- **2026-05-26 City Council** (`GMYzejWyA2U`, ~4.8 h) — future of parks, transit, budget.
- **2026-05-28 Planning Commission** (`ajch_vFR84k`, ~41 min) — Bishop 13-lot subdivision,
  Community Forestry code amendment, DADU amendment. Content spot-checked against the PC
  minutes/votes for 2026-05-28 — matches (applicant, lot count, parcel address, all 3 items).

The **ten 2025 meetings could not be recovered**: their videos are no longer publicly
available on YouTube (absent from the "Lehi City" channel `UC-BcH5cOFjKCueNOsjOZPQw`
uploads and its **City Council Meetings** / **Planning Commission** playlists — which reach
back only to Dec 2025 — absent from the "Lehi City Public Meetings" channel
`UCvdXq4ki7K9EU0FWLtTKCIw` uploads, and no match on targeted `yt-dlp` YouTube search on
2026-07-20), and OpenUtah exposes no per-video id (its transcript text is served only behind
the `robots.txt`-disallowed `/api/`). All ten are ledgered in `unrecovered.csv` — an honest
"gaps are data" result, not retried further.

## Where Lehi video lives

- **Primary video host — YouTube.** Two official channels:
  - **"Lehi City Public Meetings"** — `https://www.youtube.com/channel/UCvdXq4ki7K9EU0FWLtTKCIw`
    (the meetings channel; council/PC/RDA/LBA recordings). Also a "City Council Meetings"
    playlist: `https://www.youtube.com/playlist?list=PLtp3sV0AhHwuglXCcjk_f09lf12Q1Mxz2`.
  - **"Lehi City"** (main city channel) — `https://www.youtube.com/channel/UC-BcH5cOFjKCueNOsjOZPQw`.
- **Granicus MediaPlayer** on `lehi.granicus.com` also hosts the video clips (each
  ViewPublisher row has a video clip), but Granicus does not expose a downloadable caption
  track without the player.
- **Transcript mirror — OpenUtah:** `https://lehi.openutah.org/` — "Lehi City Public
  Meeting Transcripts." Self-described: *"Transcripts sourced from official city recordings.
  AI-generated content may contain errors."* Dashboard: **115 meetings indexed, 87
  transcribed** (as of retrieval). Meeting pages at
  `/meetings/<YYYY-MM-DD>-<headline-slug>-<uuid>`.

## Caption type: ASR (automatic), not manual

- YouTube auto-captions on these meeting videos are **ASR** (automatic speech recognition).
  No manually-authored/verbatim caption track was confirmed.
- OpenUtah transcripts are **AI-generated** from the recordings (their own disclaimer) —
  the same ASR-quality caveat applies: **expect word errors; NOT an official record.**
- The authoritative record remains the clerk's **minutes** already in
  `meeting_minutes/` and `planning_commission/`.

## Tool situation

- **2026-07-02 (pilot):** `command -v yt-dlp` → **not found** — nothing retrieved.
- **2026-07-20 (backfill):** `yt-dlp 2026.06.09` is now installed and is the sanctioned clean
  path (`yt-dlp --write-auto-sub --sub-lang en-orig --sub-format vtt --skip-download`). It
  successfully pulled the English auto-caption tracks for the two meetings whose videos are
  still public. Per-video IDs were recovered by enumerating the "Lehi City" channel's
  **City Council Meetings** (`PLtp3sV0AhHwuglXCcjk_f09lf12Q1Mxz2`) and **Planning Commission**
  (`PLtp3sV0AhHwuY0Q5thPkNAakMVbgOaYp5`) playlists with `--flat-playlist`. The ten 2025
  meetings returned no public video by any enumeration or search route (see Summary). Per the
  skill, we do **not** scrape YouTube by other means, and did not hit OpenUtah's `/api/`.
- **OpenUtah transcript text is not cleanly fetchable either.** The meeting page
  (`/meetings/...`) is a Next.js app whose static HTML contains only an AI **summary**
  article + metadata (date, body, YouTube-channel link) — **not** the verbatim transcript.
  The full transcript is loaded client-side from the site's API, and
  `https://lehi.openutah.org/robots.txt` contains **`Disallow: /api/`**. Honoring robots +
  the polite-scraper rule, we did **not** hit that endpoint. One meeting page was retained
  as a raw sample of what the mirror exposes:
  `raw/openutah_meeting_page_sample_2025-05-13_council.html` (+ `raw/_fetch_log.jsonl`).

## Coverage of the OpenUtah mirror (finding)

- Mirror coverage begins **~Jan 2, 2025** (earliest page shows Jan 2025) and runs to
  present (2026). **2024 and earlier are NOT on the mirror.** ~110 meetings on record,
  6 pages, all bodies (City Council, Planning Commission, Redevelopment Agency, Local
  Building Authority, work sessions).

## High-value meetings PROPOSED for Whisper transcription

If the user wants verbatim deliberation (Whisper is NOT run here — expensive, user's call),
these are the highest-value untranscribed council/PC meetings to prioritize (deliberation
the clerk's minutes summarize away; pull the video from the YouTube "Public Meetings"
channel or the Granicus clip):

1. **2025-05-13 City Council — denies high-density housing (Salt Spring).** A contested
   denial with neighborhood testimony — exactly the divergence the transcript captures over
   the minutes' summary.
2. **2025-04-08 City Council (Amended) — rejects green-waste facility after pushback.**
   Denial + public opposition; rationale matters.
3. **2025-05-06 / 2025-01-07 City Council — SHARE / attainable-housing plan.** Utah MIH
   (moderate-income housing) policy debate; ties to `housing_plans/`.
4. **2025-03-27 Planning Commission — hospital-area transit plan "despite" objections.**
   PC recommendation against pushback; technical-vs-political divergence.
5. **2025-04-24 Planning Commission — Swig drive-thru conditions + Fieldstone denial.**
   Conditions-of-approval detail rarely fully captured in minutes.
6. Any meeting with a **Mayor tie-break** or a **contested (Nay/Abstain/Recuse) vote**
   (see `meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv`, filter
   contested) — those are the high-drama moments where verbatim audio adds the most.

## What was checked

- YouTube: located both official channels + council playlist (WebSearch); confirmed they
  host council/PC meeting recordings.
- `yt-dlp` presence: `command -v yt-dlp` → absent.
- OpenUtah mirror: fetched `/meetings` index pages 1–6 (mapped 2025–2026 meetings), fetched
  one meeting page raw, probed `/api/...`, `/meetings/.../transcript`, and `robots.txt`.
- Granicus: known video host from `recon.md` (no downloadable captions without the player).
