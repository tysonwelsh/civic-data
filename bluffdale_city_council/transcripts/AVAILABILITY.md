# Bluffdale — meeting video transcripts: AVAILABILITY

**As-of:** 2026-07-12
**Verdict:** Meeting **video exists**, but there is **NO retrievable caption/transcript
track** anywhere on the official path. This dataset is **honestly unrecovered** (0 captions
retrieved; 15 videos catalogued in `unrecovered.csv`). This is a data finding, not a
scraper miss.

## What was checked

1. **YouTube — no official Bluffdale channel.** WebSearch (`"Bluffdale City" Utah youtube
   council meetings`) and a `yt-dlp ytsearch` surfaced only third-party clips (FOX 13, a
   2019 candidate forum on a resident's channel, a ULCT "Mayor in a Minute") — no city
   channel that posts full meetings. The Utah-meetings mirror channel **@UtahRecord**
   (`youtube.com/channel/UC5hXeD66VUV_w655ionxaSA`) carries Draper / Lehi / Layton / Sandy
   only — **not Bluffdale** (enumerated all 78 videos with `yt-dlp --flat-playlist`; zero
   Bluffdale). → The `yt-dlp --write-auto-sub` caption path has **no YouTube target** for
   Bluffdale.

2. **The city's actual video platform is CivicClerk, not YouTube.** The city's
   *Streaming-Videos* page (`bluffdale.gov/525/Streaming-Videos`) embeds
   `https://bluffdaleut.civicclerk.com/Web/Home.aspx`. Meeting recordings are served as
   plain Azure-CDN MP4s (`https://cpmedia.azureedge.net/bluffdaleut/<hash>.mp4`) via the
   CivicClerk public portal `https://bluffdaleut.portal.civicclerk.com/`.

3. **CivicClerk publishes NO captions for these videos.** The CivicClerk Events API
   (`https://bluffdaleut.api.civicclerk.com/v1/Events`, GET-only, retained verbatim at
   `raw/civicclerk_events.json`) exposes explicit closed-caption fields on every event —
   and for **all 15** media events they are empty: `closedCaptionFileName = null`,
   `closedCaptionStatus = none`, `closedCaptionServiceType = 0`, `youtubeVideoId = ""`
   (i.e. not mirrored to YouTube either). A direct `yt-dlp --list-subs` on the newest
   council MP4 returns **"has no subtitles"**. There is no official/timedtext/VTT caption
   artifact to retrieve.

4. **OpenUtah mirror is metadata-only, by rule.** `bluffdale.openutah.org` states it
   publishes "Transcripts sourced from official city recordings" (its own ASR of the same
   CivicClerk videos), but its transcript text is served client-side behind
   `robots.txt Disallow: /api/`. Per the skill's polite-scraper rule it is treated as a
   summary/metadata source only — **not bulk-grabbed**. (If the user later wants that text,
   it would be a separate, explicitly-authorized retrieval decision.)

## What exists (the video → date map)

**15 meeting videos on CivicClerk, all 2026: 2026-03-04 → 2026-07-08**
(8 City Council, 6 Planning Commission, 1 civic event — "Miss Fisher's 5th Grade
Congressional Hearing"). Full rows with `video_url` (the MP4), `video_id`
(`civicclerk:<eventId>`), and `source_url` (portal event page) are in
[`unrecovered.csv`](unrecovered.csv). CivicClerk retains only this recent window — **no
Bluffdale meeting video is available before 2026-03** (the pre-CivicClerk record is the
minutes-only CivicPlus AgendaCenter; this is an honest platform-retention gap, not a
deletion by this build).

## Coverage window

| | value |
|---|---|
| Captions retrieved | **0** |
| Videos catalogued (no captions) | **15** |
| Video platform | CivicClerk (Azure CDN MP4) — **not YouTube** |
| Video coverage window | 2026-03-04 → 2026-07-08 |
| Pre-2026 video | none retained (minutes-only era) |
| Official caption track | none (YouTube absent; CivicClerk CC fields null) |

## Whisper proposal (NOT run — user decides)

`transcripts/text/` is **empty**: no ASR captions exist, so nothing was cleaned. The only
way to obtain deliberation-level transcripts for Bluffdale is to **run Whisper (or
equivalent) over the 15 CivicClerk MP4s** listed in `unrecovered.csv`. Per the
non-negotiable rules this build does **not** run Whisper. High-value candidates, if the
user authorizes it:

- **2026-05-13, 2026-05-27, 2026-06-10 City Council Business Meetings** — the mid-2026
  budget/land-use stretch; deliberation the scanned minutes summarize away.
- **2026-03-11, 2026-03-25, 2026-04-08 City Council** — align with the current
  `meeting_minutes/` record for cross-checking contested-vote discussion.
- **Planning Commission 2026-04-15 / 2026-05-20 / 2026-06-03** — PC→Council recommendation
  reasoning behind the referral layer.

Each MP4 is a direct GET (`cpmedia.azureedge.net/bluffdaleut/<hash>.mp4`); Whisper output
would land in `text/<date>.md` (clearly headed as ASR, not an official record) and the
rows would move from `unrecovered.csv` into `index.csv` with `caption_type=asr`,
`format=caption`, `extraction_method=whisper`.

## Reproduce

```
# video → date map + null-caption proof (GET-only, polite):
curl -s -A "<browser-UA>" \
  "https://bluffdaleut.api.civicclerk.com/v1/Events?%24orderby=startDateTime%20desc"
# (page via @odata.nextLink; the merged response is retained at raw/civicclerk_events.json)

# confirm no caption track on a video:
yt-dlp --list-subs --skip-download "https://cpmedia.azureedge.net/bluffdaleut/9d628a5d2d.mp4"
#   -> "has no subtitles"
```
