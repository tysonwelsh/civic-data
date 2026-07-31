# Agenda Packets — Availability & Coverage (INDEX-ONLY)

**Dataset:** `packets/` — agenda packets / staff reports behind Midvale **City Council**
(incl. in-session **RDA**) and **Planning & Zoning Commission** agenda items.
**As-of:** 2026-07-13. **Portal:** Revize static CMS (`midvale.utah.gov` Document Center file
tree). Built by `expand-city-sources` (Source 1).

## What this dataset is
A **link index of 117 packets** (2020+), NOT a store of PDFs. See `CLAUDE.md` for the design
rationale. Short version: each packet is one bundled **whole-meeting PDF** (agenda + every staff
report + all exhibits), map/plat/site-plan heavy, **not born-digital text** (vision/OCR required
to read). `index.csv` holds a live `source_url` + byte size for each so any packet can be fetched
on demand.

## Mode decision — INDEX-ONLY (size math)
- 110 of 117 packet URLs resolved live (HEAD Content-Length probe, 2026-07-13).
- **Live set total = 2.78 GB** (min 0.34 MB · median 14.8 MB · max 171.0 MB; 18 packets >50 MB,
  2 >100 MB). The full published set (incl. the 7 dead links, ~median size each) would be ≈2.9 GB.
- **2.78 GB exceeds the ~1.5 GB disk budget** → **INDEX-ONLY** (the documented, allowed exception
  to "retain every raw original" for re-fetchable public bundles; skill §1 / SKILL "Revize/CivicPlus
  static-CMS" branch). PDFs are NOT stored; `format=na`, `extraction_method=not_retrieved`,
  `stored_locally=no`, `path` blank for every row. No text sidecars (nothing stored → nothing to
  extract). Retained raw provenance = the two scraped landing pages + `raw/_fetch_log.jsonl`.

## Coverage (what exists)
| Body | Years with packets | Packets indexed (live / dead-link) |
|---|---|---|
| City Council (incl. in-session RDA) | 2020, 2021, 2022, 2023, 2024, 2025, 2026 | **69** (67 / 2) |
| Planning & Zoning Commission | 2021, 2022, 2023, 2024, 2025, 2026 | **48** (43 / 5) |
| **Total** | | **117** (110 / 7) |

- **Council window:** 2020-10-20 → 2026-07-07. **PC window:** 2021-11-10 → 2026-07-08.
- Packet publication is **sparse before 2024** (Council 3/3/2/5 in 2020–2023; PC 0/1/3/2 in
  2020–2023) then dense (Council 21/22, PC 14/18 in 2024/2025). This is a **city publishing
  ramp**, not a scraper miss — the "Packets" column simply was not populated for most early
  meetings (minutes/agendas for those dates DO exist in `../meeting_minutes/` and
  `../planning_commission/`).
- **No council-vs-PC asymmetry in kind** — both bodies publish whole-meeting packets on the same
  Revize Document Center. The only asymmetry is the dead-link rate (below), which lands mostly on PC.

## Join to the vote/minutes layers
- Key on `(date, body)` (+ `meeting_type` for the one same-day duplicate).
- **Council** packet dates cover **57/66** distinct council vote dates; **PC** **41/43**.
  Non-matching packet dates are work/special/future meetings with no roll call (e.g. 2024 study
  sessions; the 2026-07 packets post-date the current minutes floor).
- **2025-08-19 carries TWO council packets** — the Regular meeting and a **Truth-in-Taxation**
  meeting (the documented same-day duplicate in the city's minutes layer). Distinguished by
  `meeting_type` (`regular` vs `truth_in_taxation`).

## What was checked / what's absent (gaps are data)
- **7 dead links (city 404s as-published).** These packet links appear on the city's own landing
  pages as **bare relative filenames** (a Revize `<base href>` quirk) that resolve to nothing; the
  intended `Document Center/.../<year>/Packets/` path also returns **HTTP 404** (verified by GET,
  2026-07-13). They are the city's broken links, not a harvest error, so they are catalogued with a
  best-inferred `source_url` and flagged `not_retrieved (dead link — city page 404s as-published)`,
  `content_length_bytes`/`size_mb` blank:
  - Council: 2023-04-18, 2022-11-15 (`Final CC Packet 11-15-2022`)
  - PC: 2026-06-10, 2026-03-25, 2025-04-23, 2024-12-04, 2024-10-23
- **Pre-2020** packets: out of scope (data floor 2020).
- **RDA has no separate packet stream** — Midvale's RDA is an in-session council body; its items
  ride inside the `CC Packet` for that date (body recorded as `Council`).
- All 110 live `source_url`s returned a positive HEAD Content-Length on 2026-07-13; the two landing
  pages' fetch provenance is in `raw/_fetch_log.jsonl`.

## To retrieve content
Fetch a live row's `source_url` (public GET) and read with **vision/OCR** (image/map-heavy — NOT
`pdftotext`). To re-hydrate the whole set: feed the `source_url` column to
`polite_fetch.py --batch` **uncapped** (~2.8 GB for all 110 live). Re-scrape:
`python3 build_packets_index_midvale.py && python3 probe_sizes_midvale.py && python3 write_index_midvale.py`.

## Primary-document classes (doc_class rollout, 2026-07-16)

Assessed as part of the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
Source-7 doc_class taxonomy: staff_report / exhibit / presentation / correspondence / GP text).
**Ruling: not separable — honest no.** The 117 `full_packet` rows are INDEX-ONLY (2.78 GB live,
not stored) and per prior probes are **image / map / plat-heavy — vision/OCR-only, not
born-digital text**, so there is no clean staff-report text layer to classify or section-cut
(and the 7 dead links are already recorded above). No fetch was done and no per-class
`packet_section` rows were created. Classes were assessed, not forgotten.
