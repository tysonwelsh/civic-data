# summit_county / land_use — how to use this module

Summit County's **two Planning Commissions** as a searchable minutes corpus + extracted
votes, for Snyderville-Basin growth/housing/development research. This is the **LAND_USE**
module of the `summit_county/` entity (MID-tier build; land use is the funded core here —
Snyderville Basin development pressure is the repo's dead-center research subject).

## The two commissions (distinguish via the `body` / `body_slug` column)

| `body_slug` | Body | Meets | Jurisdiction |
|---|---|---|---|
| `snyderville_basin_pc` | Snyderville Basin Planning Commission | 2nd/4th Tuesday, Sheldon Richins Bldg, Park City | Snyderville Basin planning district (west county — Kimball Jct, Silver Summit, Summit Park, Trailside, Silver Creek) |
| `eastern_summit_pc` | Eastern Summit County Planning Commission | 1st/3rd Thursday, Coalville | Eastern Summit County (Coalville, Henefer, Oakley/Weber-canyon rural + AG lands) |

Both are volunteer land-use **recommending bodies** — most actions are a *positive/negative
recommendation to the County Council or the Community Development Director*, or a direct
approval (CUP / plat amendment / low-impact permit) they hold final authority over.

## What's here
- `minutes/<year>/<date>_<body_slug>.md` — 393 meeting minutes (markdown + provenance
  front-matter). Filename slug disambiguates the two PCs.
- `raw/<date>_<body_slug>_{granicus.html|agendacenter.pdf}` — the born-digital source
  (Granicus MinutesViewer HTML, or AgendaCenter minutes PDF). **20 oversize (>10MB) raws
  were NOT stored** (link-not-mirror; re-fetch from the md's `source_url`).
- `minutes_index.csv` — one row per meeting: `date, body, body_slug, md_path, source_url,
  provenance, minutes_status, text_chars, note`.
- `all_votes.csv` — one row per **named** voter position (see ceiling below).
- `motions_tally.csv` — one row per **motion** (all 1,566; was 1,571 before the 2026-07-31
  duplicate-ingest removal below), with tally counts + mover/seconder.
- `build_votes.py` — regenerates both vote CSVs from the minutes markdown (idempotent).

## Sources & the 2024 portal-migration seam
Minutes come from **two portals**, spliced by date (see SOURCES.md):
- **AgendaCenter** (CivicEngage; `summitcountyutah.gov/AgendaCenter/Search?CIDs=5` Snyderville /
  `CIDs=6` Eastern) — the pre-migration archive, **2015-2023**. `provenance=agendacenter`.
- **Granicus** (`summitcounty.granicus.com`, MinutesViewer HTML) — the post-**May-15-2024**
  "Meetings and Minutes" portal. Snyderville **2022-11+**, Eastern **2023-03+**.
  `provenance=granicus`. Richer (agenda-item attachments listed inline; feeds `packets/`).
- Where a meeting exists in both, **Granicus is preferred** (structured HTML). Utah Public
  Notice (PMN, body 1503 "Summit County Community Development") also carries these minutes
  and is the channel for the residual gaps below (PMN's search backend was erroring at build
  time — logged as a future backfill).

## Vote recording ceiling (re-verified 2026-07-25 — see the correction below)

> **⚠ CORRECTED 2026-07-25** (`_audits/2026-07-25/report.md` F2 →
> `_audits/2026-07-25/remediation.md`). The previous text called the un-named ayes an
> unliftable source ceiling. Two qualifications now apply:
> 1. **`build_votes.py` was under-reading the PUBLISHED text.** Two rounds of repair:
>    **v3** added four unparsed divided-vote grammars (leading "Opposed were X, Y",
>    trailing "…objected."/bare "…against.", dotted-leader wraps, the 2020 two-column poll
>    grid). **v4** then replaced verb-anchored segmentation with **marker-anchored pairing**,
>    so every printed outcome gets its own item instead of being inherited by whichever item
>    the verb regex happened to find. Combined: **motions 1,526 → 1,571, named vote rows
>    409 → 496**, and meetings where tallied motions equal printed tally lines went
>    **89% → 99%** (AgendaCenter era 82% → 99%). Also fixed on the way: tab-separated OCR
>    files (one meeting went from **0 motions to 6**), U+2010 hyphens in `(7‐0)` tallies,
>    a poll-grid name pattern that swallowed 4 of 7 voters, and 24 of 26 `which was`
>    motion-text fragments.
> 2. **The Granicus HTML carries an unrendered `<!-- AYES:/NOES:/ABSENTS: -->` block**
>    (545 of them; 520/520 agree exactly with the published tally). It is **deliberately
>    NOT ingested** — owner ruling 2026-07-25 — because it is unpublished and adds **zero**
>    dissent attribution: all 25 divided motions already name their dissenter in the
>    rendered text. Do not "recover" it without a fresh ruling.

**Semi-to-fully-named tally.** Every motion names its **mover + seconder**. For the vote:
- **Unanimous motions** print a tally only — `"all voted in favor, (6-0)"` (modern) /
  `"MOTION CARRIED (5-0)"` (older). The aye voters are **NOT individually named** — this is
  a source ceiling, not a gap. Such motions are `names_recorded=false`, tally-only.
- **Divided motions DO name voters.** Modern (Granicus era): a full roll — `"Tyann Mooney
  voted AYE … John Kucera voted NAY"`. Older (AgendaCenter era): dissenters only —
  `"MOTION CARRIED (5-2) Commissioner Clyde and Commissioner Hanson opposed."`
  **Abstentions are named in both eras** (`"Commissioner X abstained"`).
- So `all_votes.csv` holds the **contested signal**: **496 named rows** (v4, 2026-07-25; was 409). Absent members are attendance, not votes, and are not rowed. The `(N-M)`
  tally in `motions_tally.csv` is the authoritative count; named rows are attribution — on a
  handful of large divided rolls one aye/nay is un-named (tally > named), which is honest.
  **Gate:** no motion's named Ayes/Nays exceed its own tally (0 violations), and every
  `member` value is name-shaped (0 fragments).

## Coverage (built 2026-07-20)

| Body | Minutes docs | Range | Cancelled (Granicus era) |
|---|---|---|---|
| Snyderville Basin PC | 203 | 2015-01-13 … 2026-05-26 | 13 |
| Eastern Summit County PC | 190 | 2015-01-08 … 2026-06-18 | 28 total |

Per-year minutes: Snyderville 2015=20,16=17,17=25,18=17,19=15,20=17,**21=4**,22=20,23=19,
24=20,25=19,26=10; Eastern 2015=23,16=17,17=18,18=18,19=16,20=14,21=17,**22=5**,23=18,24=17,
25=17,26=10.
(Counts are `minutes_index.csv` ROWS, i.e. meeting records. **Eastern 2022's 5 rows now carry
only 4 usable texts** — 2022-08-04 became `minutes_exist_text_unrecovered` on 2026-07-31; see
the duplicate-ingest gap below. Motions total **1,566** across **378 text-bearing meetings**.)

## Honest gaps (never fabricate to fill these)
- **19 motions carry a BLANK motion text** (v4) — items the clerk recorded a vote for but
  never phrased as a motion. The vote, tally and outcome are faithful; the text is honestly
  blank rather than invented.
- **140 motions carry a BLANK result** — the clerk printed no outcome for them. v2 filled
  these by taking the first Pass keyword anywhere in a segment that can run 40k chars, so a
  motion could inherit a later motion's outcome. Result and tally are now bound to the
  motion's own outcome line; where none was printed, the blank is the datum.
- Two prior attributions were REMOVED as impossible (2015-12-03 m6, 2015-12-17 m6 carried
  2 Nay rows against their own `(7-0)` tally).
- **`2017-09-12` is the one meeting failing the count check, and the extractor is right** —
  its tally is `(4-1-1)`, which the verification regex can't parse.
- **Snyderville 2021 (only 4 of ~20)** and **Eastern 2022 (only 5 of ~17)** — genuine
  portal gaps: AgendaCenter posted only these, and Granicus's archive begins after them.
  PMN body 1503 is the likely recovery channel (future backfill — see SOURCES.md).
- **14 image-only minutes** (`note` contains `needs_ocr_image_only`, `minutes_status=
  minutes_exist_text_unrecovered`) — mostly 2022 Snyderville minutes that AgendaCenter
  stored as scanned/oversize image PDFs (some were actually full packets in the Minutes
  slot). The meeting record exists; the *text* is unrecovered pending OCR. Not fabricated.
  (**15 `minutes_exist_text_unrecovered` rows total** since 2026-07-31 — the 14 image-only
  plus the 2022-08-04 wrong-file row below.)
- **`2022-08-04` Eastern PC — WRONG FILE PUBLISHED AT SOURCE, phantom meeting removed
  2026-07-31** (duplicate-ingest wave g8). The AgendaCenter Minutes slot for that meeting
  (`_08042022-3540`) does not hold the Aug 4 minutes: it serves the **June 16, 2022** ESPC
  minutes PDF (title block "THURSDAY, JUNE 16, 2022"; all 17 running headers read
  "June 16, 2022 / Page N of 17"), with one extra appended public-comment letter that the
  `_06162022-3476` copy lacks. Re-fetched live 2026-07-31 — byte-identical (521,863 B) to the
  stored raw, so this is a **county mis-upload, not an ingest or date-parse bug**; there is no
  fetch-script fix to make. The 5 motions carved from it were the 2022-06-16 motions
  double-counted and have been removed (motions 1,571 → 1,566; meetings 379 → 378;
  applications 576 → 575; **0 named vote rows affected** — both copies were tally-only).
  Because the county DID post an agenda for a non-cancelled Aug 4, 2022 ESPC meeting, the
  meeting is **real** and its minutes text is an honest gap, logged as
  `minutes_exist_text_unrecovered` rather than deleted. Recovery channel: PMN body 1503.
  The raw PDF is retained under the 08-04 name as evidence of the mis-upload — **never
  re-ingest it under this date.**
- **20 oversize (>10MB) raws not stored** — re-fetch from `source_url` (link-not-mirror).
- **Newest 1-2 held meetings lag** — minutes post only after the *next* meeting approves
  them, so the most recent held meeting may have no approved minutes yet.
- **Cancelled meetings** (13 Snyderville + 15 Eastern, Granicus era) are real "no meeting"
  records, omitted from the index by definition.

## Cardinal rules (repo-wide)
- Never fabricate minutes text, votes, or dates. Tally-only = the source named no individual
  ayes; that blank is the datum. A mislabeled doc is read from its body (the DOCX-as-`.pdf`
  2016-10-25 file, the image "minutes" that are packets).
- `raw/` + minutes markdown are canonical; `all_votes.csv`/`motions_tally.csv` are
  regenerated (`python3 build_votes.py`), never hand-edited.
