# packets/ availability — Riverton City

**As-of:** 2026-07-13. **Source:** Granicus agenda portal
(`rivertoncity.granicus.com/ViewPublisher.php?view_id=1`) — one flat table for all bodies.
**Mode:** STORED (separable born-digital staff reports; bulky exhibits capped, 2020–2021
bundles index-only). **Bodies harvested:** City Council, Planning Commission, Redevelopment
Agency (RDA). **Window:** 2020-01-07 → 2026-07-09 (the repo's 2020 data floor; the Granicus
archive itself reaches back to 2015).

## Coverage (what was retrieved)

| Body | Meetings | Window | Stored docs | Stored bytes |
|---|---|---|---|---|
| City Council | 139 | 2020-01-07 → 2026-06-16 | 2,263 | 1,112 MB |
| Planning Commission | 127 | 2020-01-23 → 2026-07-09 | 630 | 561 MB |
| RDA | 29 | 2020-04-21 → 2026-06-02 | 122 | 130 MB |
| **Total** | **295** | **2020-01-07 → 2026-07-09** | **2,613** | **1.80 GB** |

`index.csv` has **3,015 rows**: 295 agenda outlines + 561 staff_report + 2,141 exhibit + 18
full_packet (index-only). **2,613 stored** on disk (1.80 GB); **402 not stored** (see below).
Every stored PDF has a `pdftotext -layout` text sidecar unless image-only (**2,490 sidecars**;
121 PDFs are scans/errors with no sidecar — `format=scanned`, `text/_extraction_log.csv`).

## STORED-mode decision + size math

Riverton's Granicus agenda outlines are small born-digital PDFs (~50–210 KB) that link, one
level deep, to each item's staff report / resolution / ordinance / exhibit as **separate**
born-digital PDFs — most are small text documents, a minority are large map/plan exhibits.
That is the draper-era-C profile, so STORED mode fits: keep the small staff analysis on disk,
cap the bulky exhibits.

- **Stored:** 2,613 docs / **1.80 GB** (all 295 agenda outlines + every staff report/exhibit
  ≤ 4 MB).
- **Oversize exhibits capped at 4 MB:** **301** attachments HEAD-probed over the cap and
  **not** downloaded — a further **5.44 GB** avoided. All 301 are logged in
  `dropped_oversize.csv` with a live `source_url` (re-fetchable on demand; typically plansets,
  budgets, engineering drawings, comment compilations). Recorded in `index.csv` as
  `stored=no, format=na`.
- **Bundled whole-meeting packets — INDEX-ONLY:** for **18** meetings (2020-01…2021-05) the
  ViewPublisher "Agenda Packet" column exposes a bundled cloudfront PDF (0–25 MB, **145 MB**
  total). These **duplicate** the separable staff reports already stored, so they are
  catalogued index-only (`packet_kind=full_packet, stored=no, format=na`, `bytes` from HEAD).
  This is the documented, allowed exception to "retain every raw original" — public and
  re-fetchable from `source_url`; vision/OCR needed to read one. After early-2021 Granicus
  stopped populating that column, so later meetings have no bundle (the separable staff
  reports are the packet).

Storing everything uncapped would be ≈ 1.80 GB + 5.44 GB (oversize) + 0.14 GB (bundles) ≈
**7.4 GB**; STORED-with-cap keeps the searchable staff analysis at **1.80 GB**.

## Vendor finding — three agenda-delivery eras (all one Granicus table)

Every archived meeting has an `AgendaViewer.php?clip_id=<n>` link that **302-redirects** (via
a Google `docs.google.com/gview?url=` wrapper) to one of three era-specific targets, resolved
no-follow:

1. **S3 agenda-outline PDF** (2020-05 → present, **291** meetings): target
   `granicus_production_attachments.s3.amazonaws.com/rivertoncity/<hash>.pdf`. The bucket name
   has an **underscore**, so `requests`/TLS rejects the virtual host — rewrite to path-style
   `s3.amazonaws.com/granicus_production_attachments/…`. The PDF embeds `/URI` links to
   per-item attachments on `legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/…`
   and/or `rivertoncity.granicus.com/services/legistar/download/pdf/…`.
