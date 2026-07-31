# Agenda Packets — Availability & Coverage (INDEX-ONLY)

**Dataset:** `packets/` — agenda packets / staff-report bundles behind South Jordan **City
Council** and **Planning Commission** agenda items. **As-of:** 2026-07-06.
**Portal:** Municode Meetings (`southjordan-ut.municodemeetings.com`), documents on the
US-gov Azure blob store `mccmeetings.blob.core.usgovcloudapi.net/sojordanut-pubu/`.

## What this dataset is
A **link index of 169 packets**, not a store of PDFs. See `CLAUDE.md` for the design
rationale. Short version: each packet is one bundled **whole-meeting PDF** (agenda + all
staff reports + all exhibits), median **19.8 MB**, up to **195 MB**, heavy with
maps/plats/site plans (full set = **5.32 GB**). By owner decision (multi-GB, low
text-conversion value) the PDFs are **not retained locally** — `index.csv` holds a live
`source_url` + exact byte size for each so any packet can be fetched on demand.

## Coverage (what exists)
| Body | Years with packets | Packets indexed |
|---|---|---|
| City Council | 2022, 2023, 2024, 2025, 2026 | 87 |
| Planning Commission | 2022, 2023, 2024, 2025, 2026 | 82 |
| **Total** | **2022 – 2026** | **169** |

- Per body/year: Council 2022:19 · 2023:20 · 2024:18 · 2025:20 · 2026:10 (thru Jun).
  PC 2022:17 · 2023:18 · 2024:19 · 2025:20 · 2026:8 (thru May).
- Date span **2022-01-04 → 2026-06-16**.
- `size_mb`: min 0.42, median 19.78, max 195.53. 40 packets >50 MB, 7 >100 MB.
- All 169 `source_url`s verified **HTTP 200** on 2026-07-06 (HEAD probe; `raw/_fetch_log.jsonl`).

## Join to votes (`date` + `body` [+ `meeting_type`])
- **Council:** 84 packet dates; 82 join to a `meeting_minutes/all_votes.csv` date.
  Of **100** council vote dates in 2022+, **82** have a packet (the ~18 without are study /
  special / budget sessions that carry no separate packet, packets attach to the paired
  regular meeting).
- **PC:** 82 packet dates; 80 join to a `planning_commission/all_votes.csv` date.
  **80 of 82** PC vote dates in 2022+ have a packet — near-complete.
- **2 council packet dates have no vote yet** (2026-06-02, 2026-06-16) and **2 PC dates**
  (2024-05-14, 2026-05-26): the packet layer runs slightly **ahead** of the minutes/votes
  layer (repo minutes stop 2026-05-19) — these are meetings not yet minuted, not errors.

## What was checked / what's absent (gaps are data)
- **2020–2021 packets: none for either body.** Municode's South Jordan document store
  begins in 2022; a `date_filter` query for 2020 and 2021 returns zero meetings for both
  City Council and Planning Commission. This is the city's Municode publication start, not a
  scraper miss. (2020–2021 council/PC **minutes** in this repo came from Utah PMN, which does
  not carry the packets.)
- **CivicPlus / CivicEngage AgendaCenter is NOT a packet source here.** The
  `sjc.utah.gov/AgendaCenter/ViewFile/Agenda/_<date>-<id>?packet=true` links exist but resolve
  to **empty 2,542-byte AcroForm stub PDFs** ("No Agenda. Packet") — the city does not publish
  real packets through CivicPlus. All genuine packets are on Municode. Verified 2026-07-06.
- Nothing is stored on disk; no packet was OCR'd/extracted (index-only). `format=na`,
  `stored_locally=no`, `extraction_method=not_retrieved` for all 169 rows.

## To retrieve content
Fetch a row's `source_url` (public GET). A packet is a bundled whole-meeting PDF: the
agenda + staff-report memos are **born-digital text** (`pdftotext -layout` works — a sampled
40-pp council packet yielded ~10k text chars in its first 5 pages), but the **exhibits
(maps, plats, site plans, engineering studies) are images** requiring vision/OCR. To
re-hydrate the whole set: `polite_fetch.py --batch <source_urls>` **uncapped** (~5.32 GB).
Provenance of the 2026-07-06 discovery/HEAD-probe is in `raw/_fetch_log.jsonl`.

## Primary-document classes (doc_class rollout, 2026-07-16)

**Ruling: honest no — classes not separable for this portal.** Under the repo-wide
primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`, triage 2026-07-16) South Jordan was
bucketed **B-no**. All **169 packets are INDEX-ONLY whole-meeting bundles** (5.32 GB,
median ~20 MB, up to 195 MB) with **generic meeting-level titles** and **no per-attachment
rows or matter metadata** to drive a classifier. Municode attaches exactly one "Agenda
Packet" per meeting; there are no separable per-item staff-report PDFs. The four
attachment-borne classes — `staff_report`, `member_memo`, `plan_amendment`,
`development_agreement` — therefore cannot be extracted without fetching and page-cutting
5.3 GB of monolithic PDFs, which is **out of scope for this rollout**: no fetch, no
classification, no section-cut, no `doc_class`/`text_path` column added. Class 3
(`general_plan`) is handled separately in `housing_plans/`. The `index.csv` link index
remains the honest record of what the city publishes.
