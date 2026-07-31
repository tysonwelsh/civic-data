# Provo — Meeting Video Transcripts: Availability

**As-of:** 2026-07-03. **Source type:** Source 5 (meeting video transcripts) of
`expand-city-sources`. **Additive dataset** — modifies no existing Provo dataset.

## Channel

- **YouTube channel:** Provo City Council — `https://youtube.com/ProvoCityCouncil`
- **Resolved channel ID:** `UC1yR7j8igrjxXOR0XsCasfw`
  (uploads playlist `UU1yR7j8igrjxXOR0XsCasfw`)
- **Enumerated 2026-07-03** with `yt-dlp --flat-playlist --js-runtimes node` over both
  `/videos` (141 items) and `/streams` (599 items) = **740 videos total**. Meetings live
  under BOTH tabs; the full map is in `channel_videos.csv` (date parsed from title, body
  classified). This is the authoritative, current, and complete video archive for Provo
  council/work meetings — it is still actively updated (latest at enumeration: 2026-06-23).

## Caption type: ASR only

Every meeting video probed carries **only YouTube automatic (ASR) captions** — track
`en-orig` ("English (Original)"). **No human/manual caption track exists on any video.**
So `caption_type = asr` for the entire dataset. These are verbatim-ish but **word-error-prone**
(e.g. councilor surnames render as "Hoben"/"Bogden"/"Hanley"; filler "uh" is transcribed).
Corpus screener (`screen_corpus.py`) on the 10 cleaned files: dict_ratio median **0.847**,
no mojibake / replacement chars / PUA garble / duplicate bodies — normal, clean ASR.

## Per-year video availability (council bodies on YouTube)

Counts of distinct meeting videos on the channel (from `channel_videos.csv`):

| Year | Council (regular) | Work/Study | Neighborhood-district | Auto-captions |
|-----:|------------------:|-----------:|----------------------:|---------------|
| 2013 | 0  | 6  | 0  | ASR (spot-checked present) |
| 2014 | 1  | 24 | 0  | ASR |
| 2015 | 3  | 27 | 0  | **partial** — a 2015 sample had *no* captions |
| 2016 | 6  | 29 | 0  | ASR |
| 2017 | 9  | 28 | 0  | ASR |
| 2018 | 32 | 30 | 0  | ASR |
| 2019 | 28 | 24 | 0  | ASR |
| 2020 | 30 | 22 | 0  | ASR |
| 2021 | 24 | 26 | 0  | ASR |
| 2022 | 26 | 26 | 0  | ASR |
| 2023 | 22 | 24 | 40 | ASR |
| 2024 | 26 | 25 | 22 | ASR |
| 2025 | 27 | 25 | 20 | ASR |
| 2026 | 14 | 11 | 11 | ASR |
| **Total** | **248** | **327** | **93** | — |

- **Coverage is continuous 2014→present** for both regular Council and Work meetings; a
  thin 2013–2015 tail. Auto-captions were present on every year spot-checked EXCEPT a 2015
  sample (`m9IKsegNp_g`) that returned "no subtitles" — YouTube did not auto-caption some
  older/lower-audio-quality uploads, so **pre-2016 caption presence is not guaranteed per
  video** (verify with `--list-subs` before assuming).
- **Neighborhood-district meetings** (West/East/North/Central/Northwest district town-halls)
  appear only from **2023 onward** (93 videos) — a newer civic-engagement series, ASR-captioned.

## Planning Commission: NOT on this channel

Provo's YouTube channel is a **Council/Work-meeting channel**. A full enumeration found
**exactly one Planning Commission video** (`Provo City Planning Commission | May 8, 2019`)
plus one "Joint Meeting with Planning Commission". **PC meetings are not published here.**
This matches the existing repo finding that Provo PC minutes exist only 2025+
(`planning_commission/minutes_unrecovered.csv`) — the PC video record is likewise a **city
publishing gap on YouTube**, not a scraper miss. PC video/transcript, if it exists at all,
would be on a different platform (Zoom/Granicus) or the OpenUtah mirror — not recoverable
via this channel.

