# transcripts/ — Bluffdale meeting video transcripts (Source 5)

**Status: honestly unrecovered — video exists, no captions.** Built 2026-07-12 by the
`expand-city-sources` skill (Source 5). Bluffdale posts meeting **video** but no
**caption/transcript** track on any official path, so this dataset catalogues the videos
and records the gap rather than shipping caption text. Read `AVAILABILITY.md` for the full
check log; this file is the build/schema record.

## One-line summary

- Video platform: **CivicClerk** (`bluffdaleut.portal.civicclerk.com`; MP4s on
  `cpmedia.azureedge.net/bluffdaleut/<hash>.mp4`) — **not YouTube**.
- **No YouTube channel** for Bluffdale (the `yt-dlp --write-auto-sub` path has no target);
  the @UtahRecord Utah-meetings mirror does not carry Bluffdale.
- **No captions**: CivicClerk `closedCaptionFileName=null` / `closedCaptionStatus=none` and
  `youtubeVideoId=""` on all 15 media events; `yt-dlp --list-subs` → "has no subtitles".
- Captions retrieved: **0**. Videos catalogued: **15** (2026-03-04 → 2026-07-08).

## Files

```
raw/civicclerk_events.json   verbatim CivicClerk Events API dump (the video->date map +
                             the null closed-caption fields) — the provenance original
raw/_fetch_log.jsonl         url / http / bytes / sha256 / retrieved_utc for that fetch
text/                        EMPTY — no ASR captions exist to clean (see AVAILABILITY.md)
index.csv                    §9 transcripts contract header, HEADER-ONLY (0 caption rows)
unrecovered.csv              the 15 videos with no caption track (format=na + reason)
AVAILABILITY.md              what was checked, what exists, Whisper proposal, reproduce steps
CLAUDE.md                    this file
```

## Schemas

`index.csv` — exact SCHEMA_SPEC.md §9 transcripts contract header (header-only here; a row
is added only when a real caption is retrieved):
```
date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,extraction_method,path
```
- `caption_type` ∈ `manual` / `asr`; `format=caption` for a retrieved caption (`path`
  → `raw/<date>.vtt`). None exist yet, so there are no data rows.

`unrecovered.csv` — the honest gap log (one row per video with no caption):
```
date,title,body,video_url,video_id,caption_type,source_url,retrieved_date,format,reason
```
- `video_id` = `civicclerk:<eventId>` (CivicClerk has no YouTube ids); `video_url` = the
  Azure-CDN MP4; `source_url` = the CivicClerk portal event page; `caption_type` blank
  (none); `format=na`.

## Method / provenance

1. **Channel discovery** — WebSearch + `yt-dlp ytsearch` for a Bluffdale YouTube channel
   (none; only third-party clips). Enumerated @UtahRecord (`--flat-playlist`, 78 videos) —
   Draper/Lehi/Layton/Sandy only.
2. **Platform** — the city *Streaming-Videos* page embeds the CivicClerk portal; recordings
   are Azure-CDN MP4s.
3. **Enumeration** — GET-only, paged CivicClerk Events API
   (`.../v1/Events?$orderby=startDateTime desc`, followed `@odata.nextLink`), retained
   verbatim at `raw/civicclerk_events.json` (16 events; 15 with `hasMedia`). Every media
   event's closed-caption fields are null and `youtubeVideoId` empty.
4. **Caption probe** — `yt-dlp --list-subs` on the newest council MP4 → "has no subtitles".

## Caveats / how to use

- **This is NOT a transcript corpus** — there is no ASR text to search. Do not expect
  `fts_*` transcript passages for Bluffdale; the `document` catalog will show these as
  video-only entries at most.
- **Never fabricate**: the empty `text/` and header-only `index.csv` are honest, not
  incomplete extraction. Deliberation-level text requires the Whisper run proposed in
  `AVAILABILITY.md` — **not run here** (user decides).
- **Video window is 2026-only** (CivicClerk retention). Pre-2026 Bluffdale meetings are
  minutes-only; there is no earlier video to transcribe.
- **OpenUtah** (`bluffdale.openutah.org`) hosts its own ASR transcripts of these same
  recordings but serves the text behind `robots.txt Disallow: /api/` — metadata/summary
  only under the polite rule, never bulk-grabbed by this build.
- Polite, GET-only throughout; official caption path only (no ToS-violating scraping).
  Raw API response retained.
