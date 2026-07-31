# Agenda Packets — Availability & Coverage (INDEX-ONLY)

**Dataset:** `packets/` — agenda packets / staff reports behind Logan **City Council** (incl. RDA)
agenda items. **As-of:** 2026-07-05. **Portal:** Revize static CMS, no API
(`loganutah.gov` → `cms9files.revize.com`), one HTML listing page per year.

## What this dataset is
A **link index of 1,124 documents**, not a store of PDFs. Logan publishes each agenda item as its
own PDF, so a row = one document (agenda / ordinance / resolution / memo / notice), each with a live
`source_url` + byte size. See `CLAUDE.md` for the design rationale and how to fetch/read a document.

## Storage decision + size math (why index-only)
- Logan does NOT bundle meetings; it posts many small-to-medium per-item PDFs.
- HEAD size-probe of **all 1,124** documents on 2026-07-05: mean per document = **1.40 MB**, max
  **31.3 MB** (image/plat-heavy staff exhibits); measured full-set total = **1.56 GB**.
- **1.56 GB** is nearly 4× the repo's ~400 MB local-store budget. Therefore **INDEX-ONLY**:
  `format=na`, `stored_locally=no`, `path` empty; the row carries `source_url` + `size_mb`. Nothing
  is silently capped or dropped — every discovered in-window document is indexed. Per-row sizes come
  from `raw/_size_probe.jsonl` (`size_mb` populated for 1,121 of 1,124 rows; blank on 3 = the server
  returned no Content-Length on the probe; the URL is still live).

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, added 2026-07-16)

The 867 `staff_report` pointers were classified (title-only — Logan has no matter metadata) into
land-use-primary classes and those classes' TEXT extracted (fetch → `pdftotext -layout` → sha256 →
**discard binary**). This is the one true Sandy-shaped fetch job in the rollout; the binary discard
is the sanctioned §9 packets exception (`sha256` + `source_url` + `text/_fetch_log.jsonl` are the
durable provenance).

Table below shows the state **after the 2026-07-17 vision pass** (needs_ocr → 0); the parenthetical
`ok` split records how each row got its text.

| doc_class | rows | ok (text kept) | needs_ocr | 404 | errors |
|---|---|---|---|---|---|
| staff_report | 207 | 207 (42 pdftotext + 165 vision) | 0 | 0 | 0 |
| plan_amendment | 6 | 6 | 0 | 0 | 0 |
| development_agreement | 0 | — | — | — | — (honest empty — no DA/MDA rides the corpus) |
| member_memo | 0 | — | — | — | — (honest empty — no member-authored memos published) |
| **classified total** | **213** | **213** (48 pdftotext + 165 vision) | **0** | **0** | **0** |

- **0 rows left with a blank `fetch_status`** — every classified pointer was attempted.
- **needs_ocr = 0 / 213 (was 165 / 213, 77 %) — closed by the 2026-07-17 vision pass.** Logan's
  land-use exhibits are image-heavy plats / site plans / engineering drawings; the 165 rows that had
  no pdftotext layer were transcribed via a **Read-tool vision pass at 150 dpi over sha256-verified
  re-fetches** (157 unique docs, ~2,900 pages), flipped to `fetch_status='ok'` /
  `extraction_method='claude_vision'`, with imagery pages carrying honest inline markers
  (`[map/plat page N — no text]`, `[part K/M — PDF pages X–Y]` at merge seams). The other 48 `ok`
  rows are the born-digital ordinance/resolution bodies and staff memos (`pdftotext -layout`).

### Disk ledger (fetch → extract → discard)
- **Binary downloaded then DISCARDED:** 818.3 MB across 199 unique-URL fetches (14 additional
  classified rows are byte-identical-URL dedups, resolved from the `seen` map without re-fetching).
- **Text kept on disk:** originally 42 unique pdftotext sidecars (2.69 MB); after the 2026-07-17
  vision pass, **199 unique sidecars, 8.05 MB** under `text/attachments/` (42 pdftotext + 157 vision;
  the 213 ok rows sharing URLs collapse to 199 files). Vision sidecars alone are 5.36 MB.
