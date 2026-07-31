# Meeting-video transcripts — availability

**As-of:** 2026-07-03 · **Scope:** West Jordan City Council + Planning Commission meeting
video and its caption tracks. **Additive dataset; ASR (machine) transcripts only.**

## TL;DR
West Jordan posts meeting video to its **official YouTube channel**, and YouTube
auto-generates **`en-orig` (English Original) ASR caption tracks** for most of them. There
are **no human-authored / manual caption tracks** on any WJ meeting video (the only
non-ASR "subtitle" some videos carry is a `live_chat` replay, not a transcript). We pulled
a **sample of 10 recent council + PC meetings (Nov 2024 – Feb 2025)** as caption tracks —
all `en-orig` ASR — cleaned them, and indexed them. The dataset is a **representative
sample, not a full backfill**.

## Host / channel
- **West Jordan City** — `https://www.youtube.com/channel/UC7Up4AfoWj0KebppgTvnLSg`
  (vanity redirect `https://bit.ly/WestJordan`).
- Meeting video is split across **two channel tabs**:
  - **`/streams`** — live-streamed meetings, **2017 → 2023-04-12** (284 items; 131 titled
    "City Council").
  - **`/videos`** — uploaded meetings interleaved with promo content, **~mid-2023 →
    2025-02-04** (363 items; the 2024 meeting set is complete here).
- Both tabs are JS-rendered — enumerate with `yt-dlp --flat-playlist`, not WebFetch.

### Hard cutoff: YouTube meeting video ends **2025-02-04**
The most recent meeting on YouTube is **Planning Commission, Feb 4 2025**. After that the
city stopped posting meetings to YouTube and publishes video only through **Swagit** and
the **OpenUtah mirror** (see below). So YouTube captions are **unavailable for any meeting
after 2025-02-04** — those need a different source or Whisper.

## Caption type: ASR (automatic), never manual
Every retrieved track is YouTube **automatic speech recognition** — verbatim-ish but
**word-error-prone** (proper nouns, ordinance numbers, dollar figures, and crosstalk are
frequently wrong). The `en-orig` track is the original ASR; the `en` track is YouTube's
machine *translation* of it (lower quality) — we keep `en-orig`. The city's own promo
("full word-for-word searchable transcript 3–5 days after the meeting") refers to the
**OpenUtah / PrimeGov AI transcript**, which is likewise machine-generated, not a human
record. **Nothing here is an official record** — the clerk PDFs in `meeting_minutes/` are.

## Per-year caption availability (YouTube `en-orig` ASR)
Sampled one representative council meeting per year via `yt-dlp --list-subs` (plus the
full 10-meeting Nov 2024–Feb 2025 pull). Caption presence on **older** videos is spotty —
YouTube did not auto-caption every older upload:

| Year | Meeting video on YouTube? | `en-orig` ASR captions? | Notes |
|------|---------------------------|-------------------------|-------|
| 2017 | yes (streams)             | not verified            | pre-scope (repo floor 2020) |
| 2018 | yes (streams, 27)         | **NO** (sample: none)   | no auto-captions on sampled video |
| 2019 | yes (streams, 50)         | **NO** (sample: none)   | no auto-captions on sampled video |
| 2020 | yes (streams, 59)         | **YES** (sample)        | en-orig present |
| 2021 | yes (streams, 48)         | **NO** (sample: live_chat only) | captions spotty this year |
| 2022 | yes (streams, 62)         | **YES** (sample)        | en-orig present |
| 2023 | yes (streams→videos)      | **YES** (sample)        | Jan–Apr on /streams, rest on /videos |
| 2024 | yes (videos, ~81 mtgs)    | **YES** (10/10 in reach)| full meeting year, well captioned |
| 2025 | Jan 1 – **Feb 4 only**    | **YES** (sample)        | then YouTube meeting video stops |
| 2026 | **NO council/PC meetings**| n/a                     | only retreats/promo on YouTube; meetings on Swagit/OpenUtah |

(2022/2023 exact ASR presence recorded in `scratch_yearprobe.log` at build time; treat
pre-2024 caption availability as **partial** — confirm per-video with `--list-subs` before
relying on any specific older meeting.)

