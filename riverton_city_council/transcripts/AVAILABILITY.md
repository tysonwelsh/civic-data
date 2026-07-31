# Riverton — meeting video transcripts: AVAILABILITY

**As-of:** 2026-07-13 (built by `expand-city-sources`, source type 5)

**Verdict:** Riverton's authoritative video archive is **Granicus**
(`rivertoncity.granicus.com`, `view_id=1`) — video-complete for 2015→present (652 clips),
but its per-clip caption endpoint is an **empty 40-byte stub for every clip**
(0 recoverable captions). Unlike Draper/Sandy/Lehi, **Riverton is NOT carried by the
third-party "Utah Record - Public Meetings" YouTube mirror** (0 Riverton uploads). The
city's **own** YouTube channel is promo-only except for **one** archived meeting
recording — *City Council Meeting, May 1, 2018* — which does carry YouTube ASR
auto-captions and was fetched. So the sanctioned-caption yield is **exactly one meeting
transcript**; the entire in-scope 2020→present corpus is **video-complete but
caption-less on every official path** (Whisper is the only route — proposed below).

## Platform findings (what was checked)

1. **Granicus (authoritative; 0 captions).** `ViewPublisher.php?view_id=1` lists **652
   video clips** across all bodies (full catalog retained in `granicus_clips.csv` — name,
   date, clip_id, duration, MediaPlayer URL, DownloadFile URL that 302-redirects to the
   direct `archive-video.granicus.com/rivertoncity/rivertoncity_<guid>.mp4`). Bodies &
   spans:
   - **City Council 263 clips (2015-09-01 → 2026-06-16; 141 in the 2020→present window)**
   - **Planning Commission 214 (2015-09-17 → 2026-07-09; 128 in-window)**
   - RDA 62, Law Enforcement Service Area 60, Fire Service Area 32, Board of Canvassers 7,
     Board of Equalization 5, Board of Adjustment 5, Historic Preservation 4.
   Every player exposes one English subtitle track at `/videos/<clip_id>/captions.vtt`, and
   it is a **40-byte empty stub** (`WEBVTT` + one zero-length cue) on **all 25 clips
   probed** spanning **2015→2026, both Council and PC** (evidence retained:
   `raw/_granicus_captions_stub_clip811.vtt` = a 2026 Council clip,
   `_granicus_captions_stub_clip863.vtt` = a 2026 PC clip — byte-identical sha256).
   The `.srt` variant 404s; `TranscriptViewer.php` returns an empty (~1.6 KB) analytics
   boilerplate page. **Granicus captions were never populated — a data finding, not a
   scraper miss.** (Same failure mode documented for Draper.)
2. **Official Riverton YouTube channel = promo, with ONE meeting.**
   `youtube.com/rivertonutahgov` (linked from the city site): **152 videos, no `/streams`
   tab.** Content is "Mayor's Message", Miss Riverton, Citizens Academy, holiday events,
   boil-order notices, "Local First" councilmember spots — **not** meeting recordings, with
   a **single exception**: *City Council Meeting - May 1, 2018* (`aHEL5osaQFk`, 7,375 s /
   2h03m, uploaded 2018-05-02), which **has English ASR auto-captions**. Fetched and
   cleaned (18,765 words). This is the **only** Riverton meeting video on any sanctioned
   YouTube path.
3. **Utah Record mirror does NOT carry Riverton.** The third-party channel
   **"Utah Record - Public Meetings"** (`UC5hXeD66VUV_w655ionxaSA`) — the caption source
   that rescued Draper/Sandy/Lehi/Layton in this repo — has **78 uploads, 0 for Riverton**
   (Draper 40, Lehi 21, Sandy 15, Layton 3). Enumerated with `yt-dlp --flat-playlist`.
   **Riverton has no mirror.**
4. **OpenUtah** (`riverton.openutah.org` if present) was **not scraped** — its transcript
   pages / `/api/` are `robots.txt`-disallowed per the skill's polite rule; discovery came
   from Granicus + YouTube only.

## Caption stats

| platform | meeting videos | with usable captions | fetched |
|---|---|---|---|
| Granicus (`view_id=1`) | 652 (Council 263, PC 214, +others) | **0** (all 40-byte stub) | 0 |
| City YouTube (`rivertonutahgov`) | 1 (May 1, 2018) | **1** (ASR) | **1** |
| Utah Record mirror | 0 | 0 | 0 |

**Fetched: 1 caption track, 18,765 words** (raw WebVTT `raw/2018-05-01_city-council.en.vtt`,
cleaned ASR-headed markdown `text/2018-05-01_city-council.md`, provenance in
`raw/_fetch_log.csv`). This satisfies the sample-only policy — it is the *entire*
sanctioned-caption population, not a subsample.

## The honest gap

- **2020-01 → present (the repo's in-scope window): video-complete on Granicus,
  caption-less on every official path.** ~141 Council + ~128 PC meetings (plus RDA/service
  boards) each have a retrievable MP4 (`granicus_clips.csv` DownloadFile URL → 302 → direct
  MP4) but **no transcript track anywhere**. This is the whole corpus.
- **The one fetched transcript (2018-05-01) is BELOW the repo's 2020 data floor** — kept
  because it is the only sanctioned caption Riverton exposes; treat as an ASR bonus, not
  part of the 2020+ record.
- No manual/human caption track exists anywhere (the May 2018 track is ASR).

## Whisper candidates (PROPOSE ONLY — user decides; direct MP4s make this easy)

Granicus `DownloadFile.php?view_id=1&clip_id=<id>` 302-redirects to the direct MP4, so any
clip in `granicus_clips.csv` is Whisper-ready. High-value in-window targets:

1. **The 2025-12-16 Council mayoral tie-break** (Resolution 25-62, a real 2-2 tie broken by
   Mayor Staggs — the recon's signature vote): transcribe the Council clip nearest that date
   in `granicus_clips.csv` (filter `body=Council, date=2025-12-16`) to capture the
   deliberation the minutes only summarize.
2. **Contested Planning Commission meetings** — the PC is the rezone/land-use engine
   (recommendations by application number). Pick the top divided-vote PC dates from
   `db/civic.db` (`v_contested` / `planning_commission/all_votes.csv`) and transcribe those
   clips.
3. **A recent full Council meeting** (e.g. 2026-06-16, clip in `granicus_clips.csv`) as a
   representative modern sample to validate Whisper quality against the born-digital minutes.

Any Whisper output is ASR — label with the standard header (`clean_vtt.py` HDR), never treat
as the official record. The authoritative record remains the clerk's minutes under
`meeting_minutes/` (born-digital, clean text).
