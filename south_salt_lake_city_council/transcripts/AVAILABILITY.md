# transcripts/ availability — South Salt Lake City

**As of 2026-07-13.** Source type 5 (meeting-video transcripts) of `/expand-city-sources`.

## Platform verdict

- **YouTube — `@SouthSaltLakeCity`** (channel id `UCnIf0PqrH3cERoBB-vyhrbA`) is the city's
  single durable meeting-video archive. Zoom is the live host (per recon), but the public
  archive lives here. **291 uploads; 269 are body meetings** (the rest are 22 promotional clips).
- **No `/streams` tab** — live archives are folded into `/videos`.
- **"Utah Record" mirror** (`UC5hXeD66VUV_w655ionxaSA`): checked, mirrors Draper/Lehi, **0 SSL
  videos.** Not a source.
- **Captions: YouTube ASR (`en`, automatic) — no human/manual track anywhere.** Availability was
  ground-truthed per video via a batched `yt-dlp --list-subs` probe (android player client), not
  assumed.

## Coverage (meeting videos, by year × body — from `channel_videos.csv`)

| Year | CityCouncil | PlanningCommission | RDA | CivilianReviewBoard | total |
|---|---|---|---|---|---|
| 2022 | 1 | 0 | 0 | 1 | 2 |
| 2023 | 27 | 18 | 5 | 12 | 62 |
| 2024 | 42 | 20 | 12 | 13 | 87 |
| 2025 | 39 | 14 | 8 | 13 | 74 |
| 2026 (to Jul 9) | 25 | 8 | 4 | 7 | 44 |
| **total** | **134** | **60** | **29** | **46** | **269** |

Date range **2022-12-05 → 2026-07-09**. (Council counts include Work + Regular meetings, both
posted per Wednesday, plus 2 Board-of-Canvassers videos.)

## Caption statistics

- **All 269 meeting videos carry an `en` YouTube ASR (automatic) caption track — 100%
  coverage.** Zero videos without a caption track; zero manual/human caption tracks anywhere
  (every `caption_type=asr`, `format=caption`). Availability was ground-truthed **per video** by
  a batched `yt-dlp --list-subs` probe (android player client) over all 269 — 269 probed, 269
  with `en`, 0 without, 0 errors. Not one row is inferred.
- **Samples fetched: 10** (sample-only, by design) — spanning 2023–2026, Council/PC/RDA/CRB,
  prioritizing the gap-cliff years. Cleaned to `text/`; corpus screen clean (0 outliers,
  dict_ratio ~0.85 = normal ASR). Raw `.vtt` + `raw/_fetch_log.jsonl` retained.
- The remaining caption-bearing videos are **not fetched but are trivially fetchable on demand**
  with the `android`-client command in `CLAUDE.md` — YouTube has already ASR'd them, so **no
  Whisper is required for any caption-bearing video.**

## ⚠ How this video coverage fills the 2021-mid → 2025 minutes cliff (the headline)

South Salt Lake's recorded minutes are missing for **2021-mid → 2025** (the PMN "Minutes" slot
served agenda packets only — 253 council agenda-only dates; PC recorded minutes start
2023-01-19). The parent repo flags this as the one structural fact governing the city.

**The YouTube archive lands squarely on top of that gap.** For the cliff years **2023–2025**
the channel holds **108 City Council videos and 52 Planning Commission videos** (160 total),
**every one caption-bearing** — i.e. for a large share of the meetings whose *minutes were never
published*, the ASR caption is the **only substantive record of the deliberation and the
motions**. This is the highest-value gap-fill in the repo.

Caveat: an ASR caption is **not** a roll-call record — it has no speaker labels and mangles
names/numbers. It documents *what was discussed and decided in words*, not a clean vote tally.
It supplements, and does not replace, the (missing) minutes.

## Whisper candidates — PROPOSE ONLY (owner decides)

Whisper is **not** needed to obtain text for any caption-bearing video (YouTube ASR already
exists — fetch the `en` track). Whisper's value here would be a **higher-accuracy re-transcription
of the gap-cliff meetings where the caption is the sole record and name/number accuracy matters
for reconstructing decisions.** Prioritized:

1. **2023–2025 City Council Regular meetings** (60 videos) — the meetings whose minutes were
   never published; motions/decisions recoverable only from video. **Top priority.**
2. **2023–2025 City Council Work meetings** (46) — policy deliberation preceding those decisions.
3. **2023–2025 Planning Commission meetings** (52) — land-use recommendations in the same gap;
   PC recorded minutes only begin 2023-01-19, so 2023 especially is thin in the core repo.
4. **2023–2025 RDA meetings** (25) — RDA recorded minutes are sparse repo-wide.

CivilianReviewBoard videos (46) are **not** a land-use/council-record priority (police
use-of-force body, no core-repo counterpart) — listed for completeness only.

2020–2022 has **no** video (channel starts 2022-12) — that earlier slice of the cliff is
covered by the recorded minutes that DO exist (2020–early-2021) plus the honest gap log; video
cannot help there.

## What was checked / method

- Enumerated `/videos` with `yt-dlp --flat-playlist` (291 items); `/streams` tab absent.
- Title-parsed date + body for all (269 meetings, 22 promo). No `release_timestamp` probe needed
  — every meeting title carries its date.
- Batched `--list-subs` (android client, `--sleep-requests 4`) over all 269 meeting videos for
  per-video caption ground truth.
- Fetched 10 sample `en` ASR tracks; cleaned + screened.
- No POST, no auth, no ToS-violating scraping — official yt-dlp/timedtext path only.
