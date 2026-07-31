# transcripts/ — Cottonwood Heights City meeting-video transcripts (YouTube ASR)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 5). **Additive dataset**
— nothing in `meeting_minutes/`, `planning_commission/`, `public_comments/`, `db/`, or
`weeks/` was touched.

## Source

- **Channel:** Cottonwood Heights — `@CottonwoodHeights`, channel id
  **`UCcOhqM97RmMrEpUz_6L84Cw`** (`https://www.youtube.com/channel/UCcOhqM97RmMrEpUz_6L84Cw`).
  Meetings are livestreamed and archived here; the city portal
  (Granicus/CivicPlus **CivicEngage Central**, `showpublisheddocument`) hosts **minutes PDFs
  only, no video** — so unlike a PrimeGov city there is **no portal videoUrl field**; the
  video→meeting map is derived from **video titles + a timestamp probe**.
- **Enumeration:** `yt-dlp --flat-playlist` over `/streams` (556) + `/videos` (139) → **695
  unique videos**, of which **511 are meeting videos** (the rest are PR/community clips +
  recurring schedule-placeholder stubs, catalogued in `channel_videos.csv` only).
- **Captions:** YouTube **automatic (ASR) English** via
  `yt-dlp --write-auto-sub --write-sub --sub-lang en --sub-format vtt --skip-download`
  (official timedtext path only). No manual caption tracks exist (sample-verified 2018→2026).
  `caption_type=asr` everywhere. All 10 sampled videos fetched first-try on the default
  `android_vr` client — **no `player_client` iteration needed, no Whisper needed.**

## Files

```
index.csv           §9 transcripts contract header (date,title,body,video_url,video_id,
                    caption_type,source_url,retrieved_date,format,extraction_method,path)
                    + extras: duration_sec,tab,date_source. 511 rows: 10 format=caption
                    (fetched), 501 format=na (mapped_not_fetched).
channel_videos.csv  full channel map (695 rows incl. 184 NonMeeting/Other PR videos;
                    is_meeting flag).
raw/                10 fetched .vtt caption tracks, named <date>_<video_id>.en.vtt (5.2 MB).
text/<date>.md      10 cleaned transcripts, headed "AUTOMATIC TRANSCRIPTION — ASR…"
                    (~108.7k words total).
ch_transcripts_build.py  enum → channel_videos.csv + index.csv (title/timestamp date parse,
                    body classifier). Reads fetched.csv to mark the caption rows.
ch_clean_vtt.py     the .vtt → cleaned-markdown converter (dedupes rolling-caption
                    repetition, strips <c>/timestamp tags, HTML-unescapes >> speaker markers).
enum_streams.tsv / enum_videos.tsv  raw yt-dlp flat-playlist dumps (LITERAL \t separator —
                    the yt-dlp --print gotcha; ch_transcripts_build.py splits on r"\t").
undated_ids.txt / undated_probe.tsv  the 44 undated meeting videos + their timestamp probe.
sample_ids.txt / sample_urls.txt / fetched.csv / fetch_samples.log  the caption-sample fetch.
AVAILABILITY.md     platform verdict, caption stats, gap analysis, fetch backlog.
```

## Rebuild / fetch-more recipe

```
# regenerate channel_videos.csv + index.csv from the enum dumps (+ fetched.csv):
python3 ch_transcripts_build.py

# fetch one more meeting's captions (find date/body/id in channel_videos.csv or index.csv):
yt-dlp --write-auto-sub --write-sub --sub-lang en --sub-format vtt --skip-download \
  --sleep-requests 4 -o "raw/<date>_<video_id>.%(ext)s" \
  "https://www.youtube.com/watch?v=<video_id>"
python3 ch_clean_vtt.py raw/<date>_<video_id>.en.vtt text/<date>.md <date> <Body> <video_id>
# then add "<video_id>,raw/<date>_<video_id>.en.vtt" to fetched.csv and rerun the build.
```

## How dates and bodies were derived (read before joining)

- **`date_source`** — `title_iso` (111: "2026-07-07 Council…"), `title_mdy` (333: the
  2018–2023 "Cottonwood Heights City Council Meeting 8-28-18 #1" style), `title_monthname`
  (22: "Aug. 3, 2021"), `title_ymd` (1), and **`yt_release_ts_local`** (44: the undated
  "…Meeting - Live" streams, dated from `release_timestamp` converted to **America/Denver
  (UTC-7)** — never the raw UTC `upload_date`, to avoid the near-midnight day-roll).
- **`body`** — title keyword, precedence **Joint → CDRA → PlanningCommission → ARC → Council**
  (a video that says both "council" and "planning commission" is Joint; "renewal agency"/
  "CDRA"/"redevelopment" is CDRA; "architectural review"/"ARC" is ARC). Counts: Council 372,
  PlanningCommission 93, CDRA 32, Joint 2, ARC 12.
- **CDRA** = the Council's in-session Community Development & Renewal Agency (matches the repo's
  `body=CDRA` in `meeting_minutes/all_votes.csv`); sometimes it is a standalone stream.
- **ARC** (Architectural Review Commission) videos are **outside the core minutes/vote scope**
  — this repo has no ARC vote dataset — but are catalogued honestly.
- **`tab`** — which channel tab the video came from (`streams` / `videos` / `streams+videos`).

## Joining to the rest of the repo

- Council meets **Tuesday (1st & 3rd)**, PC **Wednesday** — same weekdays as the minutes layer.
  A council day is usually **two videos** (Work Session + Business Meeting); `index.csv` is one
  row per **video** — join on `(date, video_id)`, disambiguate the same-day pair by title.
- Cross-referenced spot-check: sampled dates 2020-07-07 / 2022-01-04 / 2024-01-02 have council
  minutes on disk (transcript = deliberation detail behind the minutes); 2018-08-28 / 2019-10-01
  predate the **2020 data floor**; 2026-07-07 is newer than the newest council minutes on disk
  (publishing lag). See `AVAILABILITY.md`.

## Caveats

- **ASR, not a record**: no speaker labels (bar the `>>` change markers some tracks carry),
  proper nouns garbled ("Cottonwood"→"Conwood", "Weichers"→"Wickers"). The clerk's minutes are
  authoritative; transcripts fill deliberation detail + the no-minutes / newer-than-minutes
  dates only. Never quote ASR text as the official record.
- `caption_type=asr` on the 501 `format=na` rows is a platform-pattern assertion (sampled).
- 184 non-meeting rows live only in `channel_videos.csv` (`is_meeting=no`); `index.csv` is
  meetings only.
- `enum_*.tsv` / `undated_probe.tsv` use a **literal two-char `\t`** field separator (the
  yt-dlp `--print` gotcha), not a real TAB — the build script splits on `r"\t"`.
- yt-dlp (2026-06 build) warns "No supported JavaScript runtime" / "ffmpeg not found";
  caption fetches still succeed. Installing `deno` would silence the JS warning on a bulk run.
