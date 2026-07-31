# Emigration Canyon — meeting transcripts / recordings: availability

**As-of:** 2026-07-14 · **Source type 5** (`expand-city-sources`, audio-only branch) ·
dataset floor 2017 (entity history; surviving recordings begin 2019-01 on PMN after the
pre-~mid-2018 blob purge).

## Verdict — AUDIO-ONLY: a 2017→2026 PMN meeting-audio archive, NO captions anywhere

Emigration Canyon (~1,600 residents; metro township 2017 → City 2024-05-01) is an
**audio-only** transcript entity (like siblings **Copperton**, **Magna**, and **White
City**). There is **no captioned video source** — nothing to fetch a caption track from — so
this dataset is a **link-only inventory** of the meeting-audio files attached to each Utah
Public Notice, plus a Whisper proposal. **Zero genuine transcripts** exist today.

Two things were ruled out before declaring audio-only:

1. **No YouTube channel carries Emigration Canyon meetings.** Every plausible handle 404s
   (`raw/_emig_youtube_probe.txt`): `@EmigrationCanyonUtah`, `@EmigrationCanyonCity`,
   `@TownofEmigrationCanyon`, `@CityofEmigrationCanyon`, `@EmigrationCanyonUT`,
   `@EmigrationCanyonMetroTownship`, `@EmigrationCanyonTownship` — **none exist.** The one
   handle that *does* resolve, **`@emigrationcanyon`**, is a **name-collision DECOY**: a
   personal account holding **3 non-government videos from 2009** ("Noah Mozart Minuet in C",
   etc. — `raw/_emig_channel_videos.txt`), not the government. A web search for "Emigration
   Canyon Utah city council meeting youtube" (2026-07-14) surfaced **only** Utah Public Notice
   (PMN body 5809) agendas/notices and `emigration.utah.gov` — **no official channel.** A
   ~1,600-pop canyon community runs no meeting-video channel. (Not confused with the separate
   **Emigration Canyon Improvement District** sewer/water special district, nor the legacy
   `emigrationcanyon.org` Community Council advocacy site — see recon §Do-not-confuse.)
2. **Utah Record mirror** (`UC5hXeD66VUV_w655ionxaSA`): all **78** videos enumerated —
   **zero** contain "emigration" (`raw/_utah_record_channel_titles.txt`).

Where meeting video exists at all it is a **live-only Zoom/virtual hybrid** (recent notices
describe a virtual/in-person hybrid), **not archived** to any public on-demand page. No
Granicus / Vimeo / CivicPlus media player was found (there is no city CMS at all — recon §1).
The audio archive below is reached entirely through PMN.

| Platform | Handle / URL | Items | Range | Captions? |
|---|---|---|---|---|
| **PMN audio — Council** (body 5809) | `utah.gov/pmn/files/<id>.<ext>` | 157 files / 125 dates (126 live) | 2017 → 2026 (live 2019-01→) | **NO** (audio only — Whisper) |
| **PMN audio — Planning Commission** (body 1562) | `utah.gov/pmn/files/<id>.<ext>` | 87 files / 65 dates (85 live) | 2018 → 2026 (live 2019-07→) | **NO** (audio only — Whisper) |
| YouTube (`@EmigrationCanyon*`) | — | **0 government** (all handles 404 except a 3-video personal decoy) | — | n/a |
| Utah Record mirror | `UC5hXeD66VUV_w655ionxaSA` | 78 videos, **0 Emigration** | — | n/a |
| Zoom / virtual hybrid | — | live-only, **not archived** | — | n/a |
| Vimeo / Granicus / other | — | none found (no city CMS) | — | n/a |

### How each platform was checked
- **PMN audio** — the cumulative list view `/pmn/list/notices.html?id=<body>&page=400`
  returns each body's **entire** notice history in **one GET** (the bare `?id=` form 500s;
  page 400 == page 800 == 238 council / 290 PC notices, so history is fully captured), with
  the file links + category labels inline; parsed the audio attachments per notice
  (`emig_harvest_audio.py`; saved HTML `raw/_probe_5809_list.html`,
  `raw/_probe_1562_list.html`). **All 244 audio URLs HEAD-probed** (`emig_probe_sizes.py` →
  `emig_audio_sizes.csv`): **211 live** (HTTP 200, `audio/mpeg`), **33 return 404** — the
  pre-~mid-2018 PMN **blob purge**. Audio is decided by **file EXTENSION** (mp3/m4a/wav — note
  Emigration Canyon uses an **UPPERCASE `.MP3`**; matching is case-insensitive), not the PMN
  category label. Fetch files from the **`www.utah.gov`** host — `pmn.utah.gov` 302-redirects
  to the PMN home HTML.
