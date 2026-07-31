# West Valley City meeting-video transcripts — availability

**As-of:** 2026-07-06 · **Dataset:** `west_valley_city_council/transcripts/` ·
**Source type 5** (meeting-video transcripts) · **Policy: SAMPLE-ONLY** (owner decision
2026-07-05) — full video→date map + a small recent ASR caption sample; the **map is the
deliverable**.

## Summary

West Valley City livestreams and archives its Council / RDA / Building Authority / Housing
Authority meetings on its own **YouTube channel, WVCTV (`@wvctv2290`)**. Those videos carry
**YouTube auto-captions (ASR)**, which `yt-dlp` retrieves cleanly on the official path — so
unlike the Lehi pass, transcript text WAS recovered here. Per the sample-only policy we
downloaded ASR captions for the **10 most recent regular Council meetings** (2026-02-10 →
2026-06-23) and shipped the **full channel enumeration** (1,133 videos) mapped to meeting
dates in `channel_videos.csv`, with the civic-relevant 2020–2026 subset (461 meetings) in
`index.csv`.

## Where WVC video lives

- **Official portal:** `https://www.wvc-ut.gov/837/View-Online` — a **302 redirect** to
  `https://www.youtube.com/@wvctv2290/streams`. Also broadcast on **Comcast Channel 17**
  (WVCTV) and mirrored at `wvctv.org`.
- **Primary host — YouTube channel WVCTV (`@wvctv2290`).** The legacy handle
  `https://www.youtube.com/user/WVCTV` resolves to the **same** channel. A curated
  **"West Valley City Council" playlist** also exists
  (`PLgEVO2v4UF3mmYCk1jP2KMz2gAQ5dxrbk`, ~100 items) but is a subset — the channel tabs are
  the complete source.
- **Two disjoint channel tabs (enumerated separately — they share no video IDs):**
  - **`/streams` (495 videos)** — the livestreamed meetings, **Apr 2020 → Jun 2026**. This
    is where nearly every modern Council/RDA/BA/HA meeting lives (450 of the 461 in-window
    meetings).
  - **`/videos` (638 videos)** — older regular uploads: **pre-livestream Council meetings
    2012 → early-2020** (11 in-window, the Jan–Mar 2020 meetings), plus non-meeting content
    (Chat with the Chief, PSRB public meetings, cultural events, holiday messages). Both
    tabs were mapped so early-2020 coverage is not lost.
- **No Granicus / Swagit portal.** WVC does not use a Granicus/Swagit video CMS; YouTube is
  the archive.

## Caption type: ASR (automatic), not manual

- The captions are **YouTube ASR** (`Kind: captions`, auto-generated `en`/`en-orig`, which
  are byte-identical). **No manually-authored/verbatim caption track exists.** Every cleaned
  `text/*.md` is headed **"AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an
  official record."**
- The authoritative record remains the clerk's **minutes** in `meeting_minutes/`.

## Alternate mirror — OpenUtah (found, not scraped)