## What we retrieved (this run)
10 meetings, all `caption_type=asr`, `format=caption`, listed in `index.csv`:
- **Council (5):** 2024-11-06, 2024-11-20, 2024-12-04, 2024-12-18, 2025-01-14
- **Planning Commission (5):** 2024-12-03, 2024-12-17, 2025-01-07, 2025-01-21, 2025-02-04

Raw `.vtt` in `raw/` (~8.3 MB total; sha256 in `raw/_fetch_log.jsonl`); cleaned markdown in
`text/`. `screen_corpus.py` clean (dict_ratio ~0.86, no artifacts/mojibake). This is a
**deliberate sample** — the full 2024 meeting year and captioned 2020/2022–2023 meetings
remain un-pulled but are retrievable with the same `yt-dlp` recipe (see `CLAUDE.md`).

## yt-dlp / tooling situation
- `yt-dlp` **2026.06.09 already installed** at `/Users/tysonwelsh/anaconda3/bin/yt-dlp`;
  `pip install -U yt-dlp` reported already-current. **Install was NOT a blocker** for WJ.
- Current YouTube extractor **requires a JS runtime** — Node v23 present, passed via
  `--js-runtimes node`. Caption download worked reliably with it.
- Newer challenge note: `--list-subs` sometimes warns about an "EJS remote component
  challenge solver" (needs `--remote-components ejs:github`); this only affected format
  probing, **not** the `--write-auto-sub` caption downloads, which all succeeded.
- Downloads spaced **≥33 s**; ~25 probes total — **no bot-check/rate-limit block** hit.

## OpenUtah mirror finding
`https://westjordan.openutah.org/` **exists and is active** — it mirrors WJ council/PC (and
other body) meetings with **AI-generated transcripts** ("transcripts sourced from official
city recordings; AI-generated content may contain errors"), video embedded from **Swagit or
YouTube**, and links back to PrimeGov agendas. At build time it advertised **196 indexed
meetings, 141 transcribed**, current through **July 2026** — i.e. it **covers the
post-2025-02-04 gap** that YouTube does not. **But** its transcript text is served
client-side via the site's `/api/`, and `robots.txt` has **`Disallow: /api/`** (verified) —
so under the polite-scraper rule it is a **summary/metadata source only, not a bulk-grab
transcript source.** A user who wants those transcripts should treat OpenUtah as a
manual/interactive reference or seek the underlying Swagit captions directly.

## HIGH-VALUE untranscribed meetings — PROPOSED for Whisper (NOT run)
Whisper was **not run** (expensive; user decides). Candidates, in priority order:

1. **Post-2025-02-04 council meetings not on YouTube** — the FY2026-27 **budget adoption**
   and the **June 2026 Truth-in-Taxation / property-tax-increase** council meeting (OpenUtah
   flags the 2026-06-24 council meeting as budget + property-tax + streetlight policy).
   These are the most consequential recent meetings and have **no YouTube caption**; Whisper
   would need the Swagit/OpenUtah audio. (OpenUtah already hosts an AI transcript — run
   Whisper only if an independent transcript is wanted.)
2. **2024 special / Truth-in-Taxation council meetings** on YouTube that lack `en-orig`
   (e.g. `West Jordan City Truth in Taxation Hearing`, `Special City Council Meeting -
   2024-08-27`) — confirm caption absence per-video, then Whisper the YT audio.
3. **In-scope (2020–2023) council meetings with no auto-captions** — the 2021 and 2018/2019
   samples had none; specific contested-rezone or budget meetings from those years would be
   worth Whisper on the YouTube audio if a researcher needs the deliberation.

## What was checked
- WebSearch for the channel; confirmed official WJ YouTube channel hosts council/PC video.
- `yt-dlp --flat-playlist` enumeration of both `/streams` and `/videos` tabs (647 items).
- `yt-dlp --list-subs` on one meeting per year 2018–2023 + the full 10-meeting sample.
- OpenUtah mirror existence, coverage, and `robots.txt` (`Disallow: /api/`) verified.
- PrimeGov portal + city meetings page reviewed (they link to the YouTube stream and to
  the AI transcript, not to a downloadable human transcript).