- **Fetch politeness:** GET-only, ≥1.0 s/host, browser UA, 404/429/503 honored (no retry loops);
  provenance in `text/_fetch_log.jsonl` (one line per unique-URL fetch, `binary_retained:false`).

### Gate metrics (before bulk fetch)
- **staff_report precision 100 %** (n=55 unique-URL random sample ground-truthed against live PDFs;
  15 extracted clean and all confirmed land-use, 40 image-scans with unambiguous land-use titles).
- **plan_amendment precision 100 %** (whole class, 4 unique URLs — all confirmed Logan 2045 General
  Plan drafts / adoption resolution).
- **Recall:** 0 clear misses in a random-100 unclassified sample; an exhaustive sweep of every
  land-use-keyword-plausible unclassified title found + fixed the single miss (`Ord 23-10 Public
  Zones Homeless Shelter`); est. miss <2 %.

See `CLAUDE.md` (Primary-document text layer section) for the class taxonomy, WORKSHOP/ACTION dedup
note, and the documented boundary decisions.

## Coverage (what exists)
| Body | Years with packets | Documents indexed |
|---|---|---|
| City Council | 2022, 2023, 2024, 2025, 2026 | 1,096 |
| RDA (items inside combined council meetings) | 2022–2026 | 28 |
| **Total** | | **1,124** |

Per year (all documents): 2022 = 235, 2023 = 272, 2024 = 248, 2025 = 255, 2026 = 114 (partial year).
By kind: `staff_report` 867, `agenda` 222, `notice` 24, `proclamation` 11. Spans 149 meeting-dates.

## Council vs RDA asymmetry
Logan holds **no standalone RDA meetings** and publishes **no separate RDA agenda** — the RDA board
is the City Council, and RDA business runs as `Res …/Ord …` items inside the combined council
meeting (mirroring `../meeting_minutes`, which splits Council/RDA from one combined minutes doc).
So `body=RDA` here is a **document-level** tag (filename contains `RDA`), not a separate meeting
series: 28 RDA-tagged docs vs 1,096 Council. Do not expect an RDA agenda or an RDA-only date.

## What was checked / what's absent (gaps are data)
- **2020 & 2021 packets: NONE published.** No `2020_`/`2021_council_agendas_and_packets.php` page
  exists (2020 URL serves a stale duplicate of 2019 content; 2021 URL is HTTP 404; `go.loganutah.gov
  /2020councilpackets` and `/2021councilpackets` both 404). These meetings **were held** — minutes
  and roll-call votes for 2020-01-07 onward are in `../meeting_minutes/all_votes.csv`. This is a
  **city publishing gap, not a scraper miss.**
- **2019 packets exist but are out of window.** The page named `2020_council_agendas_and_packets.php`
  (old `cms9.revize.com` host) actually holds the 2019 archive (44 meetings); a separate
  `2019_…php` holds the same. Both are outside the 2020–2026 window and **not indexed** (they don't
  join to `../meeting_minutes`, which starts 2020).
- **1 document dropped:** `General Canvass Meeting Notice 2023 - RECOUNT.pdf` (meeting group
  "RESCHEDULED - Canvass of the General Election Recount Results") — a recount-canvass notice with
  **no determinable month/day** in its filename or label. Logged here rather than given a fabricated
  date. Its `source_url` remains in `raw/_listing/2023_listing.html`.
- **Minutes PDFs are intentionally excluded** from this dataset (they belong to
  `../meeting_minutes/`); the parser drops any filename containing "Minutes".

## Provenance retained (`raw/`)
- `raw/_listing/*.html` — the 7 scraped year-listing pages (2019, 2020, 2022–2026; 2021 = 404, not
  saved). `raw/_listing/_fetch_log.jsonl` — discovery fetch log.
- `raw/_size_probe.jsonl` — HEAD Content-Length probe per `source_url` (2026-07-05).
- `raw/_parse_listings.py` — the exact parser used to build `index.csv`.

## To retrieve content
Fetch a row's `source_url` (public GET; image-heavy PDFs need vision/OCR, not `pdftotext`). To
re-hydrate all, `polite_fetch.py --batch <source_urls>` (~1.56 GB for all 1,124).