2. **GeneratedAgendaViewer HTML** (early 2020, **2** meetings: 2020-01-07, 2020-08-04):
   AgendaViewer → `/GeneratedAgendaViewer.php?...` HTML agenda whose items link to
   `MetaViewer.php?...&meta_id=<id>` — each serving the attachment PDF **directly** (200, no
   redirect).
3. **DocumentViewer PDF** (**2** meetings: 2020-03-12, 2025-02-27): AgendaViewer →
   `/DocumentViewer.php?file=rivertoncity_<hash>.pdf` PDF agenda outline; same embedded
   `/URI` legistar links as era 1.

(The `ViewPublisherRSS.php?mode=agendas|minutes` feeds cap at 100 items, too few for the full
archive — the flat ViewPublisher table was scraped instead.)

Because the agenda outlines link **one level deep and flat** (no separate memo layer),
`packet_kind` = staff_report vs exhibit is assigned by a **filename heuristic**
(`*Staff_Report*`/`*_Report*`/`*Memo*` → staff_report, else exhibit), NOT a structural fact.
Do not read `exhibit` as "not staff analysis".

## Gaps (honest)

- **83 exhibit attachments — legistarweb S3 403 AccessDenied (permanent).** All from **2020**
  meetings. The agenda outlines cite the exact object URL, but
  `legistarweb-production.s3.amazonaws.com` now returns `AccessDenied` for those older objects
  (verified 2026-07-13; the granicus `/services/legistar/download/` proxy and `MetaViewer.php`
  also fail for these ids). Recorded in `index.csv` as `stored=no, format=na,
  extraction_method="none (403 AccessDenied; legistarweb restricted this 2020 object)"`. **Not
  lost:** the stored agenda outline lists each item, and for the 2020 meetings that carry a
  bundled `full_packet` the same content is inside that bundle. ~3% of all attachments.
- **5 attachments on 2026-04-21 (clip839) — Granicus MediaManager auth-wall (not
  recoverable, 2026-07-17).** att8–att12 (Ordinance 26-06 cover + ordinance, the **26-06
  Timberline Development Agreement CC Staff Report** [att10], and Resolution 26-15 + Drought
  Mitigation Plan) were fetched at build via the
  `rivertoncity.granicus.com/services/legistar/download/pdf/<id>/` proxy, which for these five
  ids returns a **Granicus MediaManager login page** (HTML, ~4.6 KB, `sealIsEnforced:true`) —
  not the PDF. The other eight attachments on the same meeting fetched fine, so the wall is
  **per-object, not per-meeting**. Corrected in `index.csv` (2026-07-17) to the honest §9
  status `fetch_status=error:auth_wall`, `format=na` (was the misleading `scanned`/`needs_ocr`
  — the stored 4.6 KB blob is a login HTML, not a scannable image, so OCR/vision cannot
  recover it). Re-acquisition probes that were tried and FAILED (2026-07-17):
  (a) the **Legistar S3 twin** (`legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/<id>/`)
  — the S3 upload-id lives only in the Legistar back-end and is a different id space from the
  granicus download-id (download-id `4040041` on S3 → `AccessDenied`); the 2026-04-21 agenda
  outline embeds only the granicus-proxy URLs (unlike the 2025-12-11/2026-02-26 PC agendas,
  which embedded the S3 URLs directly, so those Timberline PC staff reports ARE stored);
  (b) the **Legistar InSite** (`rivertoncity.legistar.com` — Calendar/Legislation/MeetingDetail/View.ashx)
  is WAF-locked to scripted access (returns a 19-byte "Invalid parameters!" stub to every
  page; OData webapi disabled for this client); (c) the **full agenda packet** — Granicus
  `AgendaViewer.php?clip_id=839` 302-redirects only to the short agenda **outline** we already
  store, not a merged packet; PMN carries the same outline. The staff report exists (it is the
  Council presentation of the Timberline DA / PLZ-25-4009, whose PC-version staff reports are
  in the repo at 2025-12-11 and are index-only oversize at 2026-02-26), but its born-digital
  text is reachable only through the authenticated Legistar back-end or a GRAMA request. **A
  drafted records request is in the 2026-07-17 wave report.** ~0.2% of attachments.
