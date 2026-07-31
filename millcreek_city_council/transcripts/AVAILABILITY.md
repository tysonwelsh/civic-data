# Millcreek meeting-video transcripts — availability

**As-of:** 2026-07-06 · **Dataset:** `transcripts/` · **Source type #5** (meeting-video
transcripts) added by the `expand-city-sources` skill. **SAMPLE-ONLY by owner policy:** the
full channel is mapped in `index.csv`, but only ~10 caption tracks were retrieved to disk.

## What exists — a real meeting-video source (NOT an audio-only gap)

Millcreek council & Planning Commission meetings **are recorded on video and posted to
YouTube**, but on a **third-party civic mirror, not a city channel**:

- **Channel: `@UtahRecord`** — "Utah Record - Public Meetings"
  (`https://www.youtube.com/@UtahRecord`, channel id `UC5hXeD66VUV_w655ionxaSA`). A
  statewide operation that mirrors public-meeting video for ~24 Utah cities/counties, one
  **playlist per city**. Millcreek's playlist:
  **`https://www.youtube.com/playlist?list=PL6IaTceX1fg-0pvUGP_x4hs-qhgd23d6-`**
  ("Millcreek City Meetings").
- **Same operator as `millcreek.openutah.org`** — OpenUtah is the searchable transcript
  front-end (its meeting pages embed these very `@UtahRecord` YouTube IDs, e.g. the
  2026-05-11 council meeting = `YInLevo1qiw`). OpenUtah advertised "106 indexed meetings,
  90 transcribed"; the YouTube playlist holds **92** video items — consistent.
- **Coverage: 2025-01-06 → 2026-06-22** (about 18 months). **92 videos: 58 City Council +
  34 Planning Commission.** Full-length recordings (roughly 60–120 min each). All carry
  **YouTube ASR auto-captions only** (`caption_type=asr`); **no human/manual caption track**
  on any video checked. English (`en-orig`) auto-sub retrieved.
- **This does NOT reach back to the 2016/2017 start of the minutes record** — video coverage
  begins Jan 2025. The pre-2025 deliberation exists only in the minutes PDFs. The city also
  streams meetings **live** on its own website player and **Facebook Live**
  (`facebook.com/MillcreekCity/`); no city-hosted video *archive* (downloadable back-catalog)
  was found beyond the `@UtahRecord`/OpenUtah mirror.

## What was retrieved (sample-only)

Per owner policy, the full 92-video map is in `index.csv`; **10 sample ASR caption tracks**
were downloaded (`stored_locally=yes`), spread across the range and both bodies:

| date | body | video_id |
|---|---|---|
| 2025-01-06 | City Council | Yzr937kKQdw |
| 2025-01-15 | Planning Commission | DAGAkdNeMfs |
| 2025-04-07 | City Council | Vrv9xrC_ViE |
| 2025-07-07 | City Council | PyOMZDEoVNo |
| 2025-09-17 | Planning Commission | gWrDiJnWlCQ |
| 2025-10-13 | City Council | Of5uHwfngY0 |
| 2026-01-12 | City Council | qBZPHM2_u-s |
| 2026-05-11 | City Council | YInLevo1qiw |
| 2026-05-14 | Planning Commission | wRH34LEE7VI |
| 2026-06-01 | City Council | w6TRAleTJHc |

Each: raw `.vtt` in `raw/`, cleaned `.md` in `text/` (headed with the ASR disclaimer),
provenance in `raw/_fetch_log.jsonl` (url, bytes, sha256, retrieved_utc).

## What the city itself does NOT publish

- **No city-owned meeting-video channel.** Millcreek's *own* YouTube,
  **`@millcreekutah3408`** ("Millcreek, Utah", 45 videos), is **PR/promotional only** —
  State-of-the-City addresses, Millcreek Common, construction time-lapses, business-series
  clips. **Zero council/PC meeting recordings.** (Beware the unrelated "Millcreek Township"
  YouTube channels — those are **Erie County, Pennsylvania**, not Utah.)
- So the meeting video that exists is entirely dependent on the third-party `@UtahRecord`
  mirror. If that mirror ever goes dark, the video record for 2025–2026 has no city-side
  redundancy (the official record remains the AgendaCenter minutes PDFs).

## Caveats

- **ASR quality, not an official record.** Auto-captions carry word errors, mis-spelled
  surnames, and no speaker attribution beyond YouTube's `>>` change markers. Every `text/`
  file is headed with this disclaimer. Do **not** extract votes or quote members verbatim
  from these — the authoritative record is `meeting_minutes/` / `planning_commission/`.
- **Title-labeling quirk:** `@UtahRecord` titles every Millcreek video "Millcreek City
  Council" or "Millcreek Planning Commission" from the playlist; the body column here follows
  that title. But the council convenes in-session as other agencies — e.g. the retrieved
  **2026-06-01 "City Council" video is actually a Utah Renewable Communities Agency (URCA)
  board meeting** (and the CRA likewise). Treat `body` as the mirror's label, not a verified
  body; confirm against the matching minutes doc before joining.
- **Same-day duplicates are real:** council meets 2nd & 4th Monday with a 5 p.m. work session
  + 7 p.m. regular meeting, so a single date can have two council videos (e.g. 2026-01-12,
  2026-01-26, 2026-02-09). Both rows are kept with distinct `video_id`; filenames disambiguate
  with the id suffix.

## OpenUtah / OpenUtah-API note (polite-scraper rule)

`millcreek.openutah.org` serves its **verbatim transcript text client-side behind
`robots.txt Disallow: /api/`** (also `/search`, `/admin`). Per the collection's polite rule
it is treated as a **metadata/summary source only** — it was used to *confirm* the
video→YouTube mapping and coverage counts, not bulk-harvested. The captions in this dataset
come from the **official YouTube ASR track via `yt-dlp`** (the sanctioned timedtext path), not
from scraping OpenUtah's API.

## Whisper (NOT run — user decides)

Whisper-over-video/audio was **not** run (expensive; user's call). If higher-fidelity
transcripts are ever wanted, the cleanest input is the same `@UtahRecord` YouTube video (or
the city's Facebook Live archive). High-value untranscribed candidates to prioritize would be
any **contested council votes** or **major rezone Planning Commission hearings** in 2025–2026
that the ASR sample doesn't already cover — pick them from `all_votes.csv` contested rows and
map to the `index.csv` video for that date.
