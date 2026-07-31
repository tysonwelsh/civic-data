# packets/ — agenda packets & staff reports (build & linkage)

Additive dataset built by `expand-city-sources` (Source 1), as-of **2026-07-02**. The staff
analysis behind Lehi **City Council** and **Planning Commission** agenda items — staff reports,
fiscal notes, zoning/land-use analysis, resolutions/agreements, exhibits — keyed by meeting date
so it joins to the existing minutes/votes. **Pilot window: 2024–2025.** Does not modify any
existing dataset.

## Layout

```
packets/
  raw/<YYYY-MM-DD>/              originals verbatim, one folder per meeting date
    agenda_clip<clip_id>.pdf     the agenda outline (one per meeting)
    <attachmentId>_<file>.pdf    linked staff reports / exhibits
    _fetch_log.jsonl             provenance per file (url,status,bytes,sha256,retrieved_utc)
  index.csv                      one row per retained file
  dropped_oversize.csv           attachments >4 MB NOT downloaded (recoverable by URL)
  unrecovered.csv                genuine gaps (no agenda posted / duplicate portal row)
  AVAILABILITY.md                portal, window, asymmetry, sampling, gaps
  CLAUDE.md                      this file
```

## index.csv columns

`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format,
extraction_method, path, bytes, clip_id, delivery` + the 2026-07-16 primary-document
pilot extension columns `doc_class, fetch_status, sha256, text_path, text_chars`
(see "Primary-document text layer" below).

