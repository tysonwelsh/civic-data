# transcripts/ — Herriman City meeting-video transcripts (YouTube ASR)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 5). **Additive dataset**
— nothing in `meeting_minutes/`, `planning_commission/`, `db/`, or `weeks/` was touched.

## Source

- **Channel:** Herriman City — `https://www.youtube.com/channel/UCBFfCj0QT3f_2UfBE45al1w`
  (meetings mostly under `/streams`, 626; `/videos` has 357 uploads, mostly PR content).
- **The PrimeGov API is the authoritative video→meeting map:** every meeting object in
  `https://herriman.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY`
  carries a **`videoUrl`** (YouTube watch link) — 298 mapped meetings 2021–2026, incl.
  **5 unlisted videos** absent from the channel tabs. It is clerk-entered: 2 wrong-date
  copy-pastes + 1 pasted local drive path were found; the title-printed date wins on
  conflict (verified in-content for 2024-01-10). See `AVAILABILITY.md`.
- **Enumeration:** `yt-dlp --flat-playlist` over `/streams` + `/videos` (983 unique) +
  the 5 PrimeGov-only ids → 988 videos, of which **677 are meeting videos** (the rest are
  Herrimanology/PR clips, catalogued in `channel_videos.csv` only).
- **Captions:** YouTube **automatic (ASR) English** via
  `yt-dlp --write-auto-sub --write-sub --sub-lang en --sub-format vtt --skip-download`
  (official timedtext path only). No manual caption tracks exist on this channel
  (sample-verified). `caption_type=asr` everywhere.

## Files

```
index.csv           §9 contract header (date,title,body,video_url,video_id,caption_type,
                    source_url,retrieved_date,format,extraction_method,path) + extras:
                    duration_sec,tab,date_source,body_source,pg_dates,pg_bodies,
                    minutes_match. 677 rows: 10 format=caption (fetched),
                    667 format=na (mapped_not_fetched).
channel_videos.csv  the full channel map (988 rows incl. 311 NonMeeting/Other PR videos).
raw/                10 fetched .vtt caption tracks, named <date>_<video_id>.en.vtt.
text/<date>.md      cleaned transcripts, headed "AUTOMATIC TRANSCRIPTION — ASR…".
clean_vtt.py        the .vtt → cleaned-markdown converter (dedupes YouTube's
                    rolling-caption repetition, strips inline <c>/timestamp tags).
AVAILABILITY.md     platform verdict, caption stats, gap analysis, fetch backlog.
```

## How dates and bodies were derived (read before joining)

- **`date_source`** — `title` (648/677: printed in the video title — Herriman titles
  virtually every stream; abbreviated-month "Sept. 23, 2020" and numeric "5-13-20"
  variants exist in the 2019–2020 era); `primegov` (4: PrimeGov meeting dateTime);
  `title_pg_conflict` (2: title kept over a wrong PrimeGov videoUrl mapping);
  `yt_release_ts_local` (2: YouTube release_timestamp converted to America/Denver —
  the murray UTC-rollover gotcha is avoided by converting the timestamp, not trusting
  `release_date`); `yt_upload_date_utc` (1: a 2015 junk clip with no timestamp).
- **`body_source`** — `title` keywords first (incl. full agency names: "Community
  Development and Renewal Agency"→CDRA, "Safety Enforcement Area"→HCSEA, "Fire Service
  Area"→HCFSA, joint CC/PC→Joint, canvass→Canvass), else `primegov` committeeId
  (3=Council, 4=CDRA, 8=HCFSA, 9=HCSEA, 12=Joint, 14=PlanningCommission). **No weekday
  inference was needed** — beware that the PC met **Thursday** through ~2022, Wednesday
  after.
- **⚠ A Council stream is usually the WHOLE evening**: the in-session CDRA/HCSEA/HCFSA
  agency meetings happen inside the same video (PrimeGov maps one video id to several
  same-date meetings — preserved in `pg_dates`/`pg_bodies`). Standalone agency rows
  (CDRA 2, HCSEA 3, HCFSA 1) are the rare separately-streamed sessions.
- **`minutes_match`** — whether the video's date appears in this repo's
  `meeting_minutes/minutes_index.csv` (Council/agency/Canvass rows),
  `planning_commission/minutes_index.csv` (PC rows), or either (Joint rows). 41 distinct
  2020–2025 date/bodies have substantive video but no minutes — the ASR transcript is
  the only readable record for those (see AVAILABILITY.md).

## SAMPLE-ONLY policy

Per the owner decision (2026-07-05) on bulk ASR backlogs, only a 10-video representative
sample was caption-fetched (era spread 2017→2026 + two no-minutes dates + the multi-body
evening + the PrimeGov-conflict and unlisted-video probes). The other 667 rows are honest
`format=na` map rows with live watch URLs; fetch on demand:

```
python3 -m yt_dlp --write-auto-sub --write-sub --sub-lang en --sub-format vtt \
  --skip-download -o "raw/<date>_<video_id>.%(ext)s" "https://www.youtube.com/watch?v=<video_id>"
python3 clean_vtt.py raw/<date>_<id>.en.vtt text/<date>.md <date> <Body> <id>
```

## Caveats

- **ASR, not a record**: no speaker labels, proper nouns garbled. The clerk's minutes
  (where they exist) are authoritative; transcripts fill deliberation detail + the
  no-minutes dates only.
- One evening = several streams (work meeting / work meeting 2 / general / Part 1–2) —
  `index.csv` is one row per **video**; key joins on `(date, video_id)`. 46 junk-short
  clips (< 10 min) are kept honestly; filter with `duration_sec`.
- 166 rows predate the repo's 2020 data floor (channel reaches 2017-11-08) — they have
  no minutes counterpart by design.
- `text/<date>.md` exists only for the 10 sampled dates; each sampled date has exactly
  one fetched video, so date-keyed filenames are unambiguous.
- yt-dlp warned "No supported JavaScript runtime" (deprecation, 2026-06 build) — caption
  fetches still succeed; a future refresh may need `deno` installed.
