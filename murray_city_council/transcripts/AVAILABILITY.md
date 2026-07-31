# Murray City — meeting-video transcripts: availability

**As of:** 2026-07-13 (channel enumerated + captions sampled this date).

## Platform verdict

- **`murraycitylive.com` is NOT a video platform** — it is an HTML frameset wrapping a
  Wix landing page (`imaginationcompany.wixsite.com/murray`, a local production outfit)
  that links out to the archive. It has no caption API.
- **The actual archive is YouTube: channel "MURRAY CITY LIVE"**
  (`https://www.youtube.com/channel/UC_19hfQocAIWupAD5-h6oaw`). Meeting videos live
  almost entirely under the **live-streams tab** (332 streams); the uploads tab has only
  7 body-labeled videos (Council / Planning Commission / Committee of the Whole / MBA).
- The city's CivicPlus **CivicMedia** page (`murray.utah.gov/CivicMedia`) runs on the
  **TikiLive** API but hosts only PR/utility clips — **no meeting videos, no caption
  path there**. Facebook (`/Murraycityutah`) mirrors the live stream; not used (no
  official caption path).
- No `murray.openutah.org` mirror was relevant here (YouTube captions are directly
  fetchable, so the robots-blocked OpenUtah /api/ path was not needed).

## What exists

- **339 unique meeting videos, 2019-10-01 → 2026-07-07** (streams + uploads tabs,
  deduplicated; all 339 resolved to a date).
- **Captions: YouTube automatic (ASR) English tracks — present on every video checked**
  (4 probed with `--list-subs`, 10 fetched; **zero manual/human caption tracks** seen).
  `caption_type=asr` is asserted platform-wide from that sample — no manual captions are
  expected anywhere on this channel.
- Body breakdown (title keywords first, else weekday — council = Tuesday, PC = Thursday):
  **Council 186 · PlanningCommission 136 · CommitteeOfTheWhole 3 · MBA 1 · Canvass 2 ·
  Ceremony 1 · Other 1 · Unknown 9** (the 9 Unknowns are title-dated non-Tue/Thu streams,
  e.g. special sessions; durations 12 s – 3.8 h).
- **Tuesday streams are the whole civic evening in one video** — typically RDA board
  (4:00/5:30 pm) → Committee of the Whole → Council meeting (verified in sampled
  transcripts). A "Council" stream therefore usually contains RDA + CoW deliberation too.

## Date provenance

236 dates parsed from the video title (trusted as printed). The 103 undated
"MURRAY CITY LIVE" streams got dates from YouTube `release_date` — which is **UTC**, so
evening meetings roll over a day: 30 were snapped back one day onto a known minutes date
(`yt_release_date_utc-1_minutes_match`), 23 shifted Wed→Tue / Fri→Thu by cadence alone
(`yt_release_date_utc-1_weekday`), 50 kept as-is. See `date_source` per row.

## What was fetched (SAMPLE-ONLY policy, owner decision 2026-07-05)

**10 caption files** (7.3 MB VTT → ~153k words cleaned text), chosen for maximum value:

| date | body | why |
|---|---|---|
| 2021-12-07 | Council | pre-2023 era check (full evening: CoW + Council, 48.8k words) |
| 2023-01-05 | PlanningCommission | **PC minutes gap** (PC minutes end 2022-11-17) |
| 2023-06-27 | Council | **2023 council TMM minutes gap** |
| 2023-10-03 | Council | 2023 TMM gap (body-labeled upload) |
| 2023-11-14 | Council | 2023 TMM gap — longest 2023 meeting (4.6 h) |
| 2023-12-19 | Council | 2023 TMM gap |
| 2024-05-16 | PlanningCommission | PC gap |
| 2025-06-05 | PlanningCommission | PC gap |
| 2026-06-16 | Council | cross-check vs on-disk minutes (2026-06-16 minutes exist) |
| 2026-06-18 | PlanningCommission | PC gap, most recent PC |

The remaining 329 videos are mapped (`format=na`, `extraction_method=mapped_not_fetched`)
with live watch URLs — captions are fetchable on demand with
`yt-dlp --write-auto-sub --sub-lang en --sub-format vtt --skip-download`.

## The two gaps these videos can fill (high-value backlog)

Cross-referencing `minutes_match` (video date present in the repo's minutes indexes):

1. **2023 council TMM gap — 23 Tuesday videos in 2023 have NO minutes on disk** (the
   Tyler Minutes Management diversion; only 5 of ~24 2023 meetings have minutes). The
   video record is **complete** for 2023 — ASR captions are the only readable record of
   most 2023 council business.
2. **PC 2023+ gap — 63 Thursday videos 2023→2026 have NO minutes** (PC minutes end
   2022-11-17). Again the video record is complete where the minutes record stops.
   (Plus 2020-2022 scattered singles and 3 not-yet-published 2026 council dates;
   96 no-minutes videos total in 2020+.)

## Whisper candidates — NONE needed; propose bulk ASR-caption fetch instead

Every video checked already has a YouTube ASR caption track, so **no meeting is
caption-less → the Whisper candidate list is empty** (Whisper would only re-transcribe
what YouTube ASR already covers, at cost). The actionable proposal (owner decision, not
run) is instead a **bulk yt-dlp caption fetch** of the 86 gap-filling videos:
the 23 no-minutes 2023 council evenings + the 63 no-minutes 2023–2026 PC meetings
(~2–3 s/video, est. ~50 MB VTT). If any of those turn out to lack a caption track at
fetch time, those specific videos become the Whisper candidates.

## Honest limits

- ASR quality: no speaker labels; proper nouns (member names, street/case numbers)
  frequently misrecognized ("Rey the chair" for an actual name, etc.). Never quote ASR
  text as the official record.
- 9 videos have `body=Unknown`; ~15 streams are junk-short (< 10 min — false starts,
  test clips: e.g. 2023-06-14, 12 s). Durations are in the index; filter on
  `duration_sec`.
- Pre-2019-10 meetings have no video record on this channel (channel floor, not a
  collection miss).
- `caption_type=asr` on `format=na` rows is a platform-pattern assertion (sampled, not
  per-video verified) — same convention as west_valley/logan.
- `screen_corpus.py` on `text/` (2026-07-13): 0 hard flags; 7/10 `ends_mid` advisories —
  expected for ASR (the caption track stops when the broadcast cuts, often
  mid-sentence), not an extraction defect. dict_ratio median 0.863, stable across years.
