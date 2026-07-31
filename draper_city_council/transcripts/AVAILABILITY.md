# Draper — meeting video transcripts: AVAILABILITY

**As-of:** 2026-07-13 (built by `expand-city-sources`, source type 5)
**Verdict:** Draper's authoritative video archive is **Granicus** (`draper.granicus.com`,
`view_id=1`) — video-complete for 2020→present, but its caption endpoint is an **empty stub
for every clip** (0 recoverable captions). The **only sanctioned caption source** is the
third-party **"Utah Record - Public Meetings" YouTube mirror**, which carries a **2026-01-06 →
2026-04-15 window only** (25 unique Draper meetings) with **YouTube ASR auto-captions on
23/25**. A representative **sample of 10** caption tracks was fetched (all 8 mirrored Council
meetings + the 2 longest PC meetings), per the sample-only policy. Everything before 2026 is
honestly **untranscribed** (video exists on Granicus; no caption track anywhere official).

## Platform findings (what was checked)

1. **Granicus (authoritative; 0 captions).** `ViewPublisher.php?view_id=1` lists **1,426
   video clips** across all bodies (full catalog retained in `granicus_clips.csv` — name,
   date, clip_id, duration, MediaPlayer URL, direct `archive-video.granicus.com` MP4).
   2020→present: **City Council 155 clips (2020-01-14 → 2026-07-07), Planning Commission 147
   (2020-01-09 → 2026-07-09)**, RDA 10 (→2021-06), MBA 6 (→2024-02), CRA 24 (2021-11 →
   2026-06), plus HPC/committees. Every player config exposes exactly one English subtitle
   track at `/videos/<clip_id>/captions.vtt` — and it is a **40-byte empty stub** (`WEBVTT` +
   one zero-length cue) on **all 14 clips probed** spanning 2020→2026, both Council and PC
   (evidence retained: `raw/_granicus_captions_stub_clip1826.vtt`). No `.srt` variant (404);
   `TranscriptViewer.php` returns an empty analytics-boilerplate page. **Granicus captions
   were never populated — this is a data finding, not a scraper miss.**
2. **Official Draper YouTube channel has NO meeting video.** `UCXDVRMIeGN5BytGRzI2Nb_w`
   (linked from draperutah.gov) is a promo/events channel — 110 videos ("Draper City Talk",
   Draper Days, State of the City) + 1 stream (tree lighting); zero council/PC meeting
   recordings (both `/videos` and `/streams` tabs enumerated with `yt-dlp --flat-playlist`).
3. **Utah Record mirror (the caption source).** The third-party channel **"Utah Record -
   Public Meetings"** (`UC5hXeD66VUV_w655ionxaSA` — the same mirror that serves Sandy/Lehi/
   Layton in this repo) carries **40 Draper uploads = 25 unique meetings, 2026-01-06 →
   2026-04-15 only** (Council 8, PC 6, HPC 4, Appeals 2, Community Engagement 2, Tree 2,
   Parks 1; full enumeration in `channel_videos.csv`). **15 meetings are uploaded twice**
   (identical durations — true duplicates; second ID kept in `index.csv
   duplicate_video_id`). Mirror durations match the Granicus clips within ~1 minute for
   8/10 sampled meetings; **Council 2026-02-03 (5193s vs 6120s) and 2026-03-24 (5238s vs
   7680s) are shorter on the mirror — likely truncated captures** (flagged in `index.csv
   note`; the Granicus MP4 is the complete recording).
4. **Caption stats on the mirror:** **23/25 meetings have English ASR auto-captions**
   (YouTube timedtext; **no manual/human tracks exist anywhere**). Zero-caption videos:
   Parks 2026-01-07 (`PRU0sWMU2-Q`), HPC 2026-04-15 (`i9djuDik88c`), and one PC 2026-03-12
   duplicate (`0SU1GjiCvdU` — its twin `atmd5vqHDS4` has captions and was used).
5. **OpenUtah** (`draper.openutah.org`) exists, but its transcript/meeting pages and `/api/`
   are `robots.txt`-disallowed (explicitly for Claude/AI agents). Per the skill's polite
   rule it was used for nothing here — **not scraped**; discovery came from Granicus +
   YouTube only.

## What was fetched (sample-only policy)

**10 caption tracks, 179,852 words** (raw WebVTT in `raw/`, cleaned ASR-headed markdown in
`text/`, provenance in `raw/_fetch_log.csv`):

| date | body | words | note |
|---|---|---|---|
| 2026-01-06 | Council | 6,053 | |
| 2026-01-20 | Council | 8,677 | |
| 2026-02-03 | Council | 8,120 | mirror ~15 min shorter than Granicus clip |
| 2026-02-10 | Council | 22,465 | |
| 2026-02-17 | Council | 17,914 | |
| 2026-03-03 | Council | 14,398 | |
| 2026-03-24 | Council | 14,158 | mirror ~40 min shorter than Granicus clip |
| 2026-04-07 | Council | 36,980 | |
| 2026-02-26 | PlanningCommission | 16,884 | |
| 2026-03-12 | PlanningCommission | 34,203 | fetched from duplicate upload `atmd5vqHDS4` |

That is the mirror's **complete Council set** (8/8) + 2 of 6 PC meetings. The remaining 13
captioned mirror videos (4 PC + 9 committee-body) are indexed `format=na,
extraction_method=not_retrieved_sample_policy` — retrievable any time with the one-liner in
`CLAUDE.md`. All 14 Council+PC mirror dates were verified 1:1 against
`meeting_minutes/minutes_index.csv` / `planning_commission/minutes_index.csv`.

## The honest gap

- **2020-01 → 2025-12: video-complete on Granicus, caption-less everywhere.** ~300
  Council+PC meetings in the repo's coverage window have a retrievable MP4 but **no
  transcript track on any official path**. This is the bulk of the corpus.
- **2026-05 → present:** not yet on the mirror (its Draper window stops 2026-04-15); Granicus
  has the clips (e.g. Council 2026-07-07, clip 2117) with the usual empty caption stub.

## Whisper candidates (PROPOSE ONLY — user decides; direct MP4s make this easy)

1. **Council 2024-10-15 — clip 1786** (`https://archive-video.granicus.com/draper/draper_1942ae6d-edfe-464c-a3c7-df1fb16efba6.mp4`):
   the **mayoral tie-break on Ordinance #1625** (2 Aye / 2 Nay / 1 Recuse; Mayor Walker's
   only vote in the whole corpus) — the single most dramatic Draper vote; the deliberation
   behind it exists only on video.
2. **Council 2026-07-07 — clip 2117**: currently **recap-only** (no adopted minutes yet, so
   it is withheld from `meeting_minutes/`) — a transcript would be the only substantive
   record until the minutes are adopted.
3. **Contested PC meetings** (the PC is Draper's contested body — 201 contested motions vs
   the Council's 15): pick the top divided-vote dates from `db/civic.db` `v_contested` and
   transcribe those clips from `granicus_clips.csv`.

Any Whisper output is ASR — label with the standard header, never treat as the official record.
