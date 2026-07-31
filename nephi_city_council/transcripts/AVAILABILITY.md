# transcripts/ — video availability & what was checked

**Verdict: Nephi began publishing City Council meeting video only in May 2026.** For the
whole 2020–2026 window there is **no published meeting video except the final ~6 weeks**
(2026-05-05 → 2026-06-16). Of the meeting videos that *do* exist, **4 of 4 were captioned
and retrieved** (100% of extant meeting video). This is a small rural city (~6,500) that,
like many Utah towns, simply did not stream its council for most of the study period —
the gap is the finding, not a failure to look.

Checked 2026-07-05.

## Sources checked

| Source | URL | Result |
|---|---|---|
| YouTube **@NephiCity** (new channel) | `youtube.com/channel/UCbTtTpWfekf00N_w-_houEw` | **4 council-meeting livestreams** (May–Jun 2026) + 1 *scheduled* Truth-in-Taxation stream (not yet aired). 63 subscribers; channel is new. No `videos`/`playlists` tab. **This is the only meeting-video source.** |
| YouTube **Nephi City** (older channel) | `youtube.com/channel/UCsX4gp2ARaP6cmTMYFeTiBg` | 8 videos, **all short informational clips** (SharedSolar, NetMetering, The Hive, Public Library, a 2020 ordinance notice, a 2020 mayor address, Citizens Academy 2018, PAR Tax). **No council-meeting recordings.** Listed in `channel_videos.csv` (`is_meeting=false`) for completeness. |
| **nephi.openutah.org** (OpenUtah mirror) | `nephi.openutah.org` | **0 meetings indexed, 0 transcribed.** No video map for Nephi. (`/api/` is robots-disallowed and was not scraped.) |
| Nephi City "Video Hearings" page | `nephi.utah.gov/492/Video-Hearings` | **Justice-court** defendant-rights videos only (English/Spanish). Unrelated to council meetings. |
| Web search — city YouTube / livestream / Facebook | Google/WebSearch | Surfaced only the two channels above. No Facebook Live archive or third-party stream found. |
| YouTube keyword search `Nephi Utah city council meeting` | `ytsearch` | Confirmed only the two "Nephi City" channels; the rest were unrelated (out-of-state councils, railfan clips, news segments). |

## What was retrieved

All 4 extant council-meeting videos, via the sanctioned `yt-dlp` path (auto-captions = **ASR**):

| Date | Video | Length | Minutes in repo? |
|---|---|---|---|
| 2026-05-05 | `fpy8_tgnR24` | ~3h37m | yes |
| 2026-05-19 | `PeBTm7gpW7M` | ~1h02m | yes |
| 2026-06-02 | `p3CSCiciucY` | ~2h13m | yes |
| 2026-06-16 | `Deoscu1ibyQ` | ~0h36m | **no** (last minutes on file 2026-06-09) |

Per the SAMPLE-ONLY policy the retrieval cap was ~10 meetings; only 4 meeting videos exist,
so the "sample" is the full extant set. `raw/<date>.vtt` = verbatim download;
`text/<date>.md` = cleaned ASR sidecar; `raw/_fetch_log.jsonl` = provenance (url, bytes,
sha256, cmd, UTC).

## Not retrieved

- `_6V__cJJ8XM` **"Truth in Taxation Meeting"** — a *scheduled* future livestream (had not
  aired at retrieval; YouTube reported "begins in ~36 days"). No captions exist yet; it will
  auto-caption once aired. Row present in `index.csv` (`format=na`) and `channel_videos.csv`
  (`category=council_meeting_scheduled`).
- **2020-01 → 2026-04** council/PC/Board-of-Adjustment meetings — **no video was ever
  published.** The authoritative record for those meetings remains the clerk's minutes in
  `meeting_minutes/` and `planning_commission/`. This is an honest source gap, not an
  extraction gap.

## Whisper?

**Not proposed.** Every extant meeting video already carries YouTube ASR captions, which were
retrieved. There is no high-value *uncaptioned* meeting video to justify a Whisper pass. (The
only uncaptioned item, the not-yet-aired Truth-in-Taxation stream, will receive auto-captions
on air — re-run the `yt-dlp` recipe in `CLAUDE.md` on the next refresh.)