`https://westvalley.openutah.org/` — **"West Valley City Public Meeting Transcripts |
OpenUtah"**, a third-party site publishing **AI-generated** transcripts of the same city
recordings (dashboard: **87 meetings indexed, 38 transcribed**; disclaimer: *"AI-generated
content may contain errors"*). We did **not** pull its transcript text: it is served behind
`/api/`, and `https://westvalley.openutah.org/robots.txt` contains **`Disallow: /api/`** —
honoring robots + the polite-scraper rule. The YouTube ASR path we used is the official
source and needs no scraping. (Coverage there begins ~2025; YouTube goes back to 2020.)

## What was retrieved (sample)

- **10 ASR caption files**, the most recent regular Council meetings:
  2026-06-23, -06-09, -05-26, -05-12, -04-28, -04-14, -03-24, -03-10, -02-24, -02-10.
  Raw VTT in `raw/<date>_council-regular-meeting.en.vtt` (sha256 + bytes + word count in
  `raw/_fetch_log.jsonl`); cleaned text in `text/<date>_council-regular-meeting.md`.
- `yt-dlp` recipe that worked (the DEFAULT client): 
  `yt-dlp --write-auto-sub --write-sub --sub-format vtt --skip-download --sub-langs "en.*"
  <watch_url>` (yt-dlp 2026.06.09; resolved via the android VR player API — the
  android-player-client fallback recipe was not needed on this channel).

## Coverage window + cutoff

- **Window:** 2020–2026 (per task). Mapped in-window meetings: **461** (streams 450 +
  videos 11), spanning **2020-01-07 → 2026-06-23**.
- **Minutes match:** **443 / 461 (96%)** of in-window meetings join by exact date to
  `meeting_minutes/minutes_index.csv`. The 18 non-matches are legitimately minutes-less:
  budget-retreat days (no formal minutes), the 2026-06-23 meeting (newer than current
  minutes coverage, latest minutes = 2026-06-09), and a few off-cycle Monday/holiday-week
  meetings whose minutes were filed under an adjacent date.
- **Whole-channel enumeration cutoff:** as-of **2026-07-06**; newest video 2026-06-23.
- **Full channel:** 1,133 videos, 809 of them meetings, dated span 2010–2026 (out-of-window
  and non-meeting rows retained in `channel_videos.csv` but excluded from `index.csv`).

## Date provenance (map honesty)

Meeting dates in the map come from three sources (`date_source` column):
- **`title` (397 in-window)** — parsed from the video title (e.g. `06.23.2026 ...`,
  `March 25, 2025 ...`). Authoritative.
- **`upload_date_snapped` (62)** — bare-titled livestreams (e.g. "City Council Regular
  Meeting", no date in title). Their YouTube **upload date** was fetched and snapped to the
  nearest minutes date within ±1 day (the VOD posts the day **after** the Tuesday meeting —
  a clean −1-day offset for 61 of 64 fetched). `upload_date_raw` retains the unsnapped value.
- **`upload_date_approx` (2)** — the multi-day "2025 Annual Budget Retreat (Day Two)" pair,
  which did not snap to a minutes date; upload date kept as an approximate, `minutes_match`
  left False (honest).
- **8 truly undated** channel videos (swearing-in ceremonies, holiday messages, Youth
  Council clips, a Comcast Newsmakers segment) carry no extractable date and are non-
  substantive; retained in `channel_videos.csv` with empty `date`.

## High-value meetings PROPOSED for Whisper (NOT run — owner's call)

YouTube ASR captions exist for essentially every livestreamed meeting, so Whisper is only
worth it where **verbatim accuracy on names/motions matters** — the contested votes (WVC is
a high-consensus council; splits are the signal). Highest-value recent contested Council
meetings (from `meeting_minutes/all_votes.csv`; all have channel videos, IDs in
`channel_videos.csv`):

1. **2025-10-28 — Resolution 25-156 FAILS 3-3** (a rare tied failure), then **2025-11-18 —
   Res 25-156 APPROVED 4-3** on reconsideration. The full reversal arc is the single
   highest-value pair; deliberation the tally can't convey.
2. **2026-03-24 — Resolution 26-28 approved 4-3.** Close, divided vote.
3. **2025-07-08 — Ordinance 25-17 DENIED 4-3.** A contested denial (land-use).
4. **2025-11-25 — Ordinance 25-36 continued 4-2**; **2025-09-09 — Res 25-118 4-2**;
   **2025-07-22 — Res 25-103 5-2.** Divided land-use / policy votes.
5. Any meeting with a dissent in `meeting_minutes/all_votes.csv` (filter contested) — 31
   contested Council/RDA meetings 2024+ alone.

To transcribe: pull the video from `channel_videos.csv` (`video_url`), run Whisper, and
label the output identically as ASR ("expect word errors; not an official record").

## What was checked

- `wvc-ut.gov/837/View-Online` → confirmed 302 to `youtube.com/@wvctv2290/streams`.
- Enumerated **both** `@wvctv2290` tabs via `yt-dlp --flat-playlist` (`/streams` 495,
  `/videos` 638 — disjoint); confirmed `user/WVCTV` = same channel; sampled the council
  playlist (100).
- `yt-dlp` present (2026.06.09) + Node present; DEFAULT caption recipe succeeded on all 10
  sampled videos (each has an ASR `en` track).
- OpenUtah mirror: fetched the WVC landing page (87 indexed / 38 transcribed) and
  `robots.txt` (`Disallow: /api/`) — did not scrape the transcript API.
- Confirmed no Granicus/Swagit portal for WVC.
