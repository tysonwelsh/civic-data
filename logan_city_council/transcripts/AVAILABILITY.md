# Logan meeting-video transcripts — availability

**As-of:** 2026-07-05 · **Dataset:** `logan_city_council/transcripts/` · **Source type 5** (meeting-video transcripts)

## Summary

Logan City posts its Municipal Council meetings as **YouTube live streams** on the official
**"City of Logan"** channel. Every stream carries a **YouTube auto-caption (ASR) track**,
retrievable cleanly with `yt-dlp`. This dataset ships:

- a **FULL video→date map** of the channel — **155 videos** (153 dated, 2 undated
  presentations) — in `channel_videos.csv` and `index.csv`, each flagged for whether it
  matches a meeting in `meeting_minutes/minutes_index.csv`; **and**
- a **SAMPLE-ONLY** download of **10** ASR caption tracks (the 10 most recent regular
  Council meetings, 2026-01-20 → 2026-06-02) as verbatim `raw/<date>.vtt` + cleaned
  `text/<date>.md`.

**Why sample-only:** owner decision 2026-07-05. The durable deliverable here is the
**map** (which meeting is which video, and where its captions live), not a full 2021–2026
caption backfill. Any of the remaining 143 dated videos can be pulled later with the same
one-line `yt-dlp` command (see `CLAUDE.md`) — the map makes that a mechanical follow-up.

## Where Logan video lives

- **Primary host — YouTube, "City of Logan":**
  `https://www.youtube.com/channel/UCFLPAOK5eawKS_RDBU0stRQ`
  - Meetings are published under the channel **`/streams`** tab (live streams), not
    `/videos` (only 2 legacy items sit under `/videos`). Enumerate with
    `yt-dlp --flat-playlist .../streams`.
- **PMN audio (secondary):** Utah Public Notice meeting entries attach per-meeting
  **audio** (`.m4a`/`.mp3`). Noted but not used — YouTube ASR captions are preferable
  (already text; no transcription step). PMN audio is, however, the **Whisper source of
  record for the pre-2021 video gap** (see below).

## Caption type: ASR (automatic), not manual

- The caption tracks are **YouTube auto-captions (ASR)**. `yt-dlp --list-subs` shows only
  an *automatic* English track (`en` / `en-orig`, identical) — **no** manually authored /
  verbatim caption track exists. **Expect word errors; this is NOT the official record.**
  The authoritative record remains the clerk's **minutes** in `meeting_minutes/`.
- Cleaned `text/<date>.md` files carry that caveat in their header. Raw `.vtt` is retained
  verbatim in `raw/`.

## Coverage window + cutoff

- **Video coverage: 2021-01-05 → 2026-06-30.** The channel's earliest content is
  **January 2021** — **there is no 2020 video** even though the project window is
  2020–2026 and minutes exist back to 2020-01-07. **2020 is a hard video gap** (channel
  did not exist / did not archive that year).
- Per-year video counts: 2021: 29 · 2022: 26 · 2023: 28 · 2024: 26 · 2025: 29 ·
  2026: 15 (through June 30) · undated: 2.
- **136 of 153 dated videos** map to a row in `meeting_minutes/minutes_index.csv`. The
  **17 unmatched dated videos** are legitimately non-regular-meeting events with no council
  minutes: budget workshops/meetings, Truth-in-Taxation hearings, candidate/"Meet the
  Candidates" forums, board-of-canvassers/canvass meetings, a Light & Power IRP
  presentation, and 2026 meetings whose minutes are not yet published (June 16 & the
  June 30 special). The **2 undated videos** are Logan City Police "Child Predator/Internet
  Safety" presentations (not meetings) — retained in `channel_videos.csv`, excluded from
  `index.csv` (no meeting date). These are honest gaps, not defects.
- **Duplicate uploads:** Logan double-posted a handful of meetings (same date, two video
  IDs — e.g. 2021-02-16, 2021-11-02, 2022-01-18, 2022-10-18, 2023-08-15, 2023-09-05,
  2025-01-21, 2025-03-04) and split one (2021-09-21 "Part 2"). All rows are kept in the
  map; the sample picks a single video per date.

## Sample retrieved this pass (10 caption tracks)

Most-recent regular Council meetings, all matched to minutes:
2026-06-02, 2026-05-19, 2026-05-05, 2026-04-21, 2026-04-07, 2026-03-17, 2026-03-03,
2026-02-17, 2026-02-03, 2026-01-20. Each: `raw/<date>.vtt` (verbatim ASR) +
`text/<date>.md` (cleaned, ASR-headed). Provenance in `raw/_fetch_log.jsonl`
(video_url, lang, bytes, sha256, retrieved_utc).

## High-value meetings PROPOSED for Whisper transcription

Whisper is **NOT** run here (owner's call — cost). If verbatim deliberation is wanted
beyond the sample, prioritize:

1. **The 2020 video gap (entire year).** No YouTube video exists for 2020. The only audio
   path is **PMN meeting audio** (`.m4a`/`.mp3` attachments) → Whisper. Highest-value
   because it is the *only* way to get 2020 deliberation audio at all.
2. **Contested-vote meetings** — join `meeting_minutes/all_votes.csv` filtered to any
   Nay/Abstain/Recuse against `channel_videos.csv` on date; those are the high-signal
   deliberations Logan's minutes summarize away. Pull the matched YouTube video → captions
   (already ASR) or Whisper for higher fidelity.
3. **Budget / Truth-in-Taxation hearings** (the 17 unmatched events) — no council minutes
   exist for these, so a transcript is the *only* text record. Videos are already mapped in
   `channel_videos.csv` (body = BudgetWorkshop / TruthInTaxation).
4. **Any remaining 2021–2025 regular Council meeting** — all are mapped and one `yt-dlp`
   line away; Whisper only if ASR quality proves inadequate on spot-check.

## What was checked

- `yt-dlp` install: already present (v2026.06.09) — installed cleanly, no gap.
- Channel enumeration: `/streams` (153) + `/videos` (2) via `yt-dlp --flat-playlist`.
- Caption availability: `yt-dlp --list-subs` on a sample video → automatic English track
  only (ASR), formats vtt/srt/ttml/json3.
- Date mapping: title-parsed each video date; matched against
  `meeting_minutes/minutes_index.csv` (136/153 matched; 17 non-meeting events; 2 undated).
- Sample download: 10 recent Council `en` auto-caption tracks via the sanctioned
  `--write-auto-sub --sub-format vtt --skip-download` path.