## No YouTube → off-platform cutoff

There is **no** date where Provo moved council video off YouTube to Swagit/Granicus/OpenUtah.
The YouTube channel is the live primary and runs through the most recent meeting
(2026-06-23 at enumeration). **OpenUtah (`provo.openutah.org`) is a downstream mirror**, not a
replacement: its own methodology page states it ingests video from "Granicus, CivicPlus,
PrimeGov, Swagit, and YouTube" and re-transcribes. For Provo the upstream is this YouTube
channel, so YouTube captions are the same underlying content, retrieved directly and politely.

## OpenUtah mirror finding (metadata only — robots-blocked)

- `provo.openutah.org` indexes Provo meetings with AI transcripts+summaries: **"186 meetings
  indexed · 123 transcribed"** across Municipal Council, Planning Commission, Parks & Rec
  Board, Arts Council, Landmarks Commission, Board of Adjustment, Neighborhood Districts.
- **`robots.txt` DISALLOWS the transcript text for our agent.** Beyond the site-wide
  `Disallow: /api/`, the file explicitly disallows `/transcripts`, `/transcript`, `/meetings`,
  `/records`, `/minutes`, `/documents`, `/agendas` **for `ClaudeBot` / `anthropic-ai` /
  `Claude-User` / `Claude-SearchBot`** (and GPTBot et al.). So OpenUtah is treated as a
  **summary/metadata source only** — no bulk transcript grab. Its transcripts are also
  AI-generated with the same "may contain errors; video is authoritative" caveat, i.e. no
  quality advantage over the YouTube ASR we pull directly.

## What was retrieved (this run)

- **Sample: 10 meetings, 2024–2025** (5 regular Council + 5 Work), all captions ASR, **0
  unrecovered.** Raw `.en-orig.vtt` in `raw/`; de-duplicated markdown in `text/`. See
  `index.csv`. Word counts 1.8k–30.6k; two short regular meetings (2024-03-05, 2024-09-03)
  are genuinely short sessions (most business handled in the same-day Work meeting).
- This is a **SAMPLE**, not the full backfill. The remaining ~565 council/work meetings are
  mapped in `channel_videos.csv` and pull identically (`caption_type=asr`); throttle ≥33s.

## HIGH-VALUE untranscribed meetings PROPOSED for Whisper (NOT run)

Whisper is **not run** here (expensive; user decides). Two categories warrant it:

1. **Videos with NO YouTube auto-caption** — the only true transcription gap. Confirmed on a
   2015 Work Session (`m9IKsegNp_g`); the pre-2016 tail (2013–2015, ~66 videos) should be
   `--list-subs`-swept and any caption-less high-value ones Whisper'd. These predate the
   repo's 2020 data floor, so LOW priority unless the floor is lowered.
2. **High-stakes meetings where ASR word-errors most hurt** — Whisper would raise fidelity on
   fiscal/juncture meetings even though ASR exists:
   - `2024-08-13` **Truth-in-Taxation Hearing** (`mpnVab72PmM`) and `2022-08-02` Truth-in-Taxation (`kU...`/see channel_videos.csv) — tax-rate testimony, names + dollar figures.
   - Annual **budget retreats / priorities** work meetings (e.g. `2024-02-13`, `2024-01-16`,
     `2022-04-12 Priorities Retreat`, `2020-04-07`/`2020-05-12` Budget Retreats).
   - `2021-11-18` Parking Town Hall, `2018-10-23` Bond Discussion Town Hall — dense public
     testimony the clerk's minutes summarize away.
3. **Planning Commission** cannot be Whisper'd from this channel — the videos are not here
   (see above). That gap needs a different source, not Whisper.

Per-video caption presence for the FULL archive was not exhaustively swept (only spot-checked
one video/year); a complete `--list-subs` sweep before any Whisper batch is the recommended
next step and is cheap (metadata only).
