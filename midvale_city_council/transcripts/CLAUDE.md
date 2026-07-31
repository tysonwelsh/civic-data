# Midvale transcripts/ — meeting-video ASR captions (source type 5)

Additive dataset built by `/expand-city-sources`. **Sample-only**: the full 258-meeting
video→date map is enumerated in `index.csv`; 10 representative caption tracks are
downloaded, cleaned, and shipped as proof-of-quality. It does **not** modify any existing
dataset.

## What this is
- **Platform:** the official **Midvale City Government** YouTube channel
  (`UCLDszK2kMUHuc3-bV-BBslQ`) — the sole video source (no Granicus/Vimeo; the Utah
  Record third-party mirror does not carry Midvale). See `AVAILABILITY.md`.
- **Captions:** YouTube **auto-generated (ASR) only** — no manual track anywhere, so
  every row is `caption_type=asr`. These are error-prone and are **NOT** the official
  record; the clerk's minutes in `meeting_minutes/` and `planning_commission/` remain
  authoritative.
- **Coverage:** 258 governing-body meetings, **2020-04-08 → 2026-07-08**
  (Council 155 / PlanningCommission 101 / RDA 2).

## Layout
```
raw/                         retained originals + provenance
  <date>.en.vtt              the 10 downloaded auto-caption tracks, verbatim
  _enum_streams.tsv          yt-dlp --flat-playlist dump of /streams (268)  [literal \t]
  _enum_videos.tsv           yt-dlp --flat-playlist dump of /videos (11)    [literal \t]
  _all_titles.txt            deduped title list (parser QA)
  _sample_ids.txt            the 10 sampled video ids (persistent — captions get renamed)
  _ts_raw.txt / _timestamps.tsv  release_timestamp -> Denver date for the 8 undated meetings
  _utahrecord_titles.txt     proof the Utah Record mirror carries no Midvale
text/<date>.md               cleaned sample transcripts, each with the ASR header
index.csv                    SCHEMA_SPEC §9 transcripts contract (below)
AVAILABILITY.md              platform verdict, caption stats, Whisper candidates
build_transcript_index.py    (re)builds index.csv from the raw enum dumps
clean_captions.py            VTT -> text/<date>.md cleaner (dedup + ASR header)
```

## index.csv schema (§9 transcripts contract)
`date, title, body, video_url, video_id, caption_type, source_url, retrieved_date,
format, extraction_method, path` + one city extra **after** the contract:
- `date_source` — `title` (250 rows) or `release_timestamp` (8 undated meetings, dated
  via America/Denver conversion; each lands on the body's expected weekday).

Per-row semantics:
- `caption_type` = `asr` for all rows (channel has no manual captions).
- `format` = `caption` for the 10 downloaded samples (with a `path` to `raw/<date>.en.vtt`
  that exists on disk) / `na` for the 248 enumerated-but-not-downloaded meetings
  (caption exists on source; sample-only build — `path` blank).
- `body` ∈ `Council` / `PlanningCommission` / `RDA` (crosswalk-compatible with the vote
  datasets). Council includes specials, budget retreats, and the Annual Legislative
  Meeting; RDA is usually convened in-session under Council and rarely titled separately.

## Rebuild
```
python3 build_transcript_index.py     # re-derives index.csv from raw/_enum_*.tsv (idempotent)
python3 clean_captions.py             # re-cleans text/<date>.md for every format=caption row
```
`build_transcript_index.py` reads `raw/_sample_ids.txt` to know which rows are captions
(the `.vtt` files are renamed id→date on first run, so filename detection alone won't
survive a rebuild). To add samples: download `raw/<id>.en.vtt`
(`yt-dlp --write-auto-sub --sub-langs en --sub-format vtt --skip-download`), append the id
to `_sample_ids.txt`, and rerun both scripts.

## Linkage
Join to votes/minutes by **date + body**: Council/RDA video date ↔
`meeting_minutes/all_votes.csv`; PlanningCommission video date ↔
`planning_commission/all_votes.csv`. Council meets Tuesday (1st/3rd), PC Wednesday
(2nd/4th) — same join grid as `build_weeks.py`. A transcript captures the deliberation
the named-roll minutes summarize away; use it for *context*, never as a vote source.

## Caveats
- **ASR quality** — word errors throughout ("Midbell"/"Midvil" = Midvale). Preserved
  verbatim; never LLM-"corrected". Not an official record.
- **Sample-only** — 248 meetings have captions available on YouTube but not downloaded.
  A full harvest is a documented follow-up.
- **yt-dlp client quirk** — a few videos need player-client iteration to fetch captions
  (default `android_vr` says "no subtitles"; `web` flags "DRM") — see `AVAILABILITY.md`.
  Not a genuine caption gap.
- **`--print` literal `\t`** — the enum dumps are backslash-t delimited, not real tabs;
  the parser splits on `"\\t"`.