- **date** — meeting date (`YYYY-MM-DD`), the join key.
- **body** — `Council` or `PlanningCommission` (includes each body's Work Sessions).
- **meeting_type** — (§9 contract column; blank where not recorded)
- **packet_kind** — `agenda` (the agenda outline PDF) or `staff_report` (a linked attachment).
  Together, a meeting's `agenda` + its `staff_report` rows constitute its agenda packet.
- **source_url** — for `agenda`, the `AgendaViewer.php?clip_id=…` link (stable, portal-facing);
  for `staff_report`, the direct Legistar attachment URL that was fetched.
- **format** — `text` (born-digital; has an embedded font layer) or `scanned` (raster image, no
  font layer → needs OCR; 9 files). Classified with `pdffonts`.
- **extraction_method** — `none (raw retained)` (the ORIGINAL 2026-07-02 build label). **This is
  now a legacy value: born-digital text sidecars DO exist** (`text/<stem>.txt`, 553 files) — they
  were added by the later mandatory-sidecar retrofit (REFACTOR_PLAN 5.6) and feed `cities.db`
  `fts_packet`. The authoritative per-row text-availability signal is the pilot columns
  `text_path` / `text_chars` / `fetch_status` (below), not this legacy `extraction_method` label.
- **path** — repo-relative path to the raw file. **bytes** — file size on disk.
- **doc_class** (staff_report attachments only) — `staff_report` | blank = **honestly
  unclassified** (out of pilot scope, never force-bucketed). `member_memo` /
  `plan_amendment` / `development_agreement` are honest EMPTIES here (see below). Assigned by
  `classify_attachments.py`. Agenda rows carry blank `doc_class`.
- **fetch_status** (pipeline rows only) — `ok` (classified + text sidecar linked) | `needs_ocr`
  (raw on disk but no usable text layer — image-only/scanned, honest OCR floor) | blank
  (unclassified-with-sidecar or agenda rows — out of pilot scope, Sandy-faithful).
- **sha256** — hash of the retained raw binary (populated for `ok` + `needs_ocr` rows).
- **text_path** / **text_chars** — extracted-text sidecar (dataset-relative) and its length.
- **clip_id** — Granicus clip id (disambiguates two meetings sharing a date folder).
- **delivery** — how the agenda was served: `s3` (agenda on `granicus_production_attachments`
  S3) or `documentviewer` (agenda served as `DocumentViewer.php?file=lehi_<hash>.pdf`). Purely
  informational — attachment extraction works identically for both.

## How to join to minutes / votes

Join on **`date`** (+ `body`):

- Council packets ↔ `meeting_minutes/minutes_index.csv` and `meeting_minutes/all_votes.csv`
  (`body=Council`). 52 of 53 in-scope council meeting dates match a minutes date exactly.
- PC packets ↔ `planning_commission/minutes_index.csv` / `all_votes.csv`
  (`body=PlanningCommission`). PC **Work Sessions** have packets but usually **no minutes** — those
  dates won't match, by design.
- The `db/lehi.db` relational layer keys motions by date too; a packet row's `date`+`body` lines up
  with the motion/application rows there. A staff report's `title` (e.g. "BOWDEN GENERAL PLAN
  AMENDMENT CITY COUNCIL REPORT", "Res 2025-27 and Agreement") often names the ordinance/resolution
  or applicant, letting you tie a specific packet document to a specific motion.

Mayor voting rule still applies downstream: Lehi's mayor votes only to break ties — don't treat a
packet's staff recommendation as a member vote.

## Scrape method (Granicus ViewPublisher, Lehi specifics)

1. Fetch `https://lehi.granicus.com/ViewPublisher.php?view_id=1` (browser UA + Referer). Parse the
   second `<table>` with BeautifulSoup; each row = (meeting name, date, agenda link, minutes link).
   Classify body by the name string. Filter to Council + PC, 2024–2025.
2. For each row, `GET AgendaViewer.php?view_id=1&clip_id=<id>` **without following redirects** and
   read `Location`:
   - `…/DocumentViewer.php?file=lehi_<hash>.pdf` → fetch directly on `lehi.granicus.com`.
   - `https://granicus_production_attachments.s3.amazonaws.com/lehi/<hash>.pdf` → **the bucket name
     has an underscore, so its wildcard TLS cert fails hostname validation in `requests`.** Rewrite
     to **path-style** `https://s3.amazonaws.com/granicus_production_attachments/lehi/<hash>.pdf`
     (valid cert) before fetching. (`curl` tolerates the virtual-host form; Python `requests` does
     not.)
3. Extract each agenda PDF's embedded attachment links: regex `‌/URI\s*\(([^)]+)\)` over the raw
   PDF bytes, keep URLs matching `lehi.granicus.com/services/legistar/download/…` **or**
   `legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/…`. Both hosts fetch directly
   (the `legistarweb-production` bucket uses a hyphen — no TLS issue). Attachment filename =
   `<numericId>_<basename-from-URL>`.
4. Download agendas + attachments through
   `.claude/skills/expand-city-sources/scripts/polite_fetch.py` (its `save()` was imported and
   called per file: browser UA, `Referer: …ViewPublisher.php?view_id=1`, ~0.7 s throttle, retry
   with backoff, and a `_fetch_log.jsonl` line per file). A **4 MB per-file cap** was applied to
   attachments only (see `dropped_oversize.csv`); agendas were never capped.

## Caveats

- **Council staff-report asymmetry (read `AVAILABILITY.md`).** Only 5 of 56 council meetings have
  hyperlinked staff reports; the other 51 council agendas name attachments in text but don't link
  them, so those council staff PDFs aren't portal-retrievable for 2024–2025. PC packets are
  effectively complete (45/56 meetings with reports). Do **not** read "few council staff_report
  rows" as "few council items" — it's a publishing-pipeline artifact, not a substance gap.
- **Sampling:** 163 attachments >4 MB (~3.05 GB, mostly PC plats/studies) were not downloaded;
  they're logged in `dropped_oversize.csv` with source URLs — re-fetch to raise the cap.
- **`source_url` for agendas** is the `AgendaViewer` link (resolves through the redirect chain
  above), not the final S3/DocumentViewer URL, because the final hashed URL is not stable/portable.
  The final fetched URL for every file is in the row's `_fetch_log.jsonl`.
- **Text corpus DOES exist** (correcting the original 2026-07-02 "no text corpus" claim): 553
  born-digital sidecars under `text/` (added by the mandatory-sidecar retrofit; log in
  `text/_extraction_log.csv`). Run `screen_corpus.py text/` if you extend the corpus.
- **Rebuild:** re-run the scrape (method above) against ViewPublisher; the portal has no API, so a
  markup change to ViewPublisher would require updating the table parser. Re-run
  `python3 classify_attachments.py` (idempotent) to regenerate `doc_class` + the pilot columns.

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

The 452 `staff_report` attachment rows (2024–25 pilot window) were classified into the
primary-document classes and the SCHEMA_SPEC §9 pilot columns populated. Lehi is a
**classify-in-place** city — the born-digital text already exists on disk (`text/`), so no
new fetching was needed; the raw PDFs are RETAINED (unlike Sandy, which discards binaries).

| doc_class | rows | fetch_status | what it is |
|---|---|---|---|
| staff_report | 272 | 272 ok | land-use staff analysis — PC + City Council staff reports and Development Review Committee (DRC) reviews behind rezone / GPA / plat amendment / subdivision / conditional-use / development-code-amendment / area-plan / development-agreement items |
| member_memo | 0 | — | **EMPTY** — Lehi is all at-large and files no councilmember proposal memos in the 2024–25 corpus (0 "memorandum" heads; verified) |
| plan_amendment | 0 | — | **EMPTY** — the GP/land-use-map amendment substance appears only as (a) the staff report → `staff_report`, (b) the applicant request letter, and (c) an aerial/GP map exhibit; there is no separable proposed-element / Exhibit-A plan-text file to classify |
| development_agreement | 0 | — | **EMPTY** — the born-digital DA-titled files are the PC staff REPORTS about the DA (→ `staff_report`, e.g. `Stack_Soccer_DA`, `Hammond_DA_1`, `Water_s_Edge_DA_1`); the executed/draft INSTRUMENTS ride the corpus only as scanned `*_DA_2` exhibits with no text layer (→ `needs_ocr`, unverifiable) and are left blank rather than guessed |
| (blank) | 180 | 11 needs_ocr | unclassified: 169 non-report exhibits with text (aerials, GP/zoning maps, applicant letters, PC bylaws, `pz<date>`/`ws<date>` agenda-list attachments, purchase orders, resolutions/ordinances, code-table exhibits, interlocal/construction agreements) + 11 image-only rows |

- **Classifier**: `classify_attachments.py` — deterministic, rerunnable, **no db join** (Lehi has
  no Legistar matter metadata). Because the attachment TITLES are underscore-munged and often
  truncated (`Newbold_1`, `Edge_Homes_Main_Street_ZC_1`, `Warner_2`), the PRIMARY signal is the
  **text-sidecar HEAD**: Lehi staff reports open with a banner template ("`<CASE NAME>` …
  PLANNING COMMISSION REPORT" / "CITY COUNCIL REPORT", Applicant / Meeting Date / Requested
  Action fields); DRC reviews open with "Lehi City Development Review Committee". Title tokens
  (`CC_Staff_Report`/`PC_Staff_Report`, `_DRC_`) corroborate. Reading title + sidecar-head is
  fully deterministic.
- **Quality gates (2026-07-16)**: precision **staff_report 55/55 = 100%** (deterministic sample,
  n=55 ≥ 50, ground-truthed against sidecar heads / raw PDFs — every row a genuine land-use staff
  report). Recall: a full sweep of all **169 unclassified-with-sidecar** rows for independent
  report signals ("STAFF RECOMMENDATION", "…COMMISSION REPORT", "DEVELOPMENT REVIEW COMMITTEE",
  etc.) surfaced **0 missed staff reports** (the 18 signal hits are PC bylaws + `pz<date>` agenda
  lists + a PARC grant recommendation — correctly excluded). Miss rate 0% (< 10% gate).
- **Boundary decisions (documented, not bugs)**: (1) DRC (Development Review Committee) staff
  reviews ARE included in `staff_report` — they are primary staff land-use analysis with their
  own banner template. (2) DA-titled files that are PC/CC REPORTS are `staff_report`, not
  `development_agreement` (Sandy's instrument-only rule). (3) Aerials/vicinity/GP-zoning maps,
  applicant narrative letters, code-table/`AHOZ_Proposal` proposed-text exhibits, resolutions and
  signed ordinances (ordinances live in `ordinances/`) are excluded. (4) The `pz<date>` /
  `pz_ws_<date>` / `<date>_CC` attachments are meeting agenda/packet-list PDFs mislabeled
  `packet_kind=staff_report` by the original scraper — correctly left `doc_class` blank.
- **needs_ocr (11 rows)**: raw on disk, no usable text layer (9 `format=scanned` + 2
  `format=text` that extracted image-only <200 chars — `Aerial_Map`, `Horlacher_2`). All are
  non-report exhibits (aerials, a purchase order, a DRAFT construction agreement, scanned `*_DA_2`
  exhibits) → `doc_class` blank, `fetch_status=needs_ocr`, sha256 recorded, no text file — a
  recorded OCR floor, not a silent skip. (The orchestrator's "9 scanned" estimate; 11 is the true
  no-usable-text count.)
- **Pilot columns are Sandy-faithful**: populated only for the pipeline rows (272 `ok` + 11
  `needs_ocr`). The 169 unclassified rows that DO have sidecars keep blank pilot columns (out of
  pilot scope) even though their text is on disk and already indexed in `fts_packet`.
- **Coverage caveat**: this layer covers the **2024–25 pilot window only**. The **2020–2023**
  packets are a known **deferred** acquisition gap (available on the same portal, not yet
  retrieved) — see `AVAILABILITY.md`. Council staff-report asymmetry still applies (only 5/56
  council meetings hyperlink staff reports vs 45/56 PC), so `staff_report` skews to PC by
  publishing pipeline, not by substance.
- **Acceptance (Sharkey pattern)**: `CC_Staff_Report_Bowden_General_Plan_Amendment_10.22.24`
  (2024-10-22, City Council, `staff_report`, `text/2924500_..._10.22.24.txt`, 12,217 chars) —
  its verbatim analysis ("The VLDRA designation requires half-acre lots"; applicant narrative that
  the change "will increase the tax revenue of the city and help with housing affordability") is
  the primary source behind council **motion 2** that day: "Consideration of Ordinance #64-2024
  the Bowden General Plan Amendment on 5.18 acres located at 9861 West 9600 North changing the
  land use designation from VLDRA" (passed 5:0). Staff-report acreage (5.18), address (9861 West
  9600 North), and designation (VLDRA) match the motion exactly.
