# Agenda Packets — Availability & Coverage (INDEX-ONLY)

**Dataset:** `packets/` — the agenda **packets** (agenda + staff reports + ordinance drafts
+ attachments) behind South Salt Lake **City Council**, **Planning Commission (PC)**,
**Redevelopment Agency (RDA)**, and **Civilian Review Board (CRB)** agenda items.
**As-of:** 2026-07-13. **Portal:** CivicPlus / CivicEngage Central AgendaCenter
(`https://sslc.gov/AgendaCenter`).

## What this dataset is (and the structural finding that makes it the high-value SSL source)
On SSL's AgendaCenter **both the "Agenda" and the "Minutes" slots serve the AGENDA PACKET**,
**not** the recorded roll-call minutes — verified in recon across 2023–2026. (The recorded,
named-per-member minutes live on **Utah Public Notice (PMN)** bodies 1295/1296/1297 and are
handled by the core repo's `meeting_minutes/` + `planning_commission/` layers.) The core
build deliberately did **not** retain these packets ("a future `packets/` layer") — so
harvesting them **is** this dataset. The packets carry the *staff analysis* (fiscal notes,
zoning analysis, alternatives, recommendation) that explains **why** items passed.

**Full-packet endpoint:** the assembled packet is served at
`…/AgendaCenter/ViewFile/Agenda/_MMDDYYYY-<id>?packet=true`. This is the correct `source_url`
for every row: it equals the plain Agenda file when that upload already *is* the whole packet,
and is strictly the full assembled packet (agenda + all attached staff reports) when the plain
slot is only a thin agenda outline (verified: PC 2022-01-20 plain 2.9 KB vs `?packet=true`
4.1 MB). Two ids on one Council date = the 6:30 pm **Work** meeting + the 7:00 pm **Regular**
meeting; the same-day RDA (6:15 pm) is a separate `cat5` item.

## Mode decision — INDEX-ONLY (no PDFs on disk), + a 2026-07-17 targeted TEXT fetch
A **link index of 429 packets**, not a store of PDFs. Each row carries a live `source_url`
(`?packet=true`), its HEAD-probed `content_length_bytes`/`size_mb`, and `stored_locally=no`.
For the **357 non-fetched rows**: `format=na`,
`extraction_method="not_retrieved (index-only; fetch source_url on demand)"`, and the pilot
columns (below) are blank.

**Targeted TEXT fetch — 72 high-value packets (2026-07-17).** Under the sanctioned
"fetch → hash → extract → DISCARD binary" exception (SCHEMA_SPEC §9 primary-document text
layer), the 72 highest-value packets were fetched, `pdftotext -layout`-extracted to searchable
sidecars, and the binaries discarded (text-only corpus; public + re-fetchable via `source_url`).
See "Targeted fetch of the cliff/high-value subset" below. The other 357 stay honestly
index-only.

**Size math (drives the decision):** all 429 packets were HEAD-probed for `Content-Length`
on 2026-07-13 (`raw/_fetch_log.jsonl`). **Total = 3.37 GB** (min 0.00 MB, median 0.65 MB,
max **248.5 MB**; **15 packets > 50 MB, 4 > 100 MB**). This exceeds the ~1.5 GB disk budget,
and PC packets in particular are bulky image/map/plat-heavy PDFs (not text-convertible —
vision/OCR only), so by the documented §1 allowed exception the PDFs are **not retained
locally**; any packet can be re-fetched on demand from its `source_url` (public GET,
re-fetchable). Provenance of the discovery/size probe is in `raw/_fetch_log.jsonl` and the
listing HTML in `raw/_listings/`.

All 429 `?packet=true` `source_url`s returned **HTTP 200** during the size sweep.

## Coverage (what exists)
| Body | Category | Years with packets | Packets indexed | (of which cancelled/notice) |
|---|---|---|---|---|
| City Council | cat4 | 2022, 2023, 2024, 2025, 2026 | 197 | 6 |
| Planning Commission | cat3 | 2022, 2023, 2024, 2025, 2026 | 116 | 29 |
| Redevelopment Agency (RDA) | cat5 | 2020, 2021, 2022, 2023, 2024, 2025, 2026 | 50 | 0 |
| Civilian Review Board (CRB) | cat2 | 2022, 2023, 2024, 2025, 2026 | 66 | 1 |
| **Total** | | | **429** | **36** |

- Per-body meeting-type split across the set: 319 regular, 102 work, 8 special.
- `body` is classified from the AgendaCenter category (cat4/3/5/2 → Council/PC/RDA/CRB).
- `meeting_type` (regular/work/special) is parsed from the item title; `cancelled=yes`
  flags meetings the city posted then cancelled (kept as honest rows — a cancelled-meeting
  notice is a real posted document, often a small stub agenda; not fabricated).

## What was checked / what's absent (gaps are data)
- **Council & PC & CRB packets before 2022:** not on the AgendaCenter — the portal's earliest
  Council/PC/CRB listings are 2022 (queried `UpdateCategoryList?catID={4,3,2}&year={2020,2021}`
  → 0 items). **RDA** is the only body that reaches back to **2020** on the portal (2020/2021 =
  4 items each). This is a city publishing/portal-retention boundary, not a scraper miss.
- **Council 2020–2021** packets specifically: absent (AgendaCenter Council era starts 2022);
  those meetings' recorded minutes are on PMN (core repo), but the *agenda packets* were never
  posted to the AgendaCenter and are not recoverable there.
- No packet PDF is stored on disk; nothing was OCR'd/extracted (index-only). `format=na`,
  `extraction_method=not_retrieved` for all 429 rows. Text sidecars (`packets/text/`) are
  therefore **not** produced — they are mandatory only for *stored born-digital* packets.
- The 2 exactly-0.00-MB rows (CRB 2022-12-05, PC 2023-02-02 cancelled) are genuine tiny
  posted stubs, retained honestly.

## To retrieve content
Fetch a row's `source_url` (public GET; use vision/OCR for the image/map-heavy PC packets):
```
python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py \
    --out raw/<date> "<source_url>"
python3 ../../scripts/extract_packet_text.py south_salt_lake   # after any local retrieval
```
To re-hydrate the whole set, `polite_fetch.py --batch` over the `source_url` column, **uncapped**
(~3.37 GB). If retrieving, flip that row's `stored_locally`→`yes`, set `path=raw/<date>/<file>`,
`format=text|scanned`, and the real `extraction_method`.

## Primary-document classes (doc_class rollout, 2026-07-16)

**Ruling: honest no for the row-level classes — with a future targeted-fetch note.** Under
the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`, triage 2026-07-16)
South Salt Lake was bucketed **B-no**. All **429 packets are INDEX-ONLY assembled
`?packet=true` bundles** (3.37 GB) with **no per-attachment rows or matter metadata**, so
the four attachment-borne classes — `staff_report`, `member_memo`, `plan_amendment`,
`development_agreement` — are **not separable** here. Nothing was fetched, classified, or
section-cut in this documentation-only pass; no `doc_class`/`text_path` column is added.

**Noted for the future (NOT done this rollout):** these packets are SSL's **only
staff-analysis record** for the dates the recorded-minutes coverage cliff left uncovered
(see `../COVERAGE.md`), and the born-digital council packets are **small-median**
(overall median 0.65 MB) — so a **targeted fetch of the cliff-date council packets** is a
reasonable future candidate should staff-analysis text be wanted for those meetings. That
is a deliberate follow-up, not part of this documentation-only ruling. Class 3
(`general_plan`) is handled in `housing_plans/`.

## Targeted fetch of the cliff/high-value subset (2026-07-17)

The future-fetch candidate above was **executed for a bounded 72-packet subset** — the
highest-value staff-analysis records: packets tied to **contested votes** and **land-use
items**. The subset was derived from `db/civic.db` (read-only): every 2022+ meeting with a
`v_contested` motion (any Nay/Abstain/Recuse) plus every Council/PC meeting with a rezone /
zoning / CUP / subdivision / plat / general-plan / development-agreement / annexation /
density / Title-17 motion. Those date/body pairs were joined to this index's `?packet=true`
rows, capped at **≤35 MB/item** (skips the image/plat-heavy 50–250 MB PC monsters, low
text-yield), and bounded to **72 packets** (contested 40 + land-use Council 5 + land-use PC
27; **Council 28 / PC 39 / RDA 5**, 633 MB fetched). All 72 returned HTTP 200
`application/pdf`.

**Result:** all 72 are **born-digital** (`pdftotext -layout` yielded a median ~62,800 real
chars; 0 needed OCR). Each fetched row now carries the standardized pilot trailing columns:
- `format=text`, `extraction_method=pdftotext -layout`, `retrieved_date=2026-07-17`.
- `fetch_status=ok`, `sha256` (of the discarded binary), `text_path=text/<slug>.txt`,
  `text_chars`.
- `path` stays blank and `stored_locally=no` — **the binary was discarded** per the sanctioned
  exception; the searchable artifact is the `text/` sidecar; the GET provenance (url, status,
  bytes, sha256, retrieved_utc per file) is retained at `raw/_targeted_fetch_log.jsonl`.

**`doc_class` is deliberately BLANK on all 72 (honest "not separable").** These are
`packet_kind=full_packet` **assembled bundles** — one PDF interleaving the agenda + every
staff report + exhibits — so no single primary-document class (`staff_report` / `member_memo`
/ `plan_amendment` / `development_agreement`) describes the whole row at the required ≥95%
precision, and SSL packets carry no machine-readable TOC/template anchor to section-cut on
(the SCHEMA_SPEC §9 section-cut prerequisite). Blank is the sanctioned honest default; the
delivered value is the **searchable staff-analysis text** for these cliff/high-value dates
(federates via `fts_packet` on `text_path`), not a class label. Section-cutting these bundles
remains available future work if per-attachment classes are wanted.
