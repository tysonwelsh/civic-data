# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-05

Built by `expand-city-sources` (Source 1). The per-agenda-item documents behind each Logan
**City Council** meeting — the agenda plus every ordinance, resolution, budget memo, and staff
report that supports a motion in `../meeting_minutes/all_votes.csv` (`body` = `Council` or `RDA`).

## This is a LINK INDEX, not a document store — by deliberate design
Unlike St. George (one bundled PDF per meeting), Logan's Revize CMS publishes **each agenda item
as its own PDF** (`AGENDA 2025January7.pdf`, `Ord 25-01 … - ACTION.pdf`, `Res 25-02 … -
WORKSHOP.pdf`, …). Good news: fine granularity — you can pull the exact staff report for one item.
Bad news: **volume + size.** 1,124 in-window documents, mean ≈1.4 MB, max ~31 MB (site plans,
plats, engineering exhibits — image-heavy, not born-digital text), totalling **~1.56 GB**. That is
over the repo's ~400 MB local-store budget, and OCR/vision (not `pdftotext`) is needed to read the
image-heavy ones. Per the repo owner's index-only convention (limited disk, low text-conversion
value), **the PDFs are not stored locally.** `index.csv` catalogs every document with a live
`source_url` + byte size so any specific item can be fetched on demand. See `AVAILABILITY.md` for
the exact size math and the store-vs-index decision.

The retention exception is intentional and scoped to this dataset (the packet PDFs are public and
re-fetchable). `raw/` retains the **provenance**: the 7 scraped listing HTMLs
(`raw/_listing/*.html`), the discovery fetch log (`raw/_listing/_fetch_log.jsonl`), the size-probe
log (`raw/_size_probe.jsonl` — URL → Content-Length), and the parser (`raw/_parse_listings.py`).
The normal "retain every raw original" rule still applies to every *other* dataset in this repo.

## How an LLM/agent should use this
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type` for Budget Workshop /
   Truth-in-Taxation / special vs regular). Each row is ONE document.
2. To read it, **fetch `source_url`** (public GET; a `loganutah.gov` → `cms9files.revize.com` PDF).
   Check `size_mb` first.
3. Extract image-heavy PDFs with **vision or OCR**, not `pdftotext`. Label whatever you produce.
4. Bulk re-hydrate: feed the `source_url` column to `polite_fetch.py --batch` (budget ~1.56 GB for
   all 1,124).

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method(=not_retrieved), path(empty), meeting_title, filename, content_length_bytes,
size_mb, stored_locally(=no)` + the 2026-07-16 §9 primary-document columns
`doc_class, fetch_status, sha256, text_path, text_chars` (see the Primary-document text layer
section below).
- One row per **document** (not per meeting). `title` = the document (cleaned filename);
  `meeting_title` = the meeting label as posted (`"January 7 - Regular Meeting"`).
- `packet_kind` ∈ `agenda` (222), `staff_report` (867 — the ordinances/resolutions/memos),
  `notice` (24 — cancellation/canvass notices), `proclamation` (11). **Minutes PDFs are EXCLUDED**
  (they live in `../meeting_minutes/`); an agenda is never mistaken for minutes.
- `body`: `Council` (1,096) or `RDA` (28). See asymmetry note below.
- `format=na` / `stored_locally=no` / `path` empty because nothing is stored — the row is a pointer.
- `size_mb`/`content_length_bytes` from a HEAD probe on 2026-07-05 — populated for 1,121 of 1,124
  rows (blank on 3 = server returned no Content-Length on that probe; the URL is still live — fetch
  to get the file).

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

The 867 `staff_report` pointers were classified into land-use-primary classes and those classes'
text extracted (fetch → `pdftotext -layout` → sha256 → **discard binary**; 2.69 MB of text vs the
818 MB of binary that was downloaded-and-discarded). Logan has **no matter metadata** — the
classifier is **title-only** (Logan's human-typed filenames carry the instrument number + subject +
a WORKSHOP/ACTION stage suffix, e.g. `Ord 22-04 Code Amendments Short Term Rentals - WORKSHOP`).
Only `packet_kind=staff_report` rows are eligible; agendas/notices/proclamations stay blank.

