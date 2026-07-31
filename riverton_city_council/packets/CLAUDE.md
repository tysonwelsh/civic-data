# packets/ — agenda packets & staff reports (build & linkage)

Additive dataset built by `expand-city-sources` (Source 1), as-of **2026-07-13**. The staff
analysis behind Riverton **City Council**, **Planning Commission**, and **Redevelopment
Agency (RDA)** agenda items — staff reports, findings, resolutions/ordinances, exhibits —
keyed by meeting date so it joins to the existing minutes/votes. **Window: 2020-01-01 →
2026-07-13** (the Granicus archive reaches back to 2015, but the repo data floor is 2020).
Does not modify any existing dataset. **STORED mode** (separable staff reports, like draper
era C): each small born-digital staff report is on disk; bulky exhibits (>4 MB) are dropped
and logged (`dropped_oversize.csv`), and the 2020–2021 bundled whole-meeting PDFs are
catalogued **index-only**.

## Vendor / delivery (the important thing)

Agendas live on Granicus (`rivertoncity.granicus.com/ViewPublisher.php?view_id=1`, one flat
table for ALL bodies). The city CMS is Revize but hosts no packets. Every archived meeting
has an `AgendaViewer.php?clip_id=<n>` link that **302-redirects** (through a Google gview
wrapper) to one of three era-specific targets — discovered by resolving the redirect
no-follow:

| Era | Window | AgendaViewer 302 target | Attachments |
|---|---|---|---|
| **A. Generated-agenda HTML** | early 2020 (2 mtgs: 2020-01-07, 2020-08-04) | `/GeneratedAgendaViewer.php?view_id=1&clip_id=<n>` (HTML agenda) | per-item `MetaViewer.php?view_id=1&clip_id=<n>&meta_id=<id>` links, each serving the attachment PDF **directly** (200, no redirect) |
| **B. DocumentViewer PDF** | rare (2 mtgs: 2020-03-12, 2025-02-27) | `/DocumentViewer.php?file=rivertoncity_<hash>.pdf` (PDF agenda outline) | embedded `/URI` legistar links, same as era C |
| **C. S3 agenda-outline PDF** | 2020-05 → present (291 mtgs) | `granicus_production_attachments.s3.amazonaws.com/rivertoncity/<hash>.pdf` (born-digital agenda outline, ~50–210 KB) | embedded `/URI` links to per-item staff reports/exhibits |

**Era-C/B attachment hosts (two, both flat one-level `/URI` links off the agenda):**
- `legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/<id>/<name>.pdf`
- `rivertoncity.granicus.com/services/legistar/download/pdf/<id>/<name>.pdf`

Both born-digital PDFs. Unlike draper era C there is **no separate "memo" layer** — the
agenda outline links directly to every staff report, resolution, ordinance, and exhibit at
one level, so `packet_kind` (staff_report vs exhibit) here is a **filename heuristic**
(`*Staff_Report*`/`*_Report*`/`*Memo*` → `staff_report`, else `exhibit`), NOT a structural
distinction — do not read `exhibit` as "not staff analysis".

**Bundled "Agenda Packet" column:** the ViewPublisher table exposes a bundled whole-meeting
cloudfront PDF (`d3n9y02raazwpg.cloudfront.net`) for **18 in-scope 2020-01…2021-05
meetings** only (0–25 MB, 145 MB total). These duplicate the separable staff reports we
already store, so they are catalogued **INDEX-ONLY** (`packet_kind=full_packet`,
`stored=no`, `format=na`, `bytes` from HEAD `Content-Length`) — the documented, allowed
exception to "retain every raw original" (public + re-fetchable from `source_url`;
vision/OCR needed to read one).

## Layout

