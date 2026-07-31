# Agenda Packets / Staff Reports — Availability & Coverage (STORED) — as-of 2026-07-13

**Dataset:** `packets/` — the agenda packets / staff-report bundles behind White City
**Council** (and the handful of **Planning Commission**) agenda items. Each packet is the
single bundled whole-meeting PDF (agenda + staff reports + resolutions/ordinances + exhibits)
that the city posts alongside the Agenda, Minutes, and audio for each meeting.
**Entity:** White City, Salt Lake County (~5,000 pop.) — **White City Metro Township
2017–2024 → CITY 2024-05-01 (HB35)**. Both eras are covered; `era` column marks each row.

## Portal — Streamline CMS (single site, per-year document lists)
- **Host:** `https://whitecity.utah.gov` (Streamline / getstreamline.com; PDFs on a
  Cloudfront CDN at `/files/<hex-hash>/<name>.pdf`). Browser User-Agent required.
- **Harvest source pages** (saved verbatim under `packets/html/` with their own
  `_fetch_log.jsonl`):
  - `/council-meeting?year=YYYY` for **2022–2026** — anchors carry an aria-label
    `"<file> attachment for <ISO-date> Council Meeting <full title>"` (gives the exact
    meeting date + body).
  - `/meetings-archive` for the **2019–2021** packets — anchors carry NO aria-label; the
    date lives in the inner span text (e.g. "Council Meeting Packet 1.7.2021").
  - The `?year=2017…2021` pages return a default listing with **no attachment data** — the
    archive page is authoritative for the pre-2022 packets.
- **Hashes are opaque — never guessed.** Every packet URL was taken from a labeled `<a href>`
  anchor on those pages (parser: `build_packets_index_wc.py`).

## Mode decision: STORED (not index-only)
The full candidate set of **99 packet PDFs HEAD-sized to 601 MB** (largest single packet
68 MB) — far under the ~1.5 GB disk budget — so **every packet is retained on disk** in
`raw/<date>/` verbatim, with each date folder's `_fetch_log.jsonl` as byte-level provenance
(url, http status, bytes, sha256, retrieved_utc). All 99 are **born-digital** and yielded a
`text/<stem>.txt` sidecar (`extract_packet_text.py`, `pdftotext -layout`, all ≥200 chars real
text) — **zero image-only packets**, even the 60–68 MB ones (they embed plats/site-plans as
vector/text, not scans). The sidecars feed `cities.db` `fts_packet` on the next
`build_cities_db.py` run (not run here — orchestrator owns that).

## Coverage (what exists)

| Body | Packets | Meeting dates | Date range |
|---|---|---|---|
| **Council** | 92 | 91 | 2018-02-01 → 2026-07-02 |
| **Planning Commission** | 7 | 7 | 2019-11-04 → 2025-06-24 |
| **Total** | **99** | | 2018-02-01 → 2026-07-02 |

Per-year (Council packets vs. audited council minutes, ±4-day match):

| Year | Council minutes | Council packets | minutes w/ packet | minutes w/o packet |
|---|---|---|---|---|
| 2018 | 12 | 1 | 0 | 12 |
| 2019 | 14 | 2 | 2 | 12 |
| 2020 | 13 | 11 | 11 | 2 |
| 2021 | 13 | 13 | 13 | 0 |
| 2022 | 16 | 13 | 13 | 3 |
| 2023 | 15 | 16 | 13 | 2 |
| 2024 | 14 | 14 | 14 | 0 |
| 2025 | 14 | 14 | 14 | 0 |
| 2026 | 6 | 7 | 5 | 1 |

By era: **66 metro-township** (before 2024-05-01) + **33 city**. By meeting type: 83 Regular,
15 Special, 1 Canvass (Board of Canvassers, 2019).

## ⚠ Structural gap: packet publishing effectively begins late 2019
White City posted **essentially no meeting packets in 2018 and Jan–Oct 2019** — a single lone
"agenda and information packet" survives for **2018-02-01**, then the packet series proper
starts **2019-11-04**. So **2018 and most of 2019 have audited minutes but no published
packet** — a genuine city-practice gap (the metro township did not bundle/post packets in its
first years), **not** a scraper miss. From **2020 onward packet coverage is near-complete**
(matched to the audited council minutes above).

## ⚠ Meetings with an agenda/minutes but no packet (2020+) — genuine gaps
Eight council meetings 2020+ have audited minutes but no packet posted, almost all
**special / adjourned / workshop** sessions (short-agenda meetings the city does not always
bundle a packet for):
`2020-01-02, 2020-08-13, 2022-03-31, 2022-10-13, 2022-12-29, 2023-01-26,
2023-06-22, 2026-02-27` (2026-02-27 is labeled "Special Meeting"). Recent meetings
(2026-06-04, 2026-07-02) have packets posted but approved minutes not yet published — normal
publishing lag, not a gap.

## ⚠ Planning Commission — 7 packets, a BONUS layer (the repo's PC dataset is honestly empty)
White City has its own Planning Commission (4th-Thursday) but **publishes no clean PC minutes
series** — the repo's `planning_commission/` is honestly empty by design. These 7 PC **packets**
(scattered across the same council year-pages + archive) are therefore the **only structured PC
source documents in the repo**: 2019-11-04, 2021-05-25, 2021-08-26, 2021-09-07 (special),
2023-04-27, 2025-04-22, 2025-06-24. They are `body=PlanningCommission` in the index; PC coverage
is sparse and non-systematic (the city does not post most PC packets).

## What was checked
- All per-year council pages 2017–2026 + `/meetings-archive` + the current-year landing page,
  fetched 2026-07-13 (`packets/html/`). Every labeled Packet anchor was harvested; Agenda,
  Minutes(+APPROVED), and audio-MP3 anchors were deliberately excluded (those belong to the
  `meeting_minutes/` dataset / are not packets).
- No PMN crawl was needed — the Streamline site exposed the full packet set directly. PMN
  (council body 5805) remains the documented fallback if a future refresh finds a year page
  blocked.

## Honesty notes
- **Never fabricated.** A missing packet = the city didn't post one (recorded above), never a
  guessed URL. Streamline hashes were only ever taken from live anchors.
- Raw PDFs and `_fetch_log.jsonl` files are retained under `raw/<date>/` and are never deleted
  or normalized. Corpus screen (`screen_corpus.py`): no dict-ratio / split-word / read-error
  outliers; 8 files flagged `weird_char` (max 4%) are packets embedding plats/budget tables —
  expected, not corruption.

## Primary-document classes (doc_class rollout, 2026-07-16)

Assessed as part of the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
Source-7 doc_class taxonomy: staff_report / exhibit / presentation / correspondence / GP text).
**Ruling: not separable / low content — honest ~zero for the four classes.** The 99 STORED
`full_packet` bundles have **weak class anchors** and **thin formal staff-report content**
(White City council packets skew agenda / consent / fee-schedule material rather than land-use
staff analysis). No per-class `packet_section` rows were created. The 99 born-digital
full-packet text sidecars (`text/`) already serve `cities.db fts_packet`, so what packet text
exists is fully searchable at the whole-meeting granularity. Classes were assessed, not
forgotten.