| doc_class | rows | ok | needs_ocr | 404 | what it is |
|---|---|---|---|---|---|
| staff_report | 207 | 207 | 0 | 0 | land-use primary docs — rezone/downzone, LDC/Title-17 code amendments, annexation/boundary/disconnect, subdivision, ROW/easement vacations, overlays (PDO/critical-lands/historic/gateway), ADU/home-occupation/STR, site/concept plans, neighborhood plans, MIH code, flood-damage prevention, infill/flag-lot, land-use moratorium, homeless-shelter zoning |
| plan_amendment | 6 | 6 | 0 | 0 | Logan 2045 General Plan drafts + the Res 26-09 adoption resolution |
| development_agreement | 0 | — | — | — | **EMPTY** — Logan 2022–26 rides no DA/MDA instrument through the packet corpus (verified; only interlocal / franchise / power-sales / pooling agreements exist, which are NOT development agreements) |
| member_memo | 0 | — | — | — | **EMPTY** — Logan publishes no council-member proposal/amendment memos in packets (staff memos exist but are not member-authored) |

- **The taxonomy is LAND-USE-PRIMARY.** Budget/admin/finance resolutions (Budget Adjustments, URS
  retirement, elected wages, fee schedules, power-sales contracts, CDBG/ConPlan action plans,
  fireworks, master plans for transportation/water, impact-fee facilities plans, RDA
  community-reinvestment project-area plans) are **honestly unclassified** — not force-bucketed.
- **needs_ocr is now 0/213 (was 165/213, 77%) — the vision pass closed the OCR floor (2026-07-17).**
  Logan's land-use exhibits are image-heavy plats / site plans / engineering drawings scanned to PDF;
  those 165 rows had no pdftotext layer and were recorded as an OCR floor (not a silent skip). On
  2026-07-17 all 165 were transcribed by a **Read-tool vision pass at 150 dpi over sha256-verified
  re-fetches** (157 unique docs, ~2,900 pages) and flipped to `fetch_status='ok'` with
  `extraction_method='claude_vision'` (`text_path`/`text_chars` set; sidecars in
  `text/attachments/`). Imagery pages (plats, maps, aerials, renderings, blank dividers) carry honest
  inline markers — e.g. `[map/plat page N — no text]`, `[Page N]`, `[part K/M — PDF pages X–Y]` at
  merge seams for docs split across batches — never invented prose; genuinely-duplicated source pages
  are transcribed and flagged (`[NOTE: This page duplicates …]`). The other 48 `ok` rows remain the
  born-digital ordinance/resolution bodies + staff memos extracted by `pdftotext -layout`. **0 dead
  URLs (no 404s)** — Logan's Revize CMS was healthy as of 2026-07-16.
- **WORKSHOP vs ACTION dedup:** the same instrument commonly appears twice — once at the WORKSHOP
  stage and once at ACTION — as **two rows with DIFFERENT URLs** (genuinely different documents: a
  draft-stage staff report vs the final-stage packet). Those are fetched independently. Only
  **byte-identical URLs** dedup via the pipeline's `seen` map (14 classified rows were such dups).
  Among the 213 classified rows there are 121 distinct title-stems.
- **Gate metrics (2026-07-16, samples ground-truthed against live PDFs):** staff_report precision
  **100 % (n=55 unique-URL sample; 15 extracted clean, all confirmed land-use, 40 image-scans with
  unambiguous land-use titles)**; plan_amendment precision **100 % (whole class, n=4 unique URLs —
  all confirmed Logan 2045 GP docs)**. Recall: **0 clear misses in a random-100 unclassified
  sample** + an exhaustive sweep of every land-use-keyword-plausible unclassified title (found + fixed
  the one miss, `Ord 23-10 Public Zones Homeless Shelter`); est. miss <2 % (only two deliberately-
  excluded ambiguous "Code Amendments Administrative Updates" / "Residential Driveway Standards"
  titles lacking an LDC/Title-17 marker).