- **YouTube / Utah Record** — enumerated with `yt-dlp --extractor-args
  youtube:player_client=android` (dodges the PO-token false "no captions"); results above.

## Caption stats (the transcript deliverable)
- **Captioned meetings: 0.** No caption track exists on any Emigration Canyon source — every
  one of the **244** index rows is `caption_type=none`, `format=na`. This is a **true zero**
  (an audio file has no caption track to recover; there is no video with captions), **not**
  "unrecovered."
- No `text/` transcripts are produced (nothing to clean). The `text/` dir is empty by design.

## PMN audio inventory (per year × body; live = HTTP 200)

```
year  body                  files  live     media
2017  Council                  17     0    (all 404 — pre-mid-2018 blob purge)
2018  Council                  14     0    (all 404)
2018  Planning Commission       2     0    (all 404)
2019  Council                  18    18    (first live council 2019-01-24)
2019  Planning Commission       2     2    (first live PC 2019-07-17)
2020  Council / PC            9/10   9/10
2021  Council / PC           20/4   20/4
2022  Council / PC           14/8   14/8
2023  Council / PC          22/22  22/22
2024  Council / PC          18/17  18/17
2025  Council / PC          17/15  17/15
2026  Council / PC            8/7    8/7
```
**Live total ≈ 21.29 GB across 211 files** (council 126 files / 96 dates, live
2019-01-24→2026-05-19; PC 85 files / 64 dates, live 2019-07-17→2026-07-09). Media types:
**240 mp3, 4 m4a** (2022-01-25, 2024-02-22, 2025-08-20, 2026-02-23 council specials). **43
live dates carry more than one audio file** (council 25, PC 18 — multi-part recordings) — so
files outnumber distinct meeting-dates. **Join to minutes/votes by DATE, not filename.**

## Whisper candidates — PROPOSED ONLY (owner-gated, NOT run)
All **211 live PMN audio files** are flagged `whisper_candidate=yes`. They are a
**high-value untranscribed source**:
- **Emigration Canyon has NO video transcript in ANY era** — there is no YouTube/captioned
  stream at all, so for EVERY meeting the PMN audio is the **only** verbatim record. The
  council's minutes are **narrative-tally** (mover + seconder + a numeric tally; the unanimous
  majority is honestly unnamed — see `meeting_minutes/CLAUDE.md`), so the audio is the only
  way to hear who said what and how the deliberation ran.
- **Highest-value targets: the handful of named/contested motions** — the 5 contested council
  motions (2021-04-27 Brems recusal, 2021-08-24, 2021-12-14, 2023-08-22 full 5-name roll,
  2023-10-24) and the 3 contested PC motions (per `meeting_minutes/CLAUDE.md`) — plus the **2
  scanned council docs (2024-02-22, 2025-01-28) that yielded 0 extractable motions** from OCR;
  their audio is the recoverable record of what those meetings decided.
- **Bounded, clean, born-audio** (direct MP3/M4A, no OCR floor). 211 files ≈ 21.3 GB — a
  one-shot pass. **Not run here** (skill rule). The bytes are public + re-fetchable from
  `audio_url` in `index.csv`; the **33 pre-2019 files are purged and cannot be Whispered**
  (`whisper_candidate=no`).

## Gaps / honest notes
- **2017 → 2018 audio is lost** (30 distinct dates / 33 files, PMN blob purge; last purged
  date 2018-12-19) — the notices prove the meetings, the audio blobs 404. This is the **same
  pre-~mid-2018 rot** documented for the township-era minutes
  (`meeting_minutes/minutes_unrecovered.csv`; recovered council minutes begin 2018-10, PC
  2018-11). First live audio: **council 2019-01-24, PC 2019-07-17.** Note the audio purge runs
  slightly *later* than the minutes one — a few late-2018 meetings have recovered minutes but
  no recoverable audio.
- **PC audio is thinner 2019–2021** (2/4 live dates/yr) then dense 2022+ — Emigration Canyon's
  Planning Commission was low-volume early; not a scraper gap.
- **`caption_type=none` on all 244 rows is a true zero**, not a recovery gap — Emigration
  Canyon simply has no captioned medium.
- Zoom/virtual-hybrid video is not archived and is out of scope (live-only, no ToS-compliant
  capture).
