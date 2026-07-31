# Magna — meeting transcripts / recordings: availability

**As-of:** 2026-07-13 · **Source type 5** (`expand-city-sources`, audio-only branch) ·
dataset floor 2017 (entity history; surviving recordings begin 2019 on PMN after the
pre-2018 blob purge).

## Verdict — AUDIO-ONLY: a 2016→2026 PMN meeting-audio archive, NO captions anywhere

Magna is an **audio-only** transcript entity (like White City). There is **no captioned
video source** — nothing to fetch a caption track from — so this dataset is a **link-only
inventory** of the meeting-audio MP3s attached to each Utah Public Notice, plus a Whisper
proposal. **Zero genuine transcripts** exist today.

Two things were ruled out before declaring audio-only:

1. **Meeting VIDEO is a Zoom webinar, live-only.** The city streams council + CRA meetings
   on a fixed Zoom webinar (`us06web.zoom.us/j/8712578306…`, per `magna.utah.gov`), which is
   **not archived** to any public on-demand page. No Granicus / Vimeo / CivicPlus media
   player was found.
2. **No YouTube channel carries Magna meetings.** Probed the plausible handles
   (`raw/_magna_youtube_probe.txt`):
   - **`@MagnaCity`** — the channel exists but has **no `/videos` tab AND no `/streams` tab**
     (an empty placeholder; publishes nothing).
   - **`@MagnaUtah` / `@magnautah`** — both resolve to the **SAME Cyprus High School decoy
     channel** (Cyprus High is the Magna-area high school), **not** the city government.
   - `@MagnaCityUtah`, `@CityofMagna`, `@MagnaCityGovernment`, `@MagnaCityCouncil` — 404
     (do not exist).
   - **Utah Record mirror** (`UC5hXeD66VUV_w655ionxaSA`): all **78** videos enumerated —
     **zero** contain "magna" (`raw/_utah_record_channel_titles.txt`).
   Not confused with the Magna Water District (a separate special district) or Magna
   townships in other states.

The city site `magna.utah.gov` (CivicPlus) hosts agendas/minutes but no scrapable media; the
audio archive below is reached entirely through PMN.

| Platform | Handle / URL | Items | Range | Captions? |
|---|---|---|---|---|
| **PMN audio — Council** (body 5803) | `utah.gov/pmn/files/<id>.MP3` | 321 files / 217 dates (169 live) | 2017 → 2026 (live 2019→) | **NO** (audio only — Whisper) |
| **PMN audio — Planning Commission** (body 1559) | `utah.gov/pmn/files/<id>.MP3` | 136 files / 82 dates (77 live) | 2016 → 2026 (live 2020→) | **NO** (audio only — Whisper) |
| YouTube (`@MagnaCity` etc.) | — | **0 meeting videos** (empty / decoy) | — | n/a |
| Utah Record mirror | `UC5hXeD66VUV_w655ionxaSA` | 78 videos, **0 Magna** | — | n/a |
| Zoom webinar | `us06web.zoom.us/j/…` | live-only, **not archived** | — | n/a |
| Vimeo / Granicus / other | — | none found | — | n/a |

### How each platform was checked
- **PMN audio** — the cumulative list view `/pmn/list/notices.html?id=<body>&page=400` returns
  each body's **entire** notice history in **one GET**, with the file links + category labels
  inline; parsed the audio attachments per notice (`magna_harvest_audio.py`; saved HTML
  `raw/_probe_5803_list.html`, `raw/_probe_1559_list.html`). **All 457 audio URLs HEAD-probed**
  (`magna_probe_sizes.py` → `magna_audio_sizes.csv`): **370 live** (HTTP 200, `audio/mpeg`),
  **87 return 404** — the pre-~2018 PMN **blob purge** (low `file_id`; the same rot that took
  the 2017–mid-2018 township *minutes*, per `meeting_minutes/minutes_unrecovered.csv`). Audio is
  decided by **file extension** (mp3/wav), not the PMN category label (some notices mis-file a
  PDF under "Audio Recording"). Fetch files from the **`www.utah.gov`** host — `pmn.utah.gov`
  302-redirects to the PMN home HTML.