```
packets/
  raw/<YYYY-MM-DD>/                         originals verbatim, one folder per meeting date
    <Body>_clip<id>_agenda.pdf|.html        the agenda outline (era A: HTML; B/C: PDF)
    <Body>_clip<id>_att<N>_<name>.pdf        a staff report / exhibit (era C/B legistar; era A meta<id>.pdf)
    _fetch_log.jsonl                         provenance per file (url,status,bytes,sha256,utc)
  text/                                      pdftotext -layout sidecars + html tag-strip
    _extraction_log.csv                      per-PDF outcome (extracted/image_only/too_big/error)
  index.csv                                  one row per document (stored or index-only)
  dropped_oversize.csv                       attachments >4 MB NOT downloaded (recoverable by URL)
  AVAILABILITY.md                            coverage, size math, mode decision, gaps
  CLAUDE.md                                  this file
```

## index.csv columns

§9 contract: `date, title, body, meeting_type, packet_kind, source_url, retrieved_date,
format, extraction_method, path` + extras `bytes, clip_id, delivery, stored` + the
2026-07-16 primary-document columns `doc_class, fetch_status, sha256, text_path, text_chars`
(see "Primary-document text layer" below).

- **date** — meeting date (`YYYY-MM-DD`), the join key. **body** — `Council`,
  `PlanningCommission`, `RDA`.
