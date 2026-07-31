# Agenda Packets — Availability & Coverage (INDEX-ONLY)

**Dataset:** `packets/` — agenda packets / staff reports behind St. George **City Council** and
**Planning Commission** agenda items. **As-of:** 2026-07-02. **Portal:** Revize static CMS
(`sgcityutah.gov` → `cms3.revize.com`).

## What this dataset is
A **link index of 224 packets**, not a store of PDFs. See `CLAUDE.md` for the design rationale.
Short version: each packet is one bundled **10–150 MB image/map-heavy PDF** (full set = **7.5 GB**),
not text-convertible; by owner decision the PDFs are **not retained locally** — `index.csv` holds a
live `source_url` + byte size for each so any packet can be fetched on demand.

## Coverage (what exists)
| Body | Years with packets | Packets indexed |
|---|---|---|
| City Council | 2022, 2023, 2024, 2025 | 177 |
| Planning Commission | 2024, 2025 | 47 |
| **Total** | | **224** |

- All 224 `source_url`s verified **HTTP 200** on 2026-07-02 (`raw/_fetch_log.jsonl`).
- `size_mb` per row: min 0.4 MB, median 28.8 MB, max 151.4 MB. 55 packets >50 MB, 14 >100 MB.

## What was checked / what's absent (gaps are data)
- **PC packets before 2024:** none posted (checked the PC agendas/minutes page for 2020–2023 — links
  absent though PC *minutes* go back to 2020). City publishing gap, not a scraper miss.
- **Council packets before 2022:** not published on Revize (agendas/minutes page states pre-2022
  material is on the Utah Public Notice site; packets are not among it).
- **2020–2021** packets: not available (Revize packet era starts 2022).
- No packet PDF is stored on disk; nothing was OCR'd/extracted (index-only). `format=na`,
  `extraction_method=not_retrieved` for all rows.

## To retrieve content
Fetch a row's `source_url` (public GET; use vision/OCR — image-heavy). To re-hydrate all packets,
`polite_fetch.py --batch <source_urls>` **uncapped** (~7.5 GB). Provenance of the original
discovery/probe is in `raw/_fetch_log.jsonl`.

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket B-no** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) are **not separable** for this portal — an honest **no** for all
four. No fetch, no classification was performed.

Why not separable: the **224 index-only** packets are whole-meeting bundles totalling **7.5 GB**,
**image/plat-heavy** per the prior probes (vision/OCR-only — not born-digital text), and stored
nowhere on disk. With no text layer and no per-attachment metadata, class-labeled sections
cannot be cut at confidence. Class 3 (General Plan text) is handled independently under
`housing_plans/` (the St. George HTML→text sidecar work).
