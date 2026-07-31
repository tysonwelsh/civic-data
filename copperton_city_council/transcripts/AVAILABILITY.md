# Copperton — meeting transcripts / recordings: availability

**As-of:** 2026-07-14 · **Source type 5** (`expand-city-sources`, audio-only branch) ·
dataset floor 2017 (entity history; surviving recordings begin 2018-12 on PMN after the
pre-~mid-2018 blob purge).

## Verdict — AUDIO-ONLY: a 2017→2026 PMN meeting-audio archive, NO captions anywhere

Copperton (Town of ~800 residents; metro township 2017 → Town 2024-05-01) is an
**audio-only** transcript entity (like siblings **Magna** and **White City**). There is
**no captioned video source** — nothing to fetch a caption track from — so this dataset is a
**link-only inventory** of the meeting-audio files attached to each Utah Public Notice,
plus a Whisper proposal. **Zero genuine transcripts** exist today.

Two things were ruled out before declaring audio-only:

1. **No YouTube channel carries Copperton meetings.** Every plausible handle 404s
   (`raw/_copperton_youtube_probe.txt`): `@CoppertonUtah`, `@CoppertonTown`,
   `@TownofCopperton`, `@CoppertonCity`, `@CoppertonUT`, `@coppertonutah`,
   `@CoppertonTownUtah`, `@CoppertonMetroTownship` — **none exist**. A web search for
   "Copperton Utah town council meeting youtube" surfaced only PMN notices and a
   `citizenportal.ai` scrape of the same PMN audio — **no official channel**. An 800-pop town
   runs no meeting-video channel. (Not confused with the Copperton Improvement District or
   any other-place decoy.)
2. **Utah Record mirror** (`UC5hXeD66VUV_w655ionxaSA`): all **78** videos enumerated —
   **zero** contain "copperton" (`raw/_utah_record_channel_titles.txt`).

Where meeting video exists at all it is a **live-only Zoom hybrid** (the May-2026 notices
describe a virtual/in-person hybrid), **not archived** to any public on-demand page. No
Granicus / Vimeo / CivicPlus media player was found. The town's GoDaddy site
(`copperton.utah.gov`) hosts agendas/minutes but no scrapable media; the audio archive below
is reached entirely through PMN.

| Platform | Handle / URL | Items | Range | Captions? |
|---|---|---|---|---|
| **PMN audio — Council** (body 5831) | `utah.gov/pmn/files/<id>.<ext>` | 145 files / 130 dates (105 live) | 2017 → 2026 (live 2018-12→) | **NO** (audio only — Whisper) |
| **PMN audio — Planning Commission** (body 1560) | `utah.gov/pmn/files/<id>.<ext>` | 15 files / 12 dates (all live) | 2020 → 2025 | **NO** (audio only — Whisper) |
| YouTube (`@Copperton*`) | — | **0** (all handles 404) | — | n/a |
| Utah Record mirror | `UC5hXeD66VUV_w655ionxaSA` | 78 videos, **0 Copperton** | — | n/a |
| Zoom hybrid | — | live-only, **not archived** | — | n/a |
| Vimeo / Granicus / other | — | none found | — | n/a |

### How each platform was checked
- **PMN audio** — the cumulative list view `/pmn/list/notices.html?id=<body>&page=400` returns
  each body's **entire** notice history in **one GET**, with the file links + category labels
  inline; parsed the audio attachments per notice (`copperton_harvest_audio.py`; saved HTML
  `raw/_probe_5831_list.html`, `raw/_probe_1560_list.html`). **All 160 audio URLs HEAD-probed**
  (`copperton_probe_sizes.py` → `copperton_audio_sizes.csv`): **120 live** (HTTP 200,
  `audio/mpeg`/`audio/mp4`/`audio/x-wav`), **40 return 404** — the pre-~mid-2018 PMN **blob
  purge** (the same rot that took the 2017-02→2018-06 township *minutes*, per
  `meeting_minutes/minutes_unrecovered.csv`). Audio is decided by **file extension**
  (mp3/m4a/wav), not the PMN category label. Fetch files from the **`www.utah.gov`** host —
  `pmn.utah.gov` 302-redirects to the PMN home HTML.
