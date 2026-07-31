# Sandy City — meeting-video transcript availability

As-of **2026-07-05**. This dataset holds **automatic (ASR) caption tracks** for Sandy City
public-meeting videos, retrieved via the official YouTube `timedtext` path (`yt-dlp`). ASR =
machine speech-to-text: **verbatim-ish but error-prone; not an official record.** Authoritative
minutes remain `meeting_minutes/`; treat these transcripts as a supplementary, searchable
account of what was *said* (public comment, deliberation, staff presentation) that minutes
paraphrase or omit.

## Video sources found

| Channel / platform | ID | What it holds | Meeting videos? |
|---|---|---|---|
| **Utah Record – Public Meetings** (YouTube) | `UC5hXeD66VUV_w655ionxaSA` | Third-party civic-meeting archive for ~40 Utah cities; **"Sandy City Meetings" playlist** `PL6IaTceX1fg_4lrLVY7l8v5PX6Sf7u4pT` | **YES — the real archive.** Council, Planning Commission, Board of Adjustment |
| **OpenUtah** (`sandy.openutah.org`) | — | AI-indexed summaries + transcripts of the same videos (177 meetings indexed, 107 transcribed) | Indexes the Utah Record videos; **used here only as the meeting→video map.** Its verbatim transcript API (`/api/`) is `robots.txt`-disallowed and was NOT scraped |
| **Sandy City Council** (YouTube) | `UCJAb3H4Dtsc2AOsYedLjPew` | 17 videos: member profiles, Noal Bateman award reels, how-to clips | **Almost none** — exactly **one** meeting recording ever posted (Oct 25 2022, no captions) |
| **Sandy City Hall** (YouTube) | `UCUvVGK27whjBEK81W03Tr-A` | 504 videos: promos, town halls, award/recap videos | **No** regular council/PC meeting recordings |

The city does **not** self-host meeting video on Granicus/Swagit or its own site; `sandy.utah.gov/live`
is a livestream landing page with no archive. All archived meeting video flows through the
**Utah Record** channel (and OpenUtah's index of it).

## Coverage window & the platform cutoff

- **Videos exist only from 2025-01-14 onward.** The Utah Record channel did not cover Sandy
  before 2025. This is the hard **source cutoff**, not an extraction gap.
- **88 Sandy meeting videos** enumerated (2025-01-14 → 2026-06-23): **65 City Council, 21
  Planning Commission, 2 Board of Adjustment**, plus the lone 2022 council video.
- **79 have ASR captions retrieved** (`format=caption`). **All ASR; zero human/manual caption
  tracks exist** on any Sandy video. **9 videos have no caption track** (`format=na`).
- Nothing beyond 2026-06-23 was published as of retrieval; the most recent 1–2 weeks may lag.

### The 2020–2024 hole (a source limit, honest gap — do not fill)
`meeting_minutes/minutes_index.csv` lists **274 council meetings (2020-01-07 → 2026-06-02)**.
**215 of them (all of 2020–2024) have no video anywhere** — the archive did not exist yet.
Transcripts therefore cannot cover 2020–2024. Minutes are the only record for those years.

### 2025–2026 council coverage (where video exists)
Of the **59 council meetings** in `minutes_index.csv` dated 2025-01-01 or later:
- **45 have an exact-date ASR caption** in this dataset.
- **14 have no matching video** (regular sessions the archive skipped): 2025-01-07, 2025-03-11,
  2025-05-27, 2025-06-10, 2025-06-24, 2025-07-01, 2025-08-26, 2025-09-02, 2025-09-16,
  2025-10-21, 2025-10-28, 2025-11-11, 2025-11-18, 2025-12-09.
- Several captioned videos are **off the minutes grid**: budget-priorities workshops, oath/
  ceremony sessions (e.g. 2025-03-17 Bucha Sister City), and **meetings newer than the latest
  published minutes** (2026-06-09, 2026-06-16, 2026-06-23 — video leads minutes here).

## Videos with no caption track (`format=na`, 9)

| Date | Body | Video ID | Status |
|---|---|---|---|
| 2022-10-25 | Council | `JyXeBqOlc60` | Only pre-2025 meeting video; no captions published |
| 2025-01-15 | Council | `FwViJ8g_ql0` | Re-upload of the 2025-01-14 budget workshop — **that meeting IS captioned** (`x0s8DWGtgXo`) |
| 2025-03-19 | Council | `rse9MwelXnA` | FY25-26 Budget Preview — no caption, no alternate |
| 2025-05-02 | Planning Comm. | `x-RPrAtV9Nc` | No caption, no alternate |
| 2025-07-23 | Council | `CeTyDxdcm7w` | No caption, no alternate |
| 2025-09-03 | Council | `v5CljA9Y8BA` | **Housing Workshop 3** — no caption, no alternate |
| 2025-10-22 | Council | `aoDdGf7uI2Y` | City re-upload; same meeting captioned via `IQ51Y0f5MJg` |
| 2026-01-27 | Council | `2XDWfRlDEdI` | City re-upload; same meeting captioned via `uOzxlDsIKr8` |
| 2026-05-12 | Council | `ZgunjPJccEc` | City re-upload; same meeting captioned via `VIAEXKFdfsU` |

## Whisper transcription — PROPOSED (not run)

These meetings **have video but no caption of any kind** (excludes the re-uploads already
covered by a captioned twin). Running OpenAI Whisper (or similar) on the audio would recover
them. Ranked by relevance to this repo's housing/growth mission:

1. **2025-09-03 — Housing Workshop 3** (`v5CljA9Y8BA`) — *highest value.* A dedicated housing
   session; directly on-mission and likely thin in minutes.
2. **2025-03-19 — Council, FY25-26 Budget Preview** (`rse9MwelXnA`) — budget/growth priorities.
3. **2025-05-02 — Planning Commission** (`x-RPrAtV9Nc`) — land-use body, no transcript.
4. **2025-07-23 — City Council** (`CeTyDxdcm7w`) — regular session, no transcript.
5. **2022-10-25 — City Council** (`JyXeBqOlc60`) — the *only* window into a pre-2025 meeting on
   video; would be the sole 2020–2024 transcript if recovered.

The 14 missing 2025+ council dates and the 215 missing 2020–2024 dates have **no video** and are
**not** Whisper-recoverable — flag them as permanent transcript gaps.

## Method note
Meeting videos are **unlisted-style archive uploads** not shown on the source channels' public
`/videos` tab; they are reachable via the "Sandy City Meetings" playlist and via OpenUtah's
per-meeting pages. Enumeration used `yt-dlp --flat-playlist`; captions used
`yt-dlp --write-auto-sub --sub-langs "en.*"`. See `CLAUDE.md`.
