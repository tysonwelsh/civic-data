# transcripts/ — South Salt Lake City meeting-video transcripts

Built 2026-07-13 by the `/expand-city-sources` skill (source type 5). **Additive dataset** —
nothing in `meeting_minutes/`, `planning_commission/`, `db/`, or `weeks/` was touched.

## ⚠ Why this dataset matters MORE here than in most cities — the coverage cliff

South Salt Lake's recorded minutes exist essentially only for **2020–early-2021** plus a few
sporadic recent meetings; **2021-mid → 2025 the PMN "Minutes" slot served agenda packets only**
(253 council agenda-only dates in `meeting_minutes/minutes_unrecovered.csv`; recorded PC minutes
don't begin until 2023-01-19). See the parent `CLAUDE.md`/`COVERAGE.md`.

**The YouTube channel begins 2022-12 and covers 2023–2026 densely.** So for the 2023–2025
gap-cliff years, **the meeting VIDEO (and its ASR caption) is frequently the ONLY substantive
record of what the Council/PC actually deliberated and decided.** That makes the untranscribed
gap-year videos the single highest-value Whisper target in this repo — see `AVAILABILITY.md`.

## Source — ONE platform: YouTube

- **Official channel: "South Salt Lake City"** — `https://www.youtube.com/@SouthSaltLakeCity`
  (channel id `UCnIf0PqrH3cERoBB-vyhrbA`). 291 uploads; **269 are body meetings**, the other 22
  are promotional clips (State of the City, Mural Fest, celebrations, "Stories of…") kept in
  `channel_videos.csv` with `is_meeting=no`, excluded from `index.csv`.
- No separate `/streams` tab exists (live archives land on `/videos`). Zoom is the live host
  (per recon); the durable public archive is this YouTube channel.
- **"Utah Record" mirror** (`UC5hXeD66VUV_w655ionxaSA`) was checked — it mirrors Draper/Lehi
  and carries **ZERO** South Salt Lake videos. Not a source.
- **Captions are YouTube ASR (`en`, automatic).** No manual/human caption track exists on any
  video. Availability was ground-truthed per video by a batched `--list-subs` probe, not assumed.

## The yt-dlp access gotcha (READ before re-running)

This machine's yt-dlp (2026.06) has **no default JS runtime**, and the default/`web`/`mweb`
YouTube player clients hit the **PO-token wall** — they falsely report "has no automatic
captions". Enumeration (`--flat-playlist`) works, but per-video caption listing/fetch needs:

```
yt-dlp --js-runtimes node --extractor-args "youtube:player_client=android" ...
```

The **`android`** (or `ios`) player client is the one that reliably exposes and downloads the
`en` ASR track. `node` is present at `/opt/homebrew/bin/node`. All caption work here used that
combination.

## Files

```
index.csv            §9 transcripts contract header
                     (date,title,body,video_url,video_id,caption_type,source_url,
                     retrieved_date,format,extraction_method,path) + extras:
                     platform, meeting_kind, date_source, duration_s.
                     One row per MEETING video (269). Caption-bearing rows carry
                     caption_type=asr/format=caption; the 10 fetched samples also carry a path.
channel_videos.csv   full channel map (291 videos; is_meeting flag; 22 promo clips).
raw/<date>_<id>.en.vtt   the 10 fetched sample ASR caption tracks (+ _fetch_log.jsonl provenance).
text/<date>_<body>_<kind>.md   10 cleaned sample transcripts, headed "AUTOMATIC TRANSCRIPTION — ASR…".
parse_titles_ssl.py  enum_videos.psv -> channel_videos.csv (title -> date + body + meeting_kind).
clean_captions_ssl.py  .vtt -> cleaned markdown (dedupes rolling-caption triples, strips
                     <c>/timestamp tags, html.unescape for &gt;&gt; markers).
build_index_ssl.py   assembles index.csv from channel_videos.csv + the probe + fetched samples.
enum_videos.psv      raw `yt-dlp --flat-playlist` dump (id|title|duration).
_listsubs_raw.txt    batched `--list-subs` output (android client) — per-video caption ground truth.
_meeting_urls.txt / _samples.txt   working lists (269 meeting URLs / the 10 sample picks).
```

## How dates + bodies were derived (read before joining)

- **`date`** — parsed from the video TITLE, which carries the meeting date in every meeting
  upload ("2026 7 8 City Council Regular Meeting" / "2023-7-13 Planning Commission"). `date_source`
  = `title` for all 269. `--flat-playlist` returns NA timestamps, so no `release_timestamp` probe
  was needed (titles are complete). No date was fabricated — a video without a parseable leading
  date is a non-meeting promo clip (`is_meeting=no`, blank date).
- **`body`** (+ `meeting_kind`) — classified from the title keyword:
  `Planning Commission` → **PlanningCommission** (PC); `Civilian Review Board` →
  **CivilianReviewBoard** (CRB); `Redevelopment Agency`/`RDA` → **RDA**; `Board of Canvassers` →
  **CityCouncil** (BoC); `Council … Work` → **CityCouncil** (WM); `Council … Regular`/bare →
  **CityCouncil** (RC). Matches the core repo's `body`/`meeting_kind` vocabulary.
- **join** on `(date, body)` to `meeting_minutes/` (Council + RDA), `planning_commission/`
  (PC Thursday), or — for CRB — nothing in the core repo (CRB isn't a land-use body). Same date
  can carry a Work + Regular Council + RDA video (the SSL Wednesday triple); `meeting_kind`
  disambiguates. `index.csv` is one row per video.

## Fetching more captions (Whisper is a SEPARATE, owner-decided step)

To fetch a caption that the probe flagged as available (`format=caption`, no `path` yet):
```
yt-dlp --js-runtimes node --extractor-args "youtube:player_client=android" \
  --write-auto-sub --sub-lang en --sub-format vtt --skip-download \
  -o "raw/<date>_<id>.%(ext)s" "https://www.youtube.com/watch?v=<id>"
python3 clean_captions_ssl.py raw/<date>_<id>.en.vtt text/<date>_<Body>_<kind>.md <date> <Body> <id>
```
Only 10 samples were fetched by design (sample-only). The remaining caption-bearing rows are
fetchable on demand with the command above — no Whisper needed for those (YouTube already ASR'd
them). **Whisper** is only for any video that has NO caption track; see `AVAILABILITY.md` for the
(short) list and the gap-year prioritization.

## Caveats

- **ASR, not a record**: no speaker labels; proper nouns (member names, "South Salt Lake",
  street/case/ordinance numbers) are frequently misrecognized. Never quote as the official record.
  Corpus screen (`screen_corpus.py`) on the 10 samples: 0 outliers, dict_ratio ~0.85 (normal ASR).
- **Caption availability is READ from the probe, never inferred.** `caption_type=asr` means the
  batched `--list-subs` listed an `en` automatic track for that exact video id.
- yt-dlp 2026.06 deprecation warning "No supported JavaScript runtime" — worked around with
  `--js-runtimes node`; a future refresh may want `deno` installed. The PO-token/player-client
  gotcha above is the real trap — use the `android` client.
