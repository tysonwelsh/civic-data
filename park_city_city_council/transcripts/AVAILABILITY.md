# Park City — meeting-video transcripts: AVAILABILITY

**As-of: 2026-07-05.** Policy for this build: **SAMPLE-ONLY** (owner decision 2026-07-05) —
build the full video→date map, retrieve at most a ~10-meeting recent-Council ASR caption
sample. **The map is the deliverable.**

## Bottom line

Park City publishes **meeting video** but **no captions of any kind**. There is therefore
**no official ASR/caption path to sample** — `index.csv` and `channel_videos.csv` map the
194 videos that exist; `raw/` and `text/` are intentionally empty (nothing to retrieve
without transcription). Whisper is **proposed, not run** (see below).

## What was checked

| Source | URL | Result |
|---|---|---|
| City YouTube channel ("Park City Government") | `youtube.com/channel/UCY4xcig8QxEpMDqQYK-4kdQ` | 57 videos, **0 council/commission meetings** — PSAs, retirement/"Coffee with Council" clips only; **no `/streams` tab**. Not a meeting source. |
| Swagit | `parkcity.swagit.com` → `parkcity.new.swagit.com/views/default/` | **HTTP 404** everywhere. Dead / unused. |
| Granicus / openutah | `parkcity.openutah.org` | 200 but **no video** links/embeds. |
| Zoom | listed on Listen-Live page | **Live-only**, per-meeting join links; not archived. |
| **CivicClerk media** | `parkcityut.api.civicclerk.com/v1/Events` | **THE video source.** 2,250 events; **194 carry an MP4** on `https://cpmedia.azureedge.net/parkcityut/<hash>.mp4`. |

## The video source: CivicClerk → Azure CDN MP4 (no captions)

- Enumerated the full CivicClerk OData `Events` feed (server-side paging, 15/page via
  `@odata.nextLink` skiptoken; 150 pages, **2,250 events**).
- **194 events** expose a real recording (`mediaSourcePathMp4` / `mediaStreamPath`).
- **Captions: ZERO.** Across all 2,250 events, `closedCaptionSourcePath`,
  `closedCaptionFileName`, `closedCaptionBlobPath`, `closedCaptionFileType` are **all
  empty**; `youtubeVideoId` empty on every event. A sampled MP4 (event 3931, 2026-06-25,
  1.0 GB, HTTP 200) has **no caption sidecar** (`.vtt/.srt/.json` all 404). These are raw
  MP4 videos with no caption track.

### Coverage window (hard cutoff)

Video begins **2023-09-27** and runs to **2026-07-01**. **There is NO video before Sept
2023** — the 2020 – mid-2023 portion of the requested 2020–2026 window has **no recordings
at all** (minutes remain the only record there).

| Body | Videos | Date range |
|---|---:|---|
| City Council | 88 | 2023-10-05 → 2026-06-25 |
| Planning Commission | 57 | 2023-09-27 → 2026-06-24 |
| Historic Preservation Board | 27 | (within window) |
| Board of Adjustment | 13 | (within window) |
| Appeal Panel | 8 | (within window) |
| General | 1 | — |
| **Total** | **194** | **2023-09-27 → 2026-07-01** |

Council by year: 2023 = 7, 2024 = 29, 2025 = 33, 2026 = 19.

### Mapping to minutes

`channel_videos.csv` carries `minutes_match` = does the video's date equal a row in
`meeting_minutes/minutes_index.csv`. **85 of 88 Council videos match.** The 3 that don't
(**2026-06-04, 2026-06-11, 2026-06-25**) are the newest meetings whose minutes are not yet
published — an honest lead, not an error. (Planning Commission / HPB / BOA / Appeal videos
do not match `minutes_index.csv` by design — that index is `meeting_minutes` only; PC
minutes live under `planning_commission/`.)

## Whisper: PROPOSED, not run

No captions exist, so ASR was **not run** (policy). High-value candidates for a future
Whisper pass, most recent first (all City Council; `event_id`, `minutes_match`):

| Date | event_id | minutes? | video |
|---|---|---|---|
| 2026-06-25 | 3931 | **no minutes yet** | cpmedia…/f50d7bc235.mp4 |
| 2026-06-11 | 3930 | **no minutes yet** | cpmedia…/9e6113b95a.mp4 |
| 2026-06-04 | 3929 | **no minutes yet** | cpmedia…/610d53ce8b.mp4 |
| 2026-05-22 | 3876 | yes | cpmedia…/f70577f8ef.mp4 |
| 2026-05-21 | 3713 | yes | cpmedia…/5f1657662d.mp4 |
| 2026-05-07 | 3711 | yes | cpmedia…/2abd09133a.mp4 |
| 2026-04-30 | 3710 | yes | cpmedia…/ee32efa454.mp4 |
| 2026-04-09 | 3707 | yes | cpmedia…/7f41361e76.mp4 |
| 2026-03-19 | 3704 | yes | cpmedia…/798ae7a67e.mp4 |
| 2026-03-06 | 3817 | yes | cpmedia…/601ec8a14b.mp4 |

The 3 **no-minutes-yet** meetings are the single highest-value targets: video is the only
existing record. Full inventory: `channel_videos.csv` (194 rows). Whisper would deliver
`raw/<date>.vtt` + `text/<date>.md` (headed as ASR) without touching this map.
