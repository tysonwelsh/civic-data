# Ogden City Council — meeting-video transcripts (captions): availability

_As of 2026-07-05. Additive dataset. Sample-only build (owner decision 2026-07-05):
the full video→date map is the deliverable; a ~10-meeting ASR caption sample was
downloaded to prove the pipeline. Nothing here is an official record._

## Source found

**Ogden City Council YouTube channel** — the official council video source.
- Channel: <https://www.youtube.com/channel/UC5SkSjDVRckazUP4nEkYMLA>
- City landing pages that point at it: <https://www.ogdencity.gov/1203/Live-Stream-Meetings>,
  <https://ogdencity.com/livestream>, <https://ogdencity.com/councilmediaroom>.
- Council streams live Tuesdays 6 p.m.; regular Council meets 1st & 3rd Tuesdays
  (2nd Tuesday = RDA; extra 4th-Tuesday sessions occur). Meetings are archived on the
  channel afterward.

Both channel tabs were enumerated with `yt-dlp --flat-playlist` and are **disjoint**:
- `/videos` tab — 401 entries (informational clips + some older meetings)
- `/streams` tab — 282 entries (the bulk of recorded meetings, back to June 2020)
- **683 unique videos total.**

### Other sources checked
- **`ogden.openutah.org` / Granicus / Swagit / CivicClerk video portal** — none found for
  Ogden. The city's own pages route all archived video to the YouTube channel above.
- **"Ogden City Utah" YouTube channel** (`UCnV0ROTi1bSTch6at6lAzcw`) — a general city
  channel, not the council meeting archive; not used.
- Captions on the council channel are **YouTube ASR auto-captions** (`en-orig`), the only
  caption path available — Ogden publishes no human transcript. `en` and `en-orig` tracks
  were byte-identical on the sample.

## The map (`channel_videos.csv`)

All 683 videos, both tabs, with a date parsed from each title and a `minutes_match` flag
against `meeting_minutes/minutes_index.csv`.

- **369** are council/RDA/MBA/work-session meeting videos.
- **320** of those carry a parseable date; **49** are undated (mostly generic
  "Ogden City Council Live Stream" placeholders and untitled clips).
- **297** dated meeting videos match a date already in the minutes index.
- Dated meeting-video coverage runs **2018-05-01 → 2026-06-16**; within the 2020–2026
  target window by year: 2020: 27, 2021: 34, 2022: 37, 2023: 49, 2024: 66, 2025: 66,
  2026: 40 (through mid-June 2026, past the minutes cutoff of 2026-05-19).

## Sample retrieved (`raw/` + `text/`)

10 ASR caption files for the most recent regular **Ogden City Council Meeting** videos:
2026-01-06, 01-20, 02-03, 02-10, 02-17, 03-03, 04-07, 04-21, 05-05, 05-12.
Each `raw/<date>_<slug>.vtt` is verbatim YouTube VTT; `text/<date>_<slug>.md` is a
de-duplicated plain-text render headed with the ASR disclaimer. sha256 of every raw file
is in `raw/_fetch_log.jsonl`.

**Coverage window of the sample: 2026-01-06 → 2026-05-12. Cutoff: this is a sample, not a
backfill** — the other ~310 dated meeting videos are mapped but not downloaded.

## Honest gaps

- **2026-05-19 regular meeting** has a video (`gbl1FhEiQ_0`) but **no auto-captions yet**
  (only `live_chat`). Recorded in `index.csv` as `format=na`. YouTube ASR for very recent
  and very long streams can lag or never generate.
- Caption availability was confirmed on the sampled meetings only. A full per-video caption
  probe across all 369 meeting videos was **not** run (sample-only policy) — some older
  meetings may also lack ASR tracks.
- Undated/placeholder "Live Stream" entries carry no date and are left with blank
  `parsed_date` in the map.

## Whisper candidates (proposed only — NOT run)

If local ASR is added later, highest value:
1. **2026-05-19 Council Meeting** — minutes exist, YouTube ASR absent. Direct gap fill.
2. **June 2026 sessions** (June 1, 2, 9, 16; ids in `channel_videos.csv`) — past the
   minutes cutoff, no minutes yet; transcripts would be the only text record.
3. A **full caption-availability sweep** of the 320 dated meeting videos to enumerate the
   complete uncaptioned set before committing Whisper compute.