- **301 oversize exhibits (>4 MB)** intentionally not downloaded — in `dropped_oversize.csv`
  with live URLs (see size math above). Not a discovery gap; a disk-budget choice.
- **18 bundled full_packets index-only** (2020–2021) — content duplicated by stored separable
  reports; fetch on demand.
- **No early-2020 gap:** the 2020 data floor is fully covered (earliest meeting 2020-01-07).
  The recon's "Dec 2020 Granicus floor" was conservative — the archive actually holds 2015+;
  nothing earlier needed from PMN or the Revize page.
- **Out of scope (present, not harvested):** the same ViewPublisher table also carries
  Riverton Law Enforcement Service Area (60), Fire Service Area (32), Historic Preservation
  Commission (4), Board of Adjustment (2), Board of Canvassers (7), Board of Equalization (4)
  packets — same AgendaViewer delivery, addable later by the identical method.

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, added 2026-07-16)

Classify-in-place (Bucket A): a `doc_class` label + the §9 columns (`doc_class`,
`fetch_status`, `sha256`, `text_path`, `text_chars`) added to `index.csv` over the existing
sidecars — **no new fetching**. `classify_attachments.py` scans the **staff_report + exhibit
rows as ONE candidate pool** (2,702 rows; `packet_kind` here is a filename heuristic, not
structural), title-token only (Riverton has no matter table).

| doc_class | rows | ok (text on disk) | needs_ocr | index-only (no binary) |
|---|---|---|---|---|
| staff_report | 522 | 317 | 1 | 204 |
| development_agreement | 8 | 8 | 0 | 0 |
| member_memo | 0 | — | — | — (honest empty) |
| plan_amendment | 0 | — | — | — (honest empty) |
| **classified total** | **530** | **325** | **1** | **204** |

Unclassified candidate rows: **2,172** (minutes, enacting ordinances/resolutions → `ordinances/`,
contracts/interlocal/lease agreements, budget/finance items, appointments, bond releases,
proclamations, policies, packet bundles, maps/exhibits — none are land-use staff reports).

**The 204 classified index-only rows (honest — counted, not lost):** these are staff reports
that carry no local binary or sidecar because the raw was never downloaded —
**189 oversize-capped (>4 MB)** (live `source_url` in `dropped_oversize.csv`) + **15
permanently-403 legistarweb 2020 exhibits** (dead object, listed in the 83-row 2020 403 gap
above). They are classified (title is unambiguous) with `fetch_status` blank and blank
`sha256` (oversize were HEAD-probed only; 403s never fetched — no hash exists for either).
The **1 needs_ocr** row is a stored image-only scan (`format=scanned`) awaiting a vision pass.

**Gates (2026-07-16, ground-truthed against on-disk sidecars):** staff_report precision
100% (n=50), development_agreement precision 100% (whole class n=8); recall est. miss ≈ 0.4%
(2 title-token misses found by sweeping all 1,873 unclassified sidecars for the staff-report
MEMORANDUM template). member_memo + plan_amendment are honest empties (see `CLAUDE.md` for the
method, boundary decisions, and the Funaro-Rezone acceptance doc). Rerun:
`python3 classify_attachments.py`.

## Provenance

Every fetch went through `scripts/polite_fetch.py` (browser UA, Referer
`rivertoncity.granicus.com/ViewPublisher.php?view_id=1`, ≥1 s/host, retries) — one
`_fetch_log.jsonl` per `raw/<date>/` folder (url, http status, bytes, sha256, retrieved_utc).
Text sidecars via `scripts/extract_packet_text.py riverton`; per-file outcome in
`text/_extraction_log.csv`.
