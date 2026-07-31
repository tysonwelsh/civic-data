# Holladay City — meeting-video transcripts: availability

**As of:** 2026-07-13 (both platforms enumerated; YouTube captions sampled; SuiteOne video
map resolved this date).

## Platform verdict — TWO video hosts, split by era

Holladay's meeting video is spread across two unrelated platforms with a **multi-year gap**
between them:

1. **SuiteOne portal — the current meeting-video host** (2025+).
   `https://holladayut.suiteonemedia.com/`. Each event page embeds a **JWPlayer** whose
   source is a plain **S3 MP4** (`https://s3.amazonaws.com/suiteone.holladayut.videofiles/
   <hash>.mp4`, plus an `.m3u8` HLS variant). The portal home lists **181 events across
   2025-2026 only**; **75 of them carry a recording** (a `fa-video-camera` row icon).
   **There is NO caption track** on any SuiteOne video — the JWPlayer setup has no `<track>`,
   no `tracks:[]`, and no `.vtt` reference anywhere in the page (verified on multiple events).
   Video-only. → every SuiteOne row is `format=na`, `caption_type=none`, a Whisper candidate.

2. **Official YouTube channel — a shallow 2020-2021 relic** (not the archive).
   "Holladay City" `@holladaycity4925` (`UCpePWrbddeqj42k8dodt-og`). The channel holds **65
   videos total, but only 6 are genuine body-meeting recordings**, all part of a single
   **Feb-2021 batch upload** of Dec-2020 / Jan-2021 meetings. The other 59 are PR/history
   content — "Speaker Series", "Backs the Blue", the property-tax explainer series, Arts
   highlights, mayor's-message COVID clips (fully catalogued in `channel_videos.csv`,
   `is_meeting=no`). The channel is **not** the council/PC meeting archive.
   → the 6 meeting videos DO carry **YouTube ASR captions** (fetched).

3. **"Utah Record" mirror (`UC5hXeD66VUV_w655ionxaSA`) — checked, NOT a Holladay source.**
   Enumerated both its tabs (78 videos): it mirrors **Draper and Lehi** only. **Zero
   Holladay** content.

**Consequence — a 2021-mid → 2024 video gap.** YouTube meeting video stops at 2021-01-20;
SuiteOne begins 2025-01-02. **No meeting video was found on any platform for 2021-02 through
2024** (the recon predicted the SuiteOne back-catalog is ~2025+; confirmed). Video for that
era, if it exists, is not publicly discoverable — an honest gap, not a scraper miss.

## Caption statistics

| Platform | Videos | Caption track | Fetched |
|---|---|---|---|
| YouTube (meetings) | 6 | **YouTube ASR (auto), en + en-orig (identical)** — 0 manual | **6/6** |
| SuiteOne | 75 | **NONE** (video-only S3 MP4) | 0 (Whisper deferred) |

- YouTube auto-caption availability confirmed per video with `--list-subs` (en, en-orig both
  present on every meeting video). No human/manual track exists.
- SuiteOne zero-captions is an **authoritative** result: the player markup carries no caption
  reference at all. This mirrors Park City's video-only CivicClerk case.

## What was fetched (the entire caption-bearing population — 6 videos)

The whole set of caption-bearing Holladay meeting videos is only 6, so all 6 were fetched
(satisfies the ~10-sample target; there is no larger pool to sample from). Raw `.vtt` in
`raw/`, cleaned to `text/<date>.md`:

| date | body | words | date basis |
|---|---|---|---|
| 2020-12-15 | PlanningCommission | 21,701 | title ("Dec 15, 2020") |
| 2021-01-05 | PlanningCommission |  8,629 | **ASR call-to-order** (chair, 0:27 — "…meeting to order on January 5th"; ASR misheard the year "2021"→"2020"; 1st Tuesday) |
| 2021-01-07 | Council            | 19,442 | video description ("Jan 7, 2021"; 1st Thursday) |
| 2021-01-14 | Council            | 21,787 | title ("Jan. 14"; 2nd Thursday) |
| 2021-01-19 | PlanningCommission | 11,885 | title ("Jan. 19"; 3rd Tuesday) |
| 2021-01-20 | ArtsCouncil        |  9,440 | video description ("Jan 20, 2021") |

`screen_corpus.py` (2026-07-13): **0 hard flags**; dict_ratio median 0.869 (healthy ASR);
6/6 `ends_mid` advisory — expected (the caption track stops when the broadcast cuts), not a
defect.

## Date + body provenance

- **YouTube dates** come from the title (3), the video description (2), or the chair's spoken
  call-to-order in the ASR (1) — see the table. `flat-playlist` returns `NA` timestamps and
  the `upload_date` is a batch **2021-02-13/16** (useless for the meeting date), so title /
  description / spoken-date were used instead. Recorded per row in `index.csv`
  `date_source`.
- **SuiteOne dates** are the portal-listed event date (`date_source=suiteone`) — reliable.
- **Body** is read from the event/video title (Holladay titles every meeting): Council,
  PlanningCommission, RDA, LBA, ArtsCouncil, AdminHearingOfficer, Ceremony. `City Council &
  RDA Meeting` events are tagged `Council` (the RDA sits in-session inside the council
  evening, matching the core repo's `body` design); the one standalone `RDA Board Meeting`
  and the 4 `Local Building Authority` events are tagged `RDA` / `LBA`.

### SuiteOne video map (75 rows) by body

Council 37 · PlanningCommission 31 · LBA 4 · RDA 1 · AdminHearingOfficer 1 · Ceremony 1.
Full resolved map (event_id → S3 MP4 hash) in `_suiteone_video.csv`; the full 181-event
portal listing in `_suiteone_events.csv`.

## Whisper candidates — PROPOSE ONLY (owner decides; not run)

The high-value untranscribed set is the **75 SuiteOne 2025-2026 meetings** — these are the
**only** video record for the current council/PC era and they carry **no captions**, so ASR
is the only way to get their deliberation text into the repo. Priority tier: the **68
Council (37) + PlanningCommission (31)** meetings. Est. cost is meaningful (75 full-length
MP4s → Whisper). The 6 YouTube meetings already have ASR captions and need no Whisper.

If a bulk SuiteOne ASR run is authorized, the fetch path per event is:
`s3.amazonaws.com/suiteone.holladayut.videofiles/<video_id>.mp4` (from `index.csv`;
`.m3u8` HLS variant available) → Whisper → `text/<date>.md` with the ASR header, and flip the
row to `format=caption`, `caption_type=asr`, `extraction_method=whisper`.

## Honest limits

- **ASR, not a record**: no speaker labels; proper nouns (member names, "Holladay"→"holiday",
  plat/ordinance numbers, and even a meeting YEAR) frequently misrecognized. The clerk's
  minutes under `meeting_minutes/` / `planning_commission/` are authoritative; transcripts
  add deliberation detail only.
- `caption_type=none` on the 75 SuiteOne rows is verified from player markup, not inferred.
- The 2021-02 → 2024 video gap is a **publishing** gap (no platform hosts that era publicly),
  documented above; the minutes layer still covers those years via PMN.
- SuiteOne dates run to 2026-09-01 in the portal listing but only meetings **with a resolved
  recording** through 2026-07-07 are in `index.csv` (future/agenda-only events have no
  video yet).
