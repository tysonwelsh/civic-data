# Meeting video transcripts — availability

**As-of:** 2026-07-06 · **Source type #5 (meeting video transcripts)** · **SAMPLE-ONLY by owner policy.**

## Headline finding: South Jordan does NOT publish council/PC meeting *video* on YouTube

South Jordan City records its public meetings as **audio only**, posted on the city site
(`https://www.sjc.utah.gov/483/City-Council-Meeting-Audio`), plus born-digital **minutes**
PDFs. There is **no YouTube meeting-video source** and therefore **no ASR caption track for
any council or Planning Commission meeting**. This is a genuine publishing gap, not a
scraper miss.

### What was checked
| Source | Result |
|---|---|
| Official YouTube channel **"City of South Jordan"** (`UCvt-dQqGhbNgvPFomcQBFQw`) | Exists. **134 videos, all promotional/PR** (Summerfest, City Jobs, State of the City, PSAs, tax-education explainers). **Zero full council/PC meeting recordings.** Only civic-adjacent items: "Mayor and City Council Oath of Office 2026", the annual "State of the City" addresses, and a 2015 "Community Roundtable — City Manager". |
| Channel `/streams` tab | 1 entry (a memorial service livestream) — no meetings. |
| Channel `/playlists` (14 playlists) | All topical PR (Dine with Dawn, SoJo News Now, Tax Education 101, City Jobs, …). No "Council Meetings" / "Planning Commission" playlist. |
| Web-search playlists that name South Jordan | Belong to third parties (ABC4 real-estate listings; relocation vloggers) — not city meetings. |
| Web search for full meeting video / livestream | Only audio + minutes surfaced; confirms audio-only cadence and Zoom (not YouTube) for electronic participation. |
| **OpenUtah mirror** `southjordan.openutah.org` | Exists — reports **91 meetings indexed, 60 transcribed** ("transcripts sourced from official city recordings", i.e. from the city **audio**). **Not harvested:** per the expand-city-sources rule, OpenUtah serves its verbatim transcript text client-side behind `robots.txt Disallow: /api/`, so it is a **metadata/summary source only under the polite-GET rule, not a bulk grab.** It is the single best *lead* for real meeting transcripts and is called out below. |

## What this dataset contains (sample-only)

A **full channel map** of all 134 videos (`index.csv`) + **10 retrieved sample ASR caption
tracks** (`raw/*.vtt` → cleaned `text/*.md`). The 10 samples deliberately favor the most
governance-adjacent PR videos (Oath of Office, Economic Development, General Plan explainer,
Property/Truth-in-Taxation education, City Manager roundtable, SoJo News Now). They are
**not meeting transcripts** — every retrieved and cleaned file is headed accordingly.

Caption inventory across the 134 mapped videos: **65 ASR-only, 19 manual, 41 none, 9
unavailable/removed.** `caption_type` is recorded per row; all non-sampled rows are
`stored_locally=no` (index-only, re-fetchable via `yt-dlp` from `source_url`).

## High-value UNtranscribed meetings (Whisper candidates — NOT run)

Because no meeting video exists on YouTube, the honest "high-value untranscribed" set is
**every council & Planning Commission meeting**, whose only recording is the city's posted
**audio** (2020→present). If the owner ever wants verbatim deliberation transcripts, the two
routes are:

1. **Reuse OpenUtah's existing 60 transcribed meetings** (already derived from city audio) —
   a metadata/attribution question, not a scrape (respect its `robots.txt`).
2. **Whisper over the city's posted meeting audio** (`/483/City-Council-Meeting-Audio`).
   Highest-value targets = contested / public-hearing meetings (rezones, budget/Truth-in-Taxation,
   the Rio Tinto Kennecott annexation) where minutes summarize away the deliberation.
   **Whisper was NOT run** (owner decides; expensive).

**No Whisper, no bulk harvest, no OpenUtah scrape were performed** — sample-only, by policy.