- **YouTube / Utah Record** — enumerated with `yt-dlp --extractor-args
  youtube:player_client=android` (dodges the PO-token false "no captions"); results above.

## Caption stats (the transcript deliverable)
- **Captioned meetings: 0.** No caption track exists on any Copperton source — every one of
  the **160** index rows is `caption_type=none`, `format=na`. This is a **true zero** (an audio
  file has no caption track to recover; there is no video with captions), **not** "unrecovered."
- No `text/` transcripts are produced (nothing to clean). The `text/` dir is empty by design.

## PMN audio inventory (per year × body; live = HTTP 200)

```
year  body                  files  live     media
2017  Council                  24     0    (all 404 — pre-mid-2018 blob purge)
2018  Council                  17     1    (Jan–Nov purged; first live 2018-12-19)
2019  Council                  13    13
2020  Council / PC           15/1  15/1
2021  Council / PC           15/2  15/2
2022  Council / PC           13/4  13/4
2023  Council / PC           18/4  18/4
2024  Council / PC           12/2  12/2
2025  Council / PC           12/2  12/2
2026  Council                   6     6
```
**Live total ≈ 12.50 GB across 120 files** (council 105 files / 96 dates, live
2018-12-19→2026-06-17; PC 15 files / 12 dates, live 2020-09-23→2025-12-03). Media types:
**138 mp3, 21 wav, 1 m4a.** **12 live dates carry more than one audio file** (multi-part
recordings, e.g. 2019-06-19 has 2) — so files outnumber distinct meeting-dates. **Join to
minutes/votes by DATE, not filename.**

## Whisper candidates — PROPOSED ONLY (owner-gated, NOT run)
All **120 live PMN audio files** are flagged `whisper_candidate=yes`. They are a
**high-value untranscribed source**:
- **Copperton has NO video transcript in ANY era** — there is no YouTube/captioned stream at
  all, so for EVERY meeting the PMN audio is the **only** verbatim record. Copperton's minutes
  are **narrative-tally** (mover + seconder + a numeric tally; the unanimous majority is
  honestly unnamed — see `meeting_minutes/CLAUDE.md`), so the audio is the only way to hear who
  said what and how the deliberation ran.
- **Highest-value targets: the ~10 named/contested council motions** (the 2020 UFA
  agreement/resolution 3-2 splits with a named "Mayor Clayton voted 'Nay'"; the 2023 0-4
  SLVLESA tax-rate rejection) — the audio is where the dissent and reasoning are fully audible.
- **Bounded, clean, born-audio** (direct MP3, no OCR floor). 120 files ≈ 12.5 GB — a one-shot
  pass. **Not run here** (skill rule). The bytes are public + re-fetchable from `audio_url` in
  `index.csv`; the **40 pre-2019 files are purged and cannot be Whispered**
  (`whisper_candidate=no`).

## Gaps / honest notes
- **2017 → Nov-2018 council audio is lost** (34 distinct dates / 40 files, PMN blob purge) —
  the notices prove the meetings, the audio blobs 404. This overlaps the documented
  2017-02→2018-06 council-*minutes* purge (`meeting_minutes/minutes_unrecovered.csv` /
  `README.md`), but note the **audio purge boundary runs later than the minutes one**: minutes
  survive from **2018-07-18**, yet the audio for 2018-07 through 2018-11 is still 404 — so
  several 2018-H2 meetings have recovered minutes but **no** recoverable audio. First live
  council audio is **2018-12-19**.
- **PC audio starts 2020-09-23** and is sparse (12 dates through 2025-12-03) — Copperton's
  Planning Commission cancels most meetings (recon), so this is expected low volume, not a
  gap; no PC audio is purged.
- **`caption_type=none` on all 160 rows is a true zero**, not a recovery gap — Copperton
  simply has no captioned medium.
- Zoom-hybrid video is not archived and is out of scope (live-only, no ToS-compliant capture).