- **meeting_type** — blank (Riverton's combined Informal+Work+Regular is one doc per day).
- **packet_kind** — `agenda` (the outline) / `staff_report` / `exhibit` (filename heuristic,
  see above) / `full_packet` (bundled, index-only).
- **source_url** — for `agenda`, the stable `AgendaViewer.php?clip_id=` link; for
  attachments, the direct legistar/MetaViewer URL fetched; for `full_packet`, the cloudfront
  bundle URL. The exact fetched URL + status per file is in that date folder's
  `_fetch_log.jsonl`.
- **format** — `text` (born-digital PDF) / `scanned` (raster PDF, OCR/vision needed) /
  `html` (era-A agenda) / `na` (not stored: oversize or index-only).
- **extraction_method** — `pdftotext -layout` (sidecar in `text/`), `html tag-strip`
  (sidecar), `none (image-only pdf; OCR/vision if needed)`, `none (not stored; index-only)`,
  `none (oversize >4MB; not stored)`.
- **bytes** — file size on disk; for `full_packet`, HEAD `Content-Length`.
- **clip_id** — Granicus clip (`clip<N>`), disambiguates two meetings sharing a date.
- **delivery** — `s3_agenda_pdf` / `generated_agenda_html` / `metaviewer` / `legistar` /
  `cloudfront_bundle` / `none`.
- **stored** — `yes` (raw on disk) / `no` (index-only, oversize-dropped, or fetch-failed).

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

Riverton is a **Bucket-A classify-in-place** city: the born-digital staff-report/exhibit text
sidecars already exist on disk (built by Source 1), so this layer only adds a `doc_class`
label + the §9 fetch/text columns — **no bulk fetching**. `classify_attachments.py`
(deterministic, rerunnable) scans the **staff_report + exhibit rows together as one candidate
pool** (2,702 rows) — because Riverton's `packet_kind` is a filename heuristic, not structural
(see Caveats) — and assigns a class by **title token only** (Riverton has no matter table).

| doc_class | rows | ok | needs_ocr | index-only | what it is |
|---|---|---|---|---|---|
| staff_report | 522 | 317 | 1 | 204 | land-use staff/PC/CC reports (rezone, text & code amendment, ZTC, subdivision, plat, CUP-HO, site plan, lot-line, GP-amendment, DA staff reports). Body: PC 360 / Council 162. Every one is the "MEMORANDUM To: Planning Commission / Honorable Mayor and City Council — From: Planning Department" staff memo |
| development_agreement | 8 | 8 | 0 | 0 | DA / MDA **instruments** + amendments/drafts (recorded agreement text) — NOT staff reports *about* a DA, NOT the enacting ordinance/resolution, NOT fee schedules |
| member_memo | 0 | — | — | — | **EMPTY (honest).** Riverton files no council-member proposal memos in its packet corpus — the only "memo" titles are staff / MOU / OPMA-training / proclamation memos |
| plan_amendment | 0 | — | — | — | **EMPTY (honest).** Riverton's GP is a single land-use map; its GP-amendment docs are either enacting ordinances (→ `ordinances/`) or "… Staff Report" (→ staff_report), so no separate substance exhibit rides the packet corpus |

**Fetch/text columns** (classify-in-place — text already on disk):
- `fetch_status` = `ok` (classified + stored born-digital PDF with a `text/` sidecar) |
  `needs_ocr` (classified + stored but image-only, `format=scanned`, no sidecar — 1 row) |
  blank (classified but **index-only**: 189 oversize-capped >4 MB + 15 permanently-403
  legistarweb 2020 exhibits — no binary on disk; the row's `source_url` is still live for
  oversize, dead for the 403s).
- `sha256` = of the stored raw binary; falls back to the row's `raw/<date>/_fetch_log.jsonl`
  entry; blank for the 204 index-only rows (oversize were HEAD-probed only, never downloaded;
  403s never fetched — so no hash exists for either).
- `text_path` / `text_chars` = the dataset-relative `text/…txt` sidecar and its char count
  (set only on the 325 `ok` rows).

**Classifier method** — `classify_attachments.py`, title-token, first-match-wins:
staff_report requires an explicit `Staff Report` / `PC Report` / `CC Report` token (bare
"Report" is NOT used — it would catch Monthly-Manager / Annual / YTD / Compliance / Title
reports, which are not land-use staff analysis) and is land-use-scoped by a non-land-use
exclusion guard (budget / finance / audit / personnel / property-tax / impact-fee-schedule —
which in practice drops **0 of 521**: Riverton's staff-report corpus is entirely
planning/land-use). development_agreement requires a `Development Agreement`/`MDA` token and
excludes report/staff/ordinance/resolution/fee-schedule.

**Quality gates (2026-07-16, ground-truthed against on-disk sidecars):**
- **Precision:** staff_report **100%** (n=50 random, all the "MEMORANDUM … Planning
  Department" staff-memo format, all land-use); development_agreement **100%** (whole class
  n=8, each verified recorded-agreement text). member_memo / plan_amendment empty (no
  precision to compute).
- **Recall:** 0 misses in a 100-row unclassified title sample; a stronger sweep of all 1,873
  unclassified rows-with-sidecars for the staff-report MEMORANDUM template surfaced 4 memo-
  format hits, of which ~2 were genuine land-use staff reports the title-token missed →
  est. miss ≈ 2/(522+2) ≈ **0.4%**, far under the 10% bar. One tokenization edge fixed
  ("PC Report1" digit-suffix); documented residuals below.
- **Boundary decisions (documented, not bugs):** (a) staff-authored **memos** not titled
  "Report" (e.g. "Riverton Business Park Amnd-Staff PC Memo") stay unclassified, matching the
  Sandy convention. (b) A DA **fee schedule** ("MDA Amendment Impact Fees") is NOT a
  development_agreement (it is a fee table, not the instrument) — excluded. (c) Enacting
  **ordinances/resolutions** for DAs and GP amendments are excluded here — they live in
  `ordinances/`. (d) Residual recall gap: a rare land-use staff report titled by its
  ordinance/case number without the "Report" token (e.g. "24-5002 Private School Ordinance
  Amendment") is left unclassified rather than broadening the case-number rule and risking
  precision.
- Rerun: `python3 classify_attachments.py` (idempotent; `--dry-run` prints counts only).

**Acceptance (Sharkey pattern):** the **Funaro Rezone CC Staff Report** (2022-11-15, Council,
`text/Council_clip550_att14_22-24_Funaro_Rezone_CC_Staff_Report.txt`) recommends "*amending
the General Plan to Medium Density Residential and the zoning from RR-22 to R-4*" for 0.5
acres at 1794 West 11800 South — the primary text behind the **divided** Council vote that
same night adopting **Ordinance No. 22-24** (Councilmember McDougal dissenting, 4-1).

## How to join to minutes / votes

Join on **`date`** (+ `body`). Council rows ↔ `meeting_minutes/`; PC rows ↔
`planning_commission/`; RDA rows ↔ the RDA body in the minutes/votes layer. Staff-report and
resolution/ordinance titles carry the number (e.g. "Ordinance No. 26-16 - Majestic Homes
Rezone", "Resolution No. 26-29") and PC land-use items carry `YY-NNNN` case numbers — both
usable for motion-level linkage. **Riverton's mayor does NOT vote** on ordinary motions (six-
member council form, max council tally 5, tie-break only) — never read a staff recommendation
as a member vote.

## Scrape method (rebuildable)

1. Enumerate the flat ViewPublisher table (`ViewPublisher.php?view_id=1`, browser UA +
   Referer; ~1 MB HTML). Parse `tr.listingRow`; classify body by the meeting-name cell;
   read the `AgendaViewer.php?clip_id=` link and the bundled "Agenda Packet" cloudfront
   link. (The RSS feeds `ViewPublisherRSS.php?mode=agendas|minutes` cap at 100 items — too
   few for the full archive, so scrape the table.)
2. Filter to `Council`/`PlanningCommission`/`RDA`, `date >= 2020-01-01`.
3. GET each `AgendaViewer.php` **no-follow**; read `Location` (a `?url=<gview>` wrapper) to
   learn the era. **S3 bucket `granicus_production_attachments` has an underscore → `requests`
   TLS fails on the virtual host** — rewrite to path-style `s3.amazonaws.com/granicus_production_attachments/…`
   (polite_fetch does this for the initial URL; do it manually when resolving redirects).
4. Fetch the agenda; extract attachments:
   - era C/B PDF: regex `/URI\s*\(([^)]+)\)` over the bytes → keep `legistar` URLs (both hosts).
   - era A HTML: regex `MetaViewer\.php\?…meta_id=(\d+)` → the direct-PDF URLs.
5. Fetch each attachment through `polite_fetch.py save(..., max_bytes=4000000)` (browser UA,
   Referer, ≥1 s/host, `_fetch_log.jsonl` per date folder); oversize skips → `dropped_oversize.csv`.
6. Bundled packets: HEAD `Content-Length` only → `full_packet` index-only rows.
7. Sidecars: `python3 scripts/extract_packet_text.py riverton` (PDFs) + an html tag-strip
   pass for the era-A agenda HTML; `format`/`extraction_method` set per row from the outcomes.

## Caveats

- **`packet_kind` staff_report vs exhibit is a filename heuristic** (one-level flat links),
  not a structural fact — the real staff analysis is often in a PDF labelled by its subject
  (`26-16_Majestic_Homes_Rezone_CC_Staff_Report.pdf`) rather than the word "staff report".
- **The 4 MB cap drops bulky exhibits** (plansets, budgets, comment compilations). Every drop
  is in `dropped_oversize.csv` with a live URL; for 2020–2021 meetings the same content is
  also in the `full_packet` bundle row. Nothing is lost, just not local.
- **A handful of legistar exhibits are image-only scans** (`format=scanned`, see
  `text/_extraction_log.csv`) — OCR/vision to read those.
- **`full_packet` rows are index-only by design** — fetch on demand from `source_url`.
- **Service-area / minor bodies out of scope:** the same ViewPublisher table also carries
  Riverton Law Enforcement Service Area, Fire Service Area, Historic Preservation Commission,
  Board of Adjustment, Board of Canvassers, and Board of Equalization packets (all with the
  same AgendaViewer delivery) — not harvested here (Council/PC/RDA only); addable later by the
  same method.
- Rebuild: re-run the scrape (method above). No JSON API; a ViewPublisher markup change
  requires updating the table parser.