- **YouTube / Utah Record** — enumerated with `yt-dlp --extractor-args
  youtube:player_client=android` (dodges the PO-token false "no captions"); results above.

## Caption stats (the transcript deliverable)
- **Captioned meetings: 0.** No caption track exists on any Magna source — every one of the
  **457** index rows is `caption_type=none`, `format=na`. This is a **true zero** (an audio
  file has no caption track to recover; there is no video with captions), **not** "unrecovered."
- No `text/` transcripts are produced (nothing to clean). The `text/` dir is empty by design.

## PMN audio inventory (per year × body; live = HTTP 200)

```
year  body                  files  live     GB
2016  Planning Commission       3     0    0.00   ─┐ pre-~2018 PMN blob purge (404):
2017  Council / PC            38/3    0    0.00    │  ALL 2016-2018 audio blobs are purged
2018  Council / PC            42/1    0    0.00   ─┘  (87 files; notices prove the meetings)
2019  Council                  39    39    1.30
2020  Council / PC          29/21  29/21   3.02
2021  Council / PC          34/38  34/38   4.22
2022  Council / PC          28/29  28/29   4.61
2023  Council / PC          35/16  35/16   4.48
2024  Council / PC           31/9   31/9   3.82
2025  Council / PC           27/9   27/9   2.75
2026  Council / PC           18/7   18/7   2.28
```
**Live total ≈ 26.48 GB across 370 files** (council 321 files / 217 dates, live 169 dates
2019-01-08→2026-06-23; PC 136 files / 82 dates, live 77 dates 2020-02-13→2026-07-09).
Multi-part meetings are common (e.g. "Audio 2 of 3", "Audio Open"/"Audio Close") — so files
outnumber distinct meeting-dates. **Join to minutes/votes by DATE, not filename.**

## Whisper candidates — PROPOSED ONLY (owner-gated, NOT run)
All **370 live PMN audio files** are flagged `whisper_candidate=yes`. They are the
**highest-value untranscribed source in this repo**:
- **Magna has NO video transcript in ANY era** — there is no YouTube/captioned stream at all,
  so for EVERY meeting the PMN audio is the **only** verbatim record. Magna's minutes are
  **narrative-tally** (mover + seconder + a numeric tally; the majority is honestly unnamed —
  see `meeting_minutes/CLAUDE.md`), so the audio is the only way to hear who said what and how
  the deliberation actually ran.
- **Highest priority: the township era (2019–2025) council + PC audio.** That is the era whose
  minutes most often leave the majority unnamed, and the voting-Chair-titled-"Mayor" seam
  (Peay→Barney) is only fully audible in the recording. The 2026 city-era audio is lower
  priority but equally uncaptioned (no YouTube fallback exists here, unlike sibling Kearns).
- **Bounded, clean, born-audio** (direct MP3, no OCR floor). 370 files ≈ 26.5 GB — a one-shot
  pass. **Not run here** (skill rule). The bytes are public + re-fetchable from `audio_url` in
  `index.csv`; the **87 pre-2019 files are purged and cannot be Whispered**
  (`whisper_candidate=no`).

## Gaps / honest notes
- **2016–2018 audio is lost** (87 files, PMN blob purge) — the notices prove the meetings, the
  audio blobs 404. Same rot that took the 2017–mid-2018 township *minutes*
  (`meeting_minutes/minutes_unrecovered.csv`). Recoverable only if PMN restores the blobs; the
  pre-audio record for those meetings lives in `meeting_minutes/`.
- **PC live audio starts 2020-02-13** (2016–2019 PC audio is either purged or was never
  attached); council live audio starts **2019-01-08**.
- **`caption_type=none` on all 457 rows is a true zero**, not a recovery gap — Magna simply has
  no captioned medium.
- The **CRA** in-recess body has no separate media stream; its audio is folded into the council
  notice/recording of the same night (per `meeting_minutes/` `body=CRA`).
- Zoom-webinar video is not archived and is out of scope (live-only, no ToS-compliant capture).
