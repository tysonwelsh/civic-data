# Kearns — meeting transcripts / recordings: availability

**As-of:** 2026-07-13 · **Source type 5** (`expand-city-sources`) · dataset floor 2017
(entity history; recordings begin 2016/2017 on PMN, YouTube captions begin 2026-01).

## Verdict — HYBRID: a captioned 2026 YouTube series ON TOP OF a 2016→2026 PMN audio archive

Kearns has **two recording mediums**, and the second one carries real captions:

1. **PMN meeting audio (the deep archive, no captions).** Every Utah Public Notice on
   **council body 5823** and **PC body 1561** attaches a per-meeting **audio MP3** (a few
   `.wav`/`.m4a`). This runs **2016/2017 → 2026** — the only recording of the township era.
   Audio has **no caption track** → Whisper candidates (owner-gated, **not run**).
2. **YouTube captioned video (city era only, 2026+).** The city's **own** channel
   **@KearnsCity ("Kearns City Government")** posts council live-stream archives; **11 of 12
   carry an English ASR caption track**, which we fetched + cleaned. These 11 are the **only
   genuine transcripts in the Kearns repo.**

The city site `kearns.utah.gov` is Cloudflare-blocked (recon) and hosts no scrapable
media; both sources above are reached without touching it.

| Platform | Handle / URL | Items | Range | Captions? |
|---|---|---|---|---|
| **YouTube — @KearnsCity** (city's own) | `youtube.com/@KearnsCity` (Live tab) | **12 videos** | 2026-01-12 → 2026-07-13 | **11 ASR / 1 none** |
| **PMN audio — Council** (body 5823) | `utah.gov/pmn/files/<id>.MP3` | 213 files / 112 dates live | 2017 → 2026 (live 2019→) | **NO** (audio only — Whisper) |
| **PMN audio — Planning Commission** (body 1561) | `utah.gov/pmn/files/<id>.MP3` | 63 files / 50 dates live | 2016/2020 → 2026 | **NO** (audio only — Whisper) |
| Utah Record mirror | `UC5hXeD66VUV_w655ionxaSA` | 78 videos, **0 Kearns** | — | n/a (no Kearns uploads) |
| Vimeo / Granicus / other | — | none found | — | n/a |

### How each platform was checked
- **YouTube @KearnsCity** — found via web search (`"Kearns" Utah city council meeting
  youtube`), identity confirmed as the government channel (title "Kearns City Government";
  every video is a dated "Kearns City Council Meeting"). The channel has **no `/videos` tab**;
  the meetings live under the **Live/streams tab** (12 live-stream archives), enumerated with
  `yt-dlp --flat-playlist --js-runtimes node --extractor-args youtube:player_client=android`
  (list saved to `raw/_kearnscity_streams.txt`). `--list-subs` on all 12 → **11 expose English
  automatic (ASR) captions; only the newest (2026-07-13, `vgKXlTCdkkk`) has none** (too recent
  / never processed). **Not** confused with the Kearns Improvement (water) District or Oquirrh
  Park (recon decoys) — the channel is unambiguously the city council.
- **PMN audio** — the cumulative list view `/pmn/list/notices.html?id=<body>&page=<big>` returns
  each body's **entire** notice history in **one GET**, with the file links + category labels
  inline; parsed the `(Audio Recording)` attachments per notice (`kearns_harvest_audio.py`;
  saved HTML `raw/_probe_5823_list.html`, `raw/_probe_1561_list.html`). **All 276 audio URLs
  HEAD-probed** (`kearns_audio_sizes.csv`): **218 live** (HTTP 200, `audio/mpeg`/`audio/mp4`),
  **58 return 404** — the pre-~2018-07 PMN **blob purge** (low `file_id`; same rot that took the
  2017–mid-2018 township *minutes*). Audio decides on **extension**, not the PMN category label
  (some notices mis-file a PDF under "Audio Recording").
- **Utah Record mirror** (`UC5hXeD66VUV_w655ionxaSA`): all **78** videos enumerated — **zero**
  contain "kearns" (`raw/_utah_record_channel_titles.txt`).

## Caption stats (the transcript deliverable)
- **Captioned meetings: 11** (all city-era 2026), English **ASR** auto-captions from
  @KearnsCity. Raw `.vtt` in `raw/cap_<date>_<videoid>.en.vtt`; cleaned to
  `text/<date>_<videoid>.md` (headed "AUTOMATIC TRANSCRIPTION — ASR, expect word errors; not an
  official record"). **~154,000 words total.** `screen_corpus.py`: dict_ratio median **0.866**,
  no weird-char / split-word outliers — healthy spoken-word ASR (the `repeated_line` /
  `ends_mid` flags are inherent to rolling ASR captions and stream cut-offs).
- **1 YouTube video has no captions** (2026-07-13) → `caption_type=none`, `format=na`, no text.
- **All 276 PMN audio rows** are `caption_type=none`, `format=na` — a **true zero** (an audio
  file has no caption track to recover), not "unrecovered."

## PMN audio inventory (per year × body; live = HTTP 200)

```
year  body                 files  live     GB
2016  Planning Commission      1     1    0.06   (pre-floor township PC recording — genuine)
2017  Council                 28     0    0.00   ─┐ pre-~2019 PMN blob purge (404):
2018  Council                 30     0    0.00   ─┘ ALL 2017–2018 council audio is purged
2019  Council                 27    27    1.10
2020  Council / PC            20/9  20/9  1.85
2021  Council / PC           23/14 23/14  2.48
2022  Council / PC           16/11 16/11  1.21
2023  Council / PC           19/10 19/10  1.97
2024  Council / PC            18/8  18/8  1.79
2025  Council / PC            21/7  21/7  1.71
2026  Council / PC            11/3  11/3  1.41
```
**Live total ≈ 13.60 GB across 218 files** (council 213 files / 112 dates 2019→2026; PC 63 /
50 dates). Multi-part meetings are common (e.g. "…Audio 4 of 5", "Audio Open"/"Audio Close") —
so files > distinct meeting-dates. **Join to minutes/votes by DATE, not filename.**

## Whisper candidates — PROPOSED ONLY (owner-gated, NOT run)
All **218 live PMN audio files** are flagged `whisper_candidate=yes`. They are the **highest-value
untranscribed source in this repo**:
- **The township era (2019–2025) has NO video transcript** — YouTube starts 2026-01. For every
  township meeting the audio is the **only** verbatim record, and Kearns minutes are
  **narrative-tally** (mover + seconder + a numeric tally; the majority is honestly unnamed), so
  the audio is the only way to hear who said what. **Prioritize 2019–2025 council + PC audio.**
- The **2026 city-era audio is lower priority** — those meetings are already ASR-captioned on
  YouTube (this dataset's `text/`). Whisper would only corroborate.
- **Bounded, clean, born-audio** (direct MP3, no OCR floor). 218 files ≈ 13.6 GB — a one-shot pass.
- **Not run here** (skill rule). The bytes are public + re-fetchable from `audio_url` in
  `index.csv`; **58 pre-2019 files are purged and cannot be Whispered** (`whisper_candidate=no`).

## Gaps / honest notes
- **2017–2018 council audio is lost** (58 files, PMN blob purge) — the notices prove the meetings,
  the audio blobs 404. Same rot as the township-minutes back-catalog. Recoverable only if PMN
  restores the blobs. The pre-audio record for those meetings lives in `meeting_minutes/`.
- **YouTube captions are city-era only (2026-01→)** — 4 councilmembers + voting Mayor Valdez era.
  No pre-2026 video/captions exist anywhere (the channel's oldest upload is 2026-01-12).
- **The 2016-02-08 PC file is pre-floor** (Kearns Township Planning Commission, before the
  2017-01-01 floor) but is a genuine surviving recording — kept in the inventory, flagged here.
- **`caption_type=none` on audio rows is a true zero**, not a recovery gap.
- The **CRA** in-recess body has no separate media stream; its audio/video is folded into the
  council notice/stream of the same night (e.g. 2026-05-11 "CRA and City Council Meetings").
