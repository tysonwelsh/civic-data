# Midvale transcripts — availability

**As-of:** 2026-07-13 · **Source type 5** (meeting-video transcripts) · sample-only build.

## Platform verdict — YouTube (single official channel)

Midvale City livestreams and archives its public meetings on **one official YouTube
channel**:

- **Midvale City Government** — channel `UCLDszK2kMUHuc3-bV-BBslQ`
  (`https://www.youtube.com/channel/UCLDszK2kMUHuc3-bV-BBslQ`).
- The city's own **Livestream Meetings** page
  (`.../government/departments/livestream_meetings.php`) points to this channel; it
  states City Council, Redevelopment Agency, Municipal Building Authority, and Planning &
  Zoning Commission meetings are streamed live and archived there.
- Meetings live under the channel's **`/streams`** tab (268 items). The `/videos` tab
  (11 items) is almost entirely promotional clips (festivals, staff features) — only 2
  are meetings, both also enumerable via `/streams`.

**Third-party "Utah Record - Public Meetings" mirror** (`UC5hXeD66VUV_w655ionxaSA`,
which carries draper/lehi/sandy/layton): **checked — does NOT carry Midvale.** Midvale's
own channel is the sole video source. (OpenUtah has no Midvale meeting mirror; the
generic OpenUtah verbatim-transcript API is robots-blocked and is metadata-only under the
polite rule regardless.)

No Granicus/Vimeo/CivicClerk video stream was found — the Revize CMS site embeds the
YouTube player, it does not self-host video.

## Enumeration — 258 governing-body meetings, 2020-04-08 → 2026-07-08

From `yt-dlp --flat-playlist` over `/streams` + `/videos` (raw dumps retained in
`raw/_enum_streams.tsv`, `raw/_enum_videos.tsv`; note yt-dlp `--print` emits a **literal
two-char `\t`**, not a real tab — the parser splits on that). After deduping by video id
and dropping 21 non-meeting promo videos:

| Body | Videos | Notes |
|---|---|---|
| Council (incl. special / budget retreat / annual legislative) | 155 | Tuesdays (1st & 3rd + specials) |
| PlanningCommission (Planning & Zoning) | 101 | Wednesdays (2nd & 4th) |
| RDA (Redevelopment Agency, titled explicitly) | 2 | mostly convened in-session under Council; rarely titled separately on YouTube |

- **Dating:** titles-first — 250 of 258 carry an explicit date in the title
  (`MM/DD/YYYY`, `MM-DD-YYYY`, or `Month Dth, YYYY`). The 8 undated meetings were dated
  from `release_timestamp` converted to **America/Denver** (`date_source` column records
  which); every recovered date lands on the body's expected weekday (Council→Tue,
  PC→Wed), corroborating the conversion.
- The archive **floor (2020-04)** predates the repo's minutes floor slightly and is a
  YouTube-archive floor, not a publishing gap — Midvale began archiving meetings to
  YouTube around the April 2020 remote-meeting shift.
- RDA is nearly always convened *in-session* inside a Council meeting (see the repo's
  `body=RDA` motion rows), so it seldom gets its own YouTube video — the 2 RDA-titled
  videos are the exception, not an RDA gap.

## Caption availability — 100% ASR, 0% manual (of everything probed)

Every video probed with `--list-subs` and every one of the 10 downloaded samples exposes
**YouTube auto-generated captions only** (`en` + `en-orig` "English (Original)"), with
**no manual/human subtitle track anywhere** ("has no subtitles" on every probe).
Therefore `caption_type=asr` for the whole channel. This is the channel-wide observed
pattern (probed across a 2020→2026 spread + all 10 downloads); un-sampled rows inherit
`asr` on that basis, not per-video confirmation.

- **10 sample caption files downloaded** (`format=caption`), spread across bodies and
  years: PC 2020-04-22, Council 2020-07-07, PC 2021-03-10, PC 2021-12-08, Council
  2022-12-06, Council 2024-02-20, Council 2024-03-04, Council 2025-06-16, Council
  2026-07-07, PC 2026-07-08. Cleaned to `text/<date>.md` with the ASR header.
- The remaining 248 meetings are enumerated with `format=na` (caption exists on the
  source; not downloaded — this is a **sample-only** dataset by design, mirroring the
  other cities' transcripts builds). A full harvest is a deliberate follow-up, not a gap.
- **Corpus quality (10 samples):** `screen_corpus.py` clean — dict_ratio median 0.86
  (stable 0.85–0.87 across all years), no split-word / weird-char / duplicate-body /
  repeated-line outliers. ASR word errors are present and preserved verbatim (e.g.
  "Midbell"/"Midvil" for Midvale, "algiance" for allegiance) — an authenticity signal,
  never cleaned.

### yt-dlp caption-fetch quirk (operational note for a full harvest)
A minority of videos intermittently return `There are no subtitles for the requested
languages` via yt-dlp's default `android_vr` player client **even though `--list-subs`
lists `en`**; the `web`/`tv` clients instead flag some of those same videos `This video
is DRM protected`. This is a yt-dlp client-selection artifact, **not** a genuine caption
absence (e.g. 2024-12-03 `xVzgBtfHt7o`, 2024-01-16 `qDvSYqwvY88`, 2024-07-16
`4kIh3a8jB-E` hit this during sampling). A full harvest should iterate player clients
(`--extractor-args youtube:player_client=...`) and/or retry to recover these; captions
are present for essentially the whole channel.

## Whisper candidates (PROPOSE ONLY — not run)

All meetings already carry ASR captions, so Whisper is **not needed for coverage**; it
would only be an accuracy upgrade over YouTube ASR. If the user wants higher-fidelity
transcripts for the highest-value deliberations, reasonable candidates (all have video;
none is currently caption-*missing*):

1. **Contested rezone / land-use council meetings** — where the clerk's named roll call
   is terse but the deliberation is substantive (join `db/v_contested` to pick dates).
2. **Budget retreat / Annual Legislative Meeting** (e.g. 2021-01-13) — policy-setting
   sessions the minutes summarize heavily.
3. **The handful of videos that resist yt-dlp caption fetch** (the DRM/no-subs quirk
   above) — Whisper on the audio is the clean fallback if client-iteration fails.

Do **not** run Whisper by default — it is expensive and the user decides.

## What was checked
- Official YouTube channel enumeration (`/streams` 268 + `/videos` 11) — done.
- Utah Record - Public Meetings mirror (`UC5hXeD66VUV_w655ionxaSA`) — no Midvale — done.
- `--list-subs` caption probes across 2020→2026 + 10 full downloads — asr-only — done.
- Granicus/Vimeo self-hosted video — none (Revize site embeds YouTube) — done.
