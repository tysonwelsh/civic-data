# transcripts/ — Holladay City meeting-video transcripts

Built 2026-07-13 by the `/expand-city-sources` skill (source type 5). **Additive dataset** —
nothing in `meeting_minutes/`, `planning_commission/`, `db/`, or `weeks/` was touched.

## Source — two platforms, split by era (read `AVAILABILITY.md` first)

- **SuiteOne portal (2025+) — the current meeting-video host.**
  `https://holladayut.suiteonemedia.com/`. Each `/event/?id=<n>` page embeds a JWPlayer whose
  source is a plain **S3 MP4** (`s3.amazonaws.com/suiteone.holladayut.videofiles/<hash>.mp4`).
  **No caption track exists** on any SuiteOne video (verified: no `.vtt`, no `tracks:[]`).
  **75 video-flagged events, 2025-01-02 → 2026-07-07** → all `format=na`, `caption_type=none`,
  Whisper candidates.
- **YouTube "Holladay City" `@holladaycity4925` (`UCpePWrbddeqj42k8dodt-og`) — a shallow
  2020-2021 relic.** 65 videos total, only **6 genuine body meetings** (a Feb-2021 batch
  upload of Dec-2020/Jan-2021 meetings); the rest is PR/history content. The 6 meetings carry
  **YouTube ASR captions**, all fetched.
- The **"Utah Record" mirror** (`UC5hXeD66VUV_w655ionxaSA`) was checked — it mirrors
  Draper/Lehi, **zero Holladay** — not a source.
- **Gap:** no meeting video on any platform for **2021-02 → 2024** (YouTube stops 2021-01,
  SuiteOne starts 2025). Honest publishing gap; minutes still cover the era via PMN.

## Files

```
index.csv            §9 transcripts contract header
                     (date,title,body,video_url,video_id,caption_type,source_url,
                     retrieved_date,format,extraction_method,path) + extras:
                     platform, date_source, suiteone_event_id.
                     81 rows: 6 format=caption (YouTube, fetched) + 75 format=na (SuiteOne).
channel_videos.csv   full YouTube channel map (65 videos; is_meeting flag; 59 PR clips).
raw/<date>_<id>.en.vtt   6 fetched YouTube ASR caption tracks (+ _fetch_log.jsonl provenance).
text/<date>.md       6 cleaned transcripts, headed "AUTOMATIC TRANSCRIPTION — ASR…".
clean_captions_holladay.py   .vtt → cleaned-markdown (dedupes rolling-caption triples,
                     strips <c>/timestamp tags, html.unescape for &gt;&gt; markers).
parse_suiteone.py    _suiteone_home.html → _suiteone_events.csv (181 events, video flag, body).
resolve_suiteone_video.py   fetches each video event page → _suiteone_video.csv (MP4 hash).
build_index_holladay.py     assembles index.csv from the 6 YouTube rows + _suiteone_video.csv.
_suiteone_home.html  portal snapshot (parser input). _suiteone_events.csv / _suiteone_video.csv
                     = the 181-event listing and the 75 resolved video→MP4 maps.
```

## How dates + bodies were derived (read before joining)

- **`date_source`** — YouTube: `title` (3), `description` (2), `asr_spoken` (1: the
  2021-01-05 PC video, dated from the chair's call-to-order at 0:27 — ASR misheard the year;
  it is the 1st-Tuesday PC meeting). SuiteOne: `suiteone` (portal-listed event date).
  `flat-playlist` gives NA timestamps and YouTube `upload_date` is the Feb-2021 batch date —
  neither is the meeting date, so it was never used for YouTube dating.
- **`body`** — from the event/video title. `City Council & RDA Meeting` → `Council` (RDA sits
  in-session inside the council evening, matching the core repo's `body` design); standalone
  `RDA Board Meeting` → `RDA`; `Local Building Authority` → `LBA`. Other bodies present on
  SuiteOne: ArtsCouncil, AdminHearingOfficer, Ceremony (swearing-in). Council meets THURSDAY,
  PC modal-Tuesday — both are title-dated, so no weekday inference was needed.
- **join** on `(date, body)` to `meeting_minutes/` / `planning_commission/` minutes;
  `index.csv` is one row per **video** (SuiteOne `video_id` = the S3 MP4 hash; YouTube
  `video_id` = the watch id).

## Fetching more captions

YouTube (already exhausted — 6/6 fetched):
```
python3 -m yt_dlp --write-auto-sub --sub-lang en --sub-format vtt --skip-download \
  -o "raw/<date>_<id>.%(ext)s" "https://www.youtube.com/watch?v=<id>"
python3 clean_captions_holladay.py raw/<date>_<id>.en.vtt text/<date>.md <date> <Body> <id>
```
SuiteOne has **no captions** — the 75 `format=na` rows are **Whisper candidates**
(`AVAILABILITY.md`, owner decision). Fetch a SuiteOne MP4 via the `video_url` column
(`…/videofiles/<video_id>.mp4`) and run Whisper; then flip the row to `format=caption`,
`caption_type=asr`, `extraction_method=whisper`.

## Caveats

- **ASR, not a record**: no speaker labels; proper nouns (names, "Holladay"→"holiday",
  ordinance/case numbers, even a meeting YEAR) misrecognized. Never quote as the official
  record.
- `caption_type=none` (75 SuiteOne rows) is verified from player markup, not inferred.
- yt-dlp warned "No supported JavaScript runtime" (2026-06 build deprecation) — caption
  fetches still succeeded; a future refresh may need `deno` installed.
- Re-running `resolve_suiteone_video.py` re-fetches 75 event pages (~90s, throttled ≥1s);
  one event (id 3045) timed out on the first pass and is patched in `build_index_holladay.py`.
