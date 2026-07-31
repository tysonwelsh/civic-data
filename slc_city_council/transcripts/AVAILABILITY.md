# SLC meeting-video transcripts — availability

_As-of 2026-07-05. Additive dataset; does not modify `meeting_minutes/`, `planning_commission/`, or any other layer._

## Policy for this build: SAMPLE-ONLY

Owner decision (2026-07-05): build the **full video→date map** for the channel, but
download only a **~10-meeting ASR caption sample** (most-recent Council series). Salt Lake
City is a large city with >1,100 archived meeting videos; the value here is the complete map
plus a representative taste of the caption text. The remaining videos are mapped, not
retrieved — recover any of them on demand with the recipe in `CLAUDE.md`.

## Channels / platforms found

| Platform | Handle / URL | Role |
|---|---|---|
| **SLC Live Meetings** (YouTube) | `https://www.youtube.com/@SLCLiveMeetings` (`/streams` + `/videos`) | **Primary.** Government broadcast repository for ALL SLC public meetings — Council, RDA/CRA/LBA, Planning Commission, Planning Division hearings. This is the enumerated source. |
| SLCtv (YouTube) | `https://www.youtube.com/user/SLCtvmedia` | Salt Lake City cable channel (SLCtv / Comcast 17, PrismTV 8001/8501). General city programming; meeting recordings live on SLC Live Meetings, not here. |
| @SLCCouncil (YouTube) | `https://www.youtube.com/c/SLCCouncil` | Council-office channel (recaps/promo), not the meeting archive. |
| SLCtv.com | `https://slctv.com/livestream` | Live cable feed only (no on-demand archive). |
| SLC Media portal | `https://www.slc.gov/slcmedia/` | Landing page that points the public to the SLC Live Meetings YouTube channel. |
| PrimeGov | `https://slc.primegov.com/` | Agenda/minutes portal; embeds/links the YouTube video, not a separate media host. |

**Captions:** YouTube **auto-generated (ASR) English captions**. No human/manual caption
tracks were found (`caption_type=asr` throughout). ASR = expect word errors; **not an
official record** — the clerk's minutes remain authoritative.

## What was mapped

- **Enumerated via** `yt-dlp --flat-playlist` against both `@SLCLiveMeetings/streams`
  (930 videos) and `/videos` (212 videos) — the two lists are disjoint. **1,142 unique
  videos** total.
- Date parsed from the video title (`MM/DD/YYYY` or `Month D, YYYY`): **1,089 dated**,
  53 undated (mostly pre-2017 test/early uploads titled only "Formal Meeting" / "Work
  Session"). Full map in **`channel_videos.csv`** with a `minutes_match` flag.
- **487** mapped videos fall on a date present in
  `meeting_minutes/minutes_index.csv` (`minutes_match=true`).
- Coverage by year: 2011 (1), 2016 (40), 2017 (69), 2018 (94), 2019 (114), **2020 (112),
  2021 (125), 2022 (121), 2023 (120), 2024 (112), 2025 (116), 2026 (65)**.
  Oldest 2011-12-12, newest 2026-06-24. The 2020–2026 target window is **fully covered**.
- Body mix (title-classified): Council series (Council/RDA/CRA/LBA) 790, Planning
  Commission 186, Planning Division / Appeals / Admin hearings 48, Other/undated 118.

**Cutoff:** none upstream — the channel is live and current (newest video 2026-06-24). The
map is a snapshot as-of 2026-07-05; re-run the enumeration to refresh. `minutes_match=false`
for the few 2026-06-11/16/24 videos only because `minutes_index.csv` ends 2026-06-09
(minutes not yet posted), not because the video is unmatched.

## Sample retrieved (10 meetings, all `caption_type=asr`, all `minutes_match=true`)

Most-recent Council-series meetings, mixing Formal / Work Session / CRA / LBA-CRA-Council:

| Date | Meeting | video_id |
|---|---|---|
| 2026-06-09 | Formal Meeting | vssFbwKYvOE |
| 2026-06-09 | Council Work Session | npUPFIimiAg |
| 2026-06-09 | CRA Meeting | CSCy3HfjszI |
| 2026-05-19 | LBA, CRA, and City Council Formal | P-oy8t21r-k |
| 2026-05-19 | Council Work Session | jgtdb_5uTFI |
| 2026-05-14 | Council Work Session | qURCVMnJ5HE |
| 2026-05-12 | Council Work Session | B-vVy1uGU20 |
| 2026-05-12 | CRA Meeting | 4hffGKRRRfA |
| 2026-05-05 | LBA, CRA, and City Council Formal | PsVcAWvfDXw |
| 2026-05-05 | Council Work Session | lMyJuQRSTd4 |

Raw `.vtt` in `raw/`, cleaned text in `text/`, provenance (sha256, bytes, retrieved_utc) in
`raw/_fetch_log.jsonl`, machine-readable index in `index.csv`.

## Whisper candidates (PROPOSE only — not run)

All 1,142 videos have YouTube ASR captions, so nothing is *uncaptioned*. Whisper would only
add value where a higher-accuracy transcript materially helps analysis. Highest-value
targets (still ASR-captioned today, but dense/consequential deliberation where word-error
matters):

1. **Budget-adoption Formal Meetings** (annual June) — e.g. 2026-06-09 Formal (vssFbwKYvOE)
   and its Work Sessions; heavy dollar figures / department names that ASR garbles.
2. **RDA/CRA project votes** — the interleaved CRA formal meetings (e.g. 2026-05-19
   P-oy8t21r-k) where TIF districts, developer names, and parcel IDs are spoken.
3. **Major rezone / master-plan public hearings** — pick from `channel_videos.csv` by
   cross-referencing contested land-use votes in `db/slc.db` / `meeting_minutes/all_votes.csv`
   (any date with a Nay/Abstain) to spend Whisper budget only where deliberation was
   substantive.

Recommend Whisper `medium`/`large-v3` only on an owner-selected shortlist; keep the ASR
sidecar for the rest.