- **Boundary decisions (documented, not bugs):** (a) bare "right of way" / fee-schedule tokens are
  NOT land-use — a `Right of Way Permit Fee Change` / `Community Development Fee Schedule
  (Annexation Applications)` is an admin fee resolution, excluded; every real ROW/easement *vacation*
  is caught by the `vacat` token. (b) LDC (Title 17) code amendments are in-class; LMC (municipal
  code) amendments are in-class ONLY when they carry a land-use token (e.g. Home Occupations, STR) —
  `LMC 5.10 Alcoholic Beverages` / `Mobile Food Vendor` / `Micromobility` stay out. (c) Neighborhood /
  small-area plans (Hillcrest, Wilson) are filed as `staff_report` (land-use), keeping
  `plan_amendment` strictly the citywide General Plan. (d) RDA Community Reinvestment Project Area
  plans and Impact-Fee Facilities Plans are excluded (redevelopment/finance instruments).
- **Pipeline (rerunnable, resumable):** `python3 classify_attachments.py` (rewrites `doc_class`
  only; `--dry-run` for counts) → `python3 fetch_extract_text.py` (processes only classified rows
  with blank `fetch_status`; ≥1.0 s/host, browser UA, honors 404/429/503; sha256 then DISCARDS the
  binary). Provenance is `sha256` + `source_url` + `text/_fetch_log.jsonl` (one JSONL line per
  unique-URL fetch, `binary_retained:false`). Sidecars: `text/attachments/<date>_<slug>_<urlhash8>.txt`.

## Council vs RDA — read this before joining on body
Logan does **not** hold standalone RDA meetings and publishes **no separate RDA agenda**. The
Redevelopment Agency board *is* the City Council; RDA business is transacted as ordinary
`Res …/Ord …` items **inside the combined council meeting** (this is exactly why
`../meeting_minutes` splits Council/RDA out of one combined minutes doc). So here, RDA is tagged at
the **document** level: a staff doc whose name contains `RDA` (e.g. `Res 22-45 RDA Budget
Adjustment …`) → `body=RDA`; the shared agenda and everything else → `body=Council`. Consequence:
some RDA-tagged docs sit on a date that has no RDA roll-call (workshop-only item), and RDA items
that don't say "RDA" in the filename stay `Council`. Best-effort by design — the meeting is one
combined meeting.

## Coverage & join
- **1,124 documents across 149 meeting-dates, 2022–2026** (Council 1,096 / RDA 28).
- **2020 & 2021 have NO packet pages** — a Logan *publishing* gap, not a scraper miss. Those
  meetings were held (minutes + votes are in `../meeting_minutes`, 2020-01-07 onward); the city
  simply never posted agendas-and-packets pages for them. **2019** packets exist (on a stale page
  mislabeled `2020_…`) but are **out of the 2020–2026 window and not indexed.** Details in
  `AVAILABILITY.md`.
- URLs were **scraped, never guessed** — Logan's human-typed filenames are wildly inconsistent
  (`AGENDA 2023April04.pdf`, `Agenda for 2023February21.pdf`, `25December16.pdf`, a typo'd
  `AGENDA 2017March3 Spanish.pdf` on the 2026 page). Href path style also varies by year (bare
  filename in 2019/20; `departments/admin/council/…?t=<cachebuster>` in 2022+). Dates are derived
  from the English agenda filename, with the **year forced to the listing-page year** to defuse
  those filename typos.

## Regenerate / refresh
Re-scrape `https://www.loganutah.gov/government/city_council/<YEAR>_council_agendas_and_packets.php`
(2022–2026; 2026 mirror `go.loganutah.gov/2026councilpackets`) with `polite_fetch.py`, re-run the
parser in `raw/_parse_listings.py`, re-probe sizes, rebuild `index.csv` with the same columns.
