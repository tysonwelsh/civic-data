# Alta — meeting-video transcripts: availability

**As-of:** 2026-07-13 · **Source type 5** (`expand-city-sources`) · dataset floor 2020 (town history to 1970).

## Verdict

**Alta is NOT the caption-less audio-first town the recon anticipated.** Two platforms carry
its meetings, and one of them **does** carry captions:

| Platform | Handle / URL | Items | Range | Captions? |
|---|---|---|---|---|
| **YouTube** | `@townofalta2175` (`/videos` + `/streams`) | **172** (13 uploads + 159 streams) | 2020-04-04 → 2026-07-08 | **YES — auto-generated English ASR on every meeting** |
| **SoundCloud** | `soundcloud.com/townofalta` | **348** tracks | 2013-12 → 2026-07 | **NO** (audio only — Whisper lead) |
| Utah Record mirror | `UC5hXeD66VUV_w655ionxaSA` | 78 videos, **0 Alta** | — | n/a (no Alta uploads) |

The town live-streams meetings on YouTube (confirmed on the town's own `/live-stream/` page)
and separately posts the audio recordings to SoundCloud. **The two overlap but are not
identical** — SoundCloud reaches back to 2013 and includes recordings that never went to
YouTube; YouTube begins April 2020.

## YouTube captions — the finding

Every meeting video probed carried YouTube **auto-generated ("ASR") English captions**
(`en` + `en-orig`), auto-translatable into ~200 languages. **No human/manual caption track**
exists on any video (all are `automatic captions`, none listed under `Available subtitles`).
Availability was confirmed on **24 distinct videos** spanning 2020→2026 (10 `--list-subs`
probes + 14 full downloads); it is a channel-wide YouTube default, not a per-video upload.

- **caption_type = `asr`** everywhere (word errors expected; NOT an official record — the
  clerk's minutes in `meeting_minutes/` remain authoritative).
- These captions are the deliberation the terse Alta minutes summarize away — high value on a
  small-town council where much business is discussed but only tallied in the minutes.

### What was stored (SAMPLE — per task scope "sample-only")

**14 caption files downloaded** (raw `.en.vtt` + cleaned `text/<date>.md` with the mandatory
ASR header), a representative Council+PC spread across the full range — one or two per year,
both bodies:

```
2020-04-08 Council   2023-09-13 Council   2025-01-08 Council
2020-10-13 PC        2023-11-08 Council   2025-09-24 PC
2021-05-12 Council   2024-01-10 Council   2025-11-12 Council
2022-08-10 Council   2024-08-28 PC        2026-02-11 Council
                                          2026-06-17 Council
                                          2026-07-08 Council
```

The remaining **158 YouTube items are cataloged in `index.csv`** with their video→date map,
`caption_type=asr`, `stored=no`, `format=na` (caption exists on the source but not stored
locally). `screen_corpus.py` on the 14 stored transcripts: 0 read errors, 0 dict/split/weird
outliers (dict_ratio ~0.87 — normal conversational ASR).

### Proposed follow-up (NOT executed — user decides)

**Full ASR backfill:** the other ~120 substantive meeting videos (100 Council, 33 PC, 27
Budget across 2020→2026, minus dog-drawings/tests) all carry `en` ASR and can be pulled with
the same `yt-dlp --write-auto-sub` path — a bounded, no-cost harvest (~1.5 MB VTT each). Not
run here because the task scoped captions to a sample. Note the YouTube throttle gotcha below.

## SoundCloud — audio inventory (Whisper leads, NOT transcribed)

`soundcloud_audio.csv` (sidecar) catalogs **all 348 tracks**, 2013-12 → 2026-07:
**205 Council, 84 Planning Commission, 27 Budget, 4 Other, 28 Unknown**; **316 are genuine
meeting recordings** flagged `whisper_candidate=yes` (174 in-scope ≥2020; 147 pre-2020 —
below the dataset floor but the only audio record of Alta's 2013–2019 governance).

- **SoundCloud audio has NO captions** — per the skill's audio-only-city branch it is a
  **Whisper transcription lead only**. Its verbatim text was **not** bulk-grabbed. **No audio
  files were downloaded** (URLs + titles catalogued; the bytes are public + re-fetchable).
- **Whisper is PROPOSED, not run** (expensive; user decides). Highest-value candidates: any
  in-scope meeting **not** on YouTube's caption path — e.g. SoundCloud-only work sessions and
  special meetings, and the entire **2013–2019 pre-YouTube era** (147 tracks) if history below
  the 2020 floor is ever wanted.
- 17 sidecar tracks are undated (16 pre-2020 non-standard titles like `TOAMP3_0065.mp3`; 1 is
  a title typo "April **207** 2021") — fully identified by title + URL, just no parsed ISO date.

## Gaps / honest notes

- **Not every meeting is on YouTube** — the channel starts 2020-04; PC/Council meetings
  2013–2019 exist **only** on SoundCloud (audio). Sparse-town cadence means low counts are
  correct, not a miss.
- **Duplicate uploads are real** — the same meeting sometimes appears as two YouTube video_ids
  (a short truncated first attempt + the full stream) or SoundCloud "Part 1/Part 2" splits.
  Every distinct id is kept as its own row (honest — none deduped away).
- **Dates for undated YouTube streams** (63 of 172) come from `release_timestamp` converted to
  America/Denver (`date_source=release_timestamp(Denver)`); the rest are parsed from the video
  title (`date_source=title`). Release-timestamp dates are the stream date, ~the meeting date.
- **`caption_type=asr` on non-stored rows is source-attested** (channel-wide ASR verified on 24
  videos across the range), not individually re-probed per row — re-verify at download time.
