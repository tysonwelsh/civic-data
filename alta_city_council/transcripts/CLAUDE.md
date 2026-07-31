# Alta — `transcripts/` (meeting-video transcripts, source type 5)

Additive dataset from the `expand-city-sources` skill. Captures the spoken deliberation that
Alta's terse minutes summarize away. **Read `AVAILABILITY.md` first** — it holds the platform
verdict, caption stats, and the Whisper-candidate proposal. Built 2026-07-13.

> **NOT an official record.** All transcripts here are **ASR (auto speech recognition)** — word
> errors are expected. The authoritative meeting record is the clerk's minutes in
> `meeting_minutes/` / `planning_commission/`. Never quote a transcript as the vote or the
> official language.

## Two platforms (see recon §"Audio recordings")

- **YouTube `@townofalta2175`** — live-streamed meetings, 2020-04 → present. **Every meeting
  video carries YouTube auto-generated English (`en`) ASR captions.** This is the caption
  source. (Recon expected zero captions; that was wrong — captions are channel-wide.)
- **SoundCloud `soundcloud.com/townofalta`** — meeting **audio** back to 2013, **no captions**.
  A Whisper lead only (audio-only-city branch of the skill). Catalogued in the
  `soundcloud_audio.csv` sidecar; **not transcribed, not downloaded**.
- The **"Utah Record" mirror** channel (`UC5hXeD66VUV_w655ionxaSA`) has **0 Alta uploads** —
  checked and ruled out.

## Files

```
raw/<date>_<videoid>.en.vtt   the 14 downloaded YouTube auto-caption tracks (verbatim VTT)
text/<date>.md                cleaned, de-duplicated transcript + mandatory ASR header
index.csv                     §9 transcripts contract — the FULL YouTube video->date map (172 rows)
soundcloud_audio.csv          SIDECAR — all 348 SoundCloud audio tracks (Whisper leads)
AVAILABILITY.md               verdict, caption stats, Whisper candidates (propose-only)
clean_vtt.py / parse_dates.py / build_index.py   the build scripts (reproducibility)
```

## `index.csv` schema

Starts with the exact **SCHEMA_SPEC §9 transcripts contract header**:
`date, title, body, video_url, video_id, caption_type, source_url, retrieved_date, format,
extraction_method, path` — then city extras: `platform, tab, duration_sec, stored,
captions_available, date_source, date_precision, title_raw`.

- **172 rows = every YouTube item** (13 `/videos` + 159 `/streams`), 2020-04-04 → 2026-07-08.
  Body mix: 100 Council, 33 PlanningCommission, 27 BudgetCommittee, 9 Other, 3 Unknown.
- `caption_type` = **`asr`** on all rows (YouTube auto-captions; no manual track anywhere).
- **`stored=yes` (14 rows)** → `format=caption`, `path=raw/<date>_<id>.en.vtt`, a cleaned
  `text/<date>.md` exists. **`stored=no` (158 rows)** → `format=na`, blank path (the caption
  exists on YouTube but was not downloaded — see AVAILABILITY "sample-only" scope + backfill).
- `date_source` = `title` (parsed from the video title) or `release_timestamp(Denver)` (for the
  63 undated streams, the stream time converted to America/Denver ≈ the meeting date).

## `soundcloud_audio.csv` (sidecar)

All **348** SoundCloud tracks, 2013-12 → 2026-07: `date, date_precision, title, body, url,
track_slug, source_url, platform, caption_type(=none), whisper_candidate, notes`. **316** are
genuine meeting recordings flagged `whisper_candidate=yes`. Kept OUT of `index.csv` because it
has no captions — it is a transcription lead, not a transcript source. Not validated by
`validate_dataset.py` (only `index.csv` is).

## How it was built (reproducible)

```bash
# enumerate (JS channel pages are unscrapable; use yt-dlp flat-playlist)
yt-dlp --flat-playlist --dump-json https://www.youtube.com/@townofalta2175/videos  > yt_videos.jsonl
yt-dlp --flat-playlist --dump-json https://www.youtube.com/@townofalta2175/streams > yt_streams.jsonl
yt-dlp --flat-playlist --dump-json https://soundcloud.com/townofalta               > sc_tracks.jsonl
# dates for undated streams: release_timestamp -> America/Denver
yt-dlp --skip-download --print "%(id)s ... %(release_timestamp)s ..." <ids>
# download a caption (ASR), then clean
yt-dlp --write-auto-sub --sub-lang en --sub-format vtt --skip-download -o 'raw/<date>_<id>.%(ext)s' <url>
python3 clean_vtt.py raw/<date>_<id>.en.vtt text/<date>.md <date> <id> "<title>" <body> <url> <retrieved>
python3 build_index.py   # writes index.csv + soundcloud_audio.csv
```

- `clean_vtt.py` strips YouTube's inline word-timing tags and the rolling-caption duplicates,
  keeps periodic `[HH:MM:SS]` anchors, and prepends the ASR-warning header. Source wording is
  preserved verbatim — NOT LLM-cleaned (implausibly clean ASR would be a hallucination signal).

## Gotchas learned here (candidates for the SKILL)

- **YouTube throttles rapid separate caption fetches.** A shell loop of one `yt-dlp` process
  per video got the first ~2 then silently wrote nothing (no error with output suppressed).
  **Fix: pass many URLs to ONE `yt-dlp` invocation with `--sleep-requests 4`** — the shared
  session downloaded all 14 cleanly. Add this to the SKILL's transcripts note.
- **`yt-dlp --print "...\t..."` writes a LITERAL backslash-t**, not a tab — split on `\\t`.
- **No JS runtime + "impersonation" warnings are non-fatal** — caption downloads succeeded
  anyway on this host (deno/curl-impersonate not installed).
- Channel meeting videos have **title typos** (`Planninng`, `Commmssion`, `Commisison`) — the
  body classifier keys on the substring `planning`/`commiss` to catch them.

## Caveats for analysis

- ASR only — see the header warning; join transcripts to minutes/votes by **meeting date**
  (Wednesday council cadence; PC 4th-Wed as-needed). Alta's mayor VOTES (max roll 5) — but
  don't infer votes from a transcript; use `meeting_minutes/all_votes.csv`.
- `stored=no` rows are a catalog, not content. `format=na` there means "not on disk," not "no
  caption exists" — the caption is fetchable (see AVAILABILITY backfill proposal).
- This dataset was **NOT** loaded into `cities.db` in this run (per task scope: no
  `build_cities_db.py`). A later federated build will pick `index.csv` into the `document`
  catalog.
