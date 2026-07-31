# White City — `packets/` dataset (build method, linkage, caveats)

Agenda packets / staff-report bundles behind White City **Council** (+ 7 **Planning
Commission**) agenda items, built by `/expand-city-sources` (source 1), 2026-07-13. Purely
additive — no existing dataset was modified. **STORED mode**: 99 packets, 601 MB, all on disk.

## What a "packet" is here
One **bundled whole-meeting PDF** per meeting (agenda + staff reports + draft
resolutions/ordinances + exhibits), posted by the city alongside the Agenda, Minutes, and
audio. `packet_kind` is `full_packet` for every row (White City does not unbundle into
per-item handouts the way Alta's older era did). This is the staff analysis that explains
*why* an item passed — join it to `meeting_minutes/all_votes.csv` by date.

## Source & harvest
- **Streamline CMS** at `https://whitecity.utah.gov`; PDFs on Cloudfront at
  `/files/<hex-hash>/<name>.pdf` (browser UA required; hashes opaque — **only harvested from
  live labeled anchors, never guessed**).
- Two page layouts, both parsed by **`build_packets_index_wc.py`** (in this dir):
  - `/council-meeting?year=YYYY` (2022–2026): anchors carry
    `aria-label="<file> attachment for <ISO-date> Council Meeting <title>"` → exact date + body.
  - `/meetings-archive` (2019–2021 packets): no aria-label; date parsed from the inner span
    text / filename. (`?year=2017…2021` pages return no attachment data — archive is
    authoritative pre-2022.)
- Source listing pages are retained verbatim under **`packets/html/`** (+ its `_fetch_log.jsonl`)
  as harvest provenance — the anchor set as it existed 2026-07-13.

## Build pipeline (reproduce)
1. `build_packets_index_wc.py` → parses `html/*.html` → `_candidates.csv`
   (date, body, meeting_type, packet_kind, title, filename, url). Classifies body by title
   ("planning commission" → PlanningCommission, else Council) and meeting_type
   (special/workshop/canvass/regular). Excludes Agenda/Minutes/MP3 anchors — packets only.
2. Sizing (`polite_fetch.py --size-only`, results in `_sizes.csv`): 601 MB total → **under the
   1.5 GB budget → STORED** (not index-only).
3. Fetch: `polite_fetch.py` per row into `raw/<date>/<filename>` (throttled GET, browser UA,
   Referer set; per-date `_fetch_log.jsonl` with sha256).
4. `python3 /Users/tysonwelsh/civic-data/scripts/extract_packet_text.py white_city` →
   `text/<stem>.txt` sidecars (`pdftotext -layout`, ≥200 chars). Log: `text/_extraction_log.csv`
   (all 99 = `extracted`).
5. `build_index_wc.py` → `index.csv` (reads `_candidates.csv` + on-disk sizes + the extraction
   log to set `format`/`extraction_method`). Re-run after any re-fetch; idempotent.

## `index.csv` schema
SCHEMA_SPEC §9 packets contract header (exact, in order) + 2 city extras:
```
date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path,era,bytes
```
- `path` is **dataset-relative including `raw/`** (e.g. `raw/2023-06-01/6-1-2023_wcmt_meeting_packet.pdf`).
- `format` = `text` for all 99 (born-digital); `extraction_method` = `pdftotext -layout`.
- **`era`** (extra): `metro_township` (date < 2024-05-01) | `city` (≥ 2024-05-01, HB35).
- **`bytes`** (extra): on-disk file size.

## Linkage
- **To votes/minutes:** join `date` + `body` to `meeting_minutes/all_votes.csv` /
  `minutes_index.csv`. All council votes in this repo are `body=Council`; the 7 PC packets have
  no minutes counterpart (repo `planning_commission/` is honestly empty — these packets are the
  only PC source docs; see AVAILABILITY.md).
- Packet-label dates occasionally differ from the minutes date by a day or two; use a ±3–4 day
  tolerance when joining special/adjourned meetings.

## Caveats (see AVAILABILITY.md for the full gap table)
- **Packet publishing begins late 2019** — 2018 + Jan–Oct 2019 have minutes but no packet
  (city practice, not a miss). 2020+ near-complete.
- **8 special/workshop council meetings 2020+ have no packet** (short-agenda sessions) — genuine
  agenda-without-packet gaps, listed in AVAILABILITY.md.
- **PC coverage is sparse/non-systematic** (7 packets 2019–2025) — the city posts most PC
  packets nowhere.
- Never fabricated: missing = not published; hashes only from live anchors.

## Regeneration
`python3 build_packets_index_wc.py && python3 build_index_wc.py` (after re-fetching raws with
`polite_fetch.py`). Raw PDFs, `_fetch_log.jsonl`, and `html/` are retained and never
hand-edited. `_candidates.csv` / `_sizes.csv` are build intermediates.

## Primary-document classes
Assessed 2026-07-16 (doc_class rollout) — **not applicable / not separable** for this Streamline
portal (weak anchors, thin formal staff-report content; honest ~zero for the four classes).
Full-packet text sidecars already serve FTS. See `AVAILABILITY.md` § "Primary-document classes
(doc_class rollout, 2026-07-16)".
