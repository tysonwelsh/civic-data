# packets/ — agenda packets & staff reports (build & linkage)

Additive dataset built by `expand-city-sources` (Source 1), as-of **2026-07-13**. The staff
analysis behind Draper **City Council**, **Planning Commission**, **RDA**, **MBA**, and
**CRA** agenda items — staff memos, findings, ordinances/resolutions, exhibits — keyed by
meeting date so it joins to the existing minutes/votes. **Window: 2020-01-01 → 2026-07-13.**
Does not modify any existing dataset.

## The three delivery eras (the single most important thing to know)

Draper's agendas live on Granicus (`ViewPublisher.php?view_id=1`), but the *packet content*
behind them changed vendor twice. All three eras are enumerated from the same ViewPublisher
table; the era is per-meeting, discovered by following the `AgendaViewer.php` 302 redirect:

| Era | Window (approx) | AgendaViewer 302 target | Packet content |
|---|---|---|---|
| **A. NovusAgenda** | 2020-04 → 2023-08 | `draper.novusagenda.com/Agendapublic/MeetingView.aspx?MeetingID=<id>` (HTML) | per-item `CoverSheet.aspx?ItemID=&MeetingID=` (HTML staff memo) → `AttachmentViewer.ashx?AttachmentID=&ItemID=` (PDF staff reports/exhibits) |
| **B. DocumentViewer** | early 2020 + most RDA/MBA/CRA | `/DocumentViewer.php?file=draper_<hash>.pdf` (PDF agenda) | the PDF's **broken** `file:///C:/Windows/TEMP/CoverSheet.aspx?ItemID=&MeetingID=` URIs still leak the Novus item ids → same Novus flow as era A |
| **C. Granicus/Legistar** | 2023-09 → present | `granicus_production_attachments.s3.amazonaws.com/draper/<hash>.pdf` (PDF agenda outline) | embedded `/URI` links to `d2kbkoa27fdvtw.cloudfront.net/draper/<hash>.pdf` **staff memos** (~60 KB born-digital text: memo, findings, PC recommendation), each embedding `/URI` links to `legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/<id>/<name>.pdf` **exhibits** |

Additionally, from **2023-09** the ViewPublisher table has an **"Agenda Packet" column**:
one bundled whole-meeting PDF per meeting on `d3n9y02raazwpg.cloudfront.net` (8–36 MB,
duplicates the memos + ALL exhibits incl. the oversize ones). These are cataloged
**INDEX-ONLY** (`packet_kind=full_packet`, `stored=no`, `format=na`, `bytes` from HEAD) —
storing ~135 of them ≈ 2.5+ GB of mostly-duplicate content. This is the documented,
allowed exception to "retain every raw original" (public + re-fetchable; the URL is in
`source_url`).

## Layout

```
packets/
  raw/<YYYY-MM-DD>/                    originals verbatim, one folder per meeting date
    <date>_<body>_clip<id>_agenda.pdf|.html    the agenda (era A: MeetingView HTML)
    <date>_<body>_memo_<hash>.pdf              era-C staff memo (the staff analysis)
    <date>_<body>_exh<attId>_<name>.pdf        era-C exhibit (≤4 MB; oversize dropped+logged)
    <date>_<body>_item<ItemID>_coversheet.html era-A/B per-item Novus cover sheet
    <date>_<body>_item<ItemID>_att<AttID>.pdf  era-A/B Novus attachment (≤4 MB cap)
    _fetch_log.jsonl                           provenance per file (url,status,bytes,sha256,utc)
  text/                                extracted text sidecars (pdftotext + html tag-strip)
    _extraction_log.csv                per-PDF outcome (extracted/image_only/…)
  index.csv                            one row per cataloged document (stored or index-only)
  classify_attachments.py              deterministic doc_class classifier (rerunnable; see below)
  link_text_sidecars.py                populates the §9 text-layer columns from on-disk sidecars
  dropped_oversize.csv                 attachments >4 MB NOT downloaded (recoverable by URL)
  unrecovered.csv                      portal rows with no agenda/packet link + failed fetches
  AVAILABILITY.md                      coverage, size math, mode decision, gaps
  CLAUDE.md                            this file
```

## index.csv columns

§9 contract: `date, title, body, meeting_type, packet_kind, source_url, retrieved_date,
format, extraction_method, path` + extras `bytes, clip_id, delivery, stored` + the
2026-07-16 primary-document extension `doc_class, fetch_status, sha256, text_path,
text_chars` (see "Primary-document text layer" below).

- **date** — meeting date (`YYYY-MM-DD`), the join key. **body** — `Council`,
  `PlanningCommission`, `RDA`, `MBA`, `CRA`.
- **meeting_type** — `Special` / `Retreat` / `Board of Canvassers` / `Truth in Taxation`
  from the listing row's meeting name; blank = regular.
- **packet_kind** —
  - `agenda`: the agenda outline (era C/B PDF, era A MeetingView HTML).
  - `staff_report`: era-C cloudfront staff memo (PDF, the analysis: memo + findings +
    PC-recommendation language) or era-A/B Novus cover sheet (HTML; **often thin/boilerplate**
    — in eras A/B the real analysis usually sits in the attached `exhibit` PDFs).
  - `exhibit`: an attachment linked from a staff_report — era C legistar S3, era A/B Novus
    `AttachmentViewer.ashx`. **In eras A/B many "exhibits" ARE the full staff report**
    (e.g. `Hohl_Office_Staff_Report.pdf`); the kind is structural (link level), not semantic.
  - `full_packet`: the bundled whole-meeting PDF, index-only.
- **source_url** — for `agenda`, the portal-facing `AgendaViewer.php?clip_id=` link (stable);
  the final fetched URL per file is in that date folder's `_fetch_log.jsonl`. For everything
  else, the direct URL fetched.
- **format** — `text` (born-digital PDF, has a font layer per `pdffonts`) / `scanned`
  (raster PDF, OCR needed) / `html` / `na` (not stored).
- **extraction_method** — `pdftotext -layout` (sidecar in `text/`), `html tag-strip`
  (sidecar in `text/`), `none (image-only pdf; OCR/vision if needed)`, `none (not stored)`.
- **bytes** — file size on disk; for `full_packet` rows the HEAD `Content-Length`.
- **clip_id** — Granicus clip id (`clip<N>`), disambiguates two meetings sharing a date.
- **delivery** — `s3` / `documentviewer` / `novus_meetingview` / `novus_coversheet` /
  `novus_attachment` / `cloudfront_memo` / `legistar_s3` / `cloudfront_bundle`.
- **stored** — `yes` (raw on disk) / `no` (index-only, oversize-dropped, or fetch-failed).

## How to join to minutes / votes

Join on **`date`** (+ `body`). Council rows ↔ `meeting_minutes/minutes_index.csv` /
`all_votes.csv`; PC rows ↔ `planning_commission/`. Era-C memo titles carry the ordinance
number and case (e.g. "Public Hearing: Ordinance #1630"), and PC land-use items carry the
`YYYY-NNNN-<TYPE>` case numbers — both usable for motion-level linkage. Draper's mayor does
NOT vote (max council tally 5) — never read a staff recommendation as a member vote.

## Scrape method (rebuildable)

1. Fetch `https://draper.granicus.com/ViewPublisher.php?view_id=1` (browser UA + Referer;
   ~8 MB HTML, one flat table of ALL bodies). Parse `tr.listingRow`; classify body by the
   meeting-name cell; parse the **Agenda Packet column's direct cloudfront links** AND the
   `AgendaViewer.php?clip_id=` links. (The "Documents Selector" `<option value>` lists hold
   only MinutesViewer docs — minutes/recaps, not packets.)
2. GET each `AgendaViewer.php` **without following redirects**; read `Location` to learn
   the era. The 2023-09+ target bucket `granicus_production_attachments` has an underscore —
   **`requests` fails TLS mid-redirect-chain** (even via polite_fetch, which only rewrites
   the *initial* URL), so resolve the redirect manually and fetch the **path-style rewrite**
   `s3.amazonaws.com/granicus_production_attachments/…`.
3. Era C: regex `/URI\s*\(([^)]+)\)` over the agenda PDF bytes → memo URLs (d2kbkoa27fdvtw);
   fetch each memo; regex its bytes → legistar exhibit URLs; fetch with a **4 MB HEAD cap**
   (`polite_fetch.py save(..., max_bytes=4000000)`; skipped → `dropped_oversize.csv`).
4. Eras A/B: get ItemID/MeetingID pairs (era A: `CoverSheet.aspx` hrefs in the MeetingView
   HTML; era B: the broken `file:///` URIs in the agenda PDF). Fetch each CoverSheet HTML;
   parse `AttachmentViewer.ashx?AttachmentID=&ItemID=` links; fetch attachments. **Novus
   sends no Content-Length and ignores Range**, so oversize enforcement is stream-and-abort
   at 4 MB (logged with `bytes=">N"`).
5. Bundled packets: HEAD `Content-Length` only → index-only rows.
6. Sidecars: `python3 scripts/extract_packet_text.py draper` (PDFs) + an html tag-strip
   pass for the Novus HTML files; `extraction_method` set per row from the outcomes.

All fetches ran through `polite_fetch.py` (browser UA, Referer, ≥~1 s/host effective
spacing, retries, `_fetch_log.jsonl` per date folder) except the Novus stream-abort path,
which writes the same log format.

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

The 4,248 attachment rows (`packet_kind` ∈ `staff_report`/`exhibit`) were classified into
the pilot's content-bearing classes and each classified row LINKED to its already-on-disk
text sidecar (Draper is **classify-in-place** — the raw PDFs/HTML and `text/` sidecars
already existed from the expand-sources build, so **nothing was re-fetched**). Columns
`doc_class, fetch_status, sha256, text_path, text_chars` were added (SCHEMA_SPEC §9).

| doc_class | rows | ok | needs_ocr | index-only | what it is |
|---|---|---|---|---|---|
| staff_report | 895 | 895 | 0 | 0 | LAND-USE staff analysis: era-C `cloudfront_memo` staff memos (PC memos + Council land-use memos) + era-A/B/C exhibits titled `*Staff Report*`/`PC Report` (rezone/ZMA/LUMA/CUP/subdivision/plat/site-plan/text-amendment/DA/annex/deviation). The former 2 needs_ocr (the Avery Townhomes 18-page image-only staff report ×2) were vision-transcribed 2026-07-19 → ok |
| plan_amendment | 18 | 18 | 0 | 0 | GP/land-use-map amendment substance: `Ordinance NNNN … LUMA` adopting-ordinance PDFs + MIHP (GP Ch.4 Housing) + adopted Station Area Plans |
| development_agreement | 9 | 9 | 0 | 0 | the DA/MDA **instrument** exhibits (`AN ORDINANCE APPROVING/AMENDING A DEVELOPMENT AGREEMENT`, MDA amendment text) — NOT staff reports *about* DAs (those are `staff_report`) |
| member_memo | 0 | — | — | — | **EMPTY for Draper 2020-26** — no council-member proposal/amendment memos ride the packet corpus (honest empty class, like Sandy's DA) |

**Index-only follow-up wave (2026-07-17):** the 243 classified rows that were index-only after
the 2026-07-16 rollout (oversize >4 MB exhibits dropped by the build's 4 MB cap) were fetched,
text-extracted, and DISCARDED under the SCHEMA_SPEC §9 discard-binary exception — **2.74 GB
fetched → 204 MB text, binaries not retained** (storing them would ~triple the exhibit disk for
duplicate content already inside each meeting's `full_packet` URL). Result: **241 ok** new text
sidecars + **2 needs_ocr** (one 18-page image-only PDF re-published on 2022-08-16 & 2022-10-04
Council, same sha256 — honest OCR floor). **0 404s, 0 auth-walls** — every classified oversize
URL is still live. These discard rows keep `stored=no` (describes the binary), `path` blank,
`bytes` = fetched size, `sha256` of the fetched binary, and a `text/` sidecar; `format=text`
(born-digital) or `scanned` (needs_ocr). **No classified row is index-only any longer.**

**needs_ocr → ok vision pass (2026-07-19):** the 2 `needs_ocr` rows (the *Avery Townhomes –
Land Use & Zoning Map Amendments* staff report, application TEXTMAP-139-2022 & TEXTMAP-142-2022,
an 18-page image-only PDF re-published verbatim on 2022-08-16 Council clip610 and 2022-10-04
Council clip630, one shared sha256) were **re-fetched** from their live Novus `source_url`s
(both http 200, sha256 unchanged), **vision-transcribed** with the Read tool
(`extraction_method=claude_vision`, 22,870 chars each: full staff report + Engineering review +
legal description + figure notes for the map/plat exhibits), and the binaries **discarded** per
the §9 discard-binary exception. Both rows now `fetch_status=ok`, `format=scanned`, `stored=no`,
`text_path` set. **Draper packets now carry 0 needs_ocr rows.** The discard rows' §9 columns
are maintained directly in `index.csv` (no binary on disk to re-derive them from).

**`link_text_sidecars.py` is now discard-row-safe (fixed 2026-07-19).** The former hazard —
the script blanked `text_path`/`text_chars`/`fetch_status` on every `stored=no` discard row
because it predated the 2026-07-17 discard wave — is FIXED: the script now detects a §9 discard
row (`stored=no` with a populated `text_path`) and PRESERVES it verbatim (never resets or
recomputes its `doc_class`/`fetch_status`/`sha256`/`text_path`/`text_chars`/`extraction_method`),
including the 2 vision-transcribed Avery rows, while still re-linking the 679 stored binaries.
Proven byte-identical: a full rerun is now a clean no-op (index.csv sha256 unchanged; the 243
discard rows and both Avery rows byte-for-byte identical). Backup of the pre-fix state:
`_backups/2026-07-19-lm-wave-followups/draper/packets/`. Safe to rerun.

- `fetch_status`: `ok` = text sidecar present (`text_path`/`text_chars` set, `sha256` of the
  fetched binary); `needs_ocr` = image-only, no usable text layer (honest OCR floor — **0 rows
  as of 2026-07-19**; the former 2 Avery staff-report rows were vision-transcribed to ok).
  **No blank/index-only classified rows remain** (all 243 follow-ups resolved 2026-07-17; live
  URLs still in `source_url` / `dropped_oversize.csv`).
- **Classifier** (`classify_attachments.py`): deterministic title + `body` + `packet_kind`
  + `delivery` token rules, **no matter table** (Draper has none). Land-use scoping of the
  era-C Council staff memos (whose title only names an ordinance number, e.g. "Public
  Hearing: Ordinance #1633") uses a READ-ONLY join to `../ordinances/index.csv`
  (`ordinance_no → land_use`). PC-body `cloudfront_memo` = land-use by definition (the PC is
  Draper's land-use body). `link_text_sidecars.py` populates the four provenance columns.
  Both idempotent/rerunnable.
- **Quality gates (2026-07-16, ground-truthed against on-disk sidecars/PDFs):**
  - `staff_report` precision **50/50 = 100%** (random n=50); the heuristic Council-memo
    channel swept in full (n=75) → **0 non-land-use false positives** (all are land-use /
    housing-element / station-area / GP-element / boundary-adjustment staff memos).
    Recall: random n=100 unclassified in-scope rows → **0 missed in-scope docs (0% est.
    miss)**.
  - `plan_amendment` precision **18/18 = 100%** (whole class desk-verified — every ok row
    opens `AN ORDINANCE AMENDING THE OFFICIAL LAND USE MAP…` or `MIHP … Chapter 4 HOUSING`).
  - `development_agreement` precision **9/9 = 100%** (whole class — every one is the DA
    instrument/ordinance text).
- **Boundary decisions (documented, not bugs):**
  - `staff_report` = **land-use only** (Sandy taxonomy). Council era-C admin memos —
    resolutions, local-consent liquor licenses, appointments, non-land-use ordinances — are
    left **blank** (honest); a budget/interlocal memo is not a land-use staff report.
  - **`novus_coversheet` (1,032 thin era-A/B HTML coversheets) are EXCLUDED by design** —
    they are boilerplate ("MEMO To: … Re: … Comments:" with empty fields; verified thin on
    sample). The real staff analysis rides the attached **exhibit**, which IS classified, so
    no analysis text is lost.
  - `development_agreement` catches the **instrument** exhibit; "…DA Staff Report/PC
    Report…" exhibits fall through to `staff_report` (the `\breport\b` exclusion).
  - `plan_amendment` requires an ordinance/named-plan token, so agenda-item **slide-deck
    presentations** (e.g. "5.a City Initiated … LUMA and ZMA", vicinity/aerial maps) stay
    unclassified rather than mis-labeled.
  - Rezone (ZMA) / text ordinances are **not** a target class here — they belong to the
    `ordinances/` dataset.
- **Acceptance (Sharkey pattern):** the **Ordinance #1625** staff memo
  (`text/2024-10-15_Council_memo_a8b30134aa9a193927383f4a5b6cab020.txt`) is the primary
  text behind Draper's **single mayoral tie-break** (2024-10-15 motion 3, `3-2 Pass` —
  Mayor Walker breaking a 2-2 split, `all_votes.csv`). The memo reveals the matter the
  minutes only tally as "Ordinance #1625": *"David Nixon, who resides at 987 Old English Rd,
  is requesting the City Council vacate the right-of way adjacent to his property"* (a ROW
  vacation tied to the 1995 Wild Rose Subdivision Phase 2 development agreement).
- Rerun: `python3 classify_attachments.py && python3 link_text_sidecars.py` (idempotent).

## Caveats

- **Era-A/B cover sheets are often boilerplate** ("MEMO To: … Re: … ATTACHMENTS: …" with
  empty fields) — the staff analysis is in the attachments. Do not read a thin coversheet
  as "no staff analysis existed".
- **The 4 MB cap drops some full staff reports**, especially PC staff reports with embedded
  maps/plats (5–23 MB) and "all public comment" compilations. Every drop is in
  `dropped_oversize.csv` with a live URL, and the meeting's `full_packet` row (era C)
  contains the same content — nothing is lost, just not local.
- **Era-C `staff_report` memos are the cleanest text layer** (born-digital, uniform MEMO
  format, "Re:" line = the index `title`). Era-A/B analysis is PDF attachments of varying
  quality; a few are image-only (see `format=scanned` + extraction log).
- **`full_packet` rows are index-only by design** — fetch on demand from `source_url`;
  vision/OCR may be needed for map-heavy pages.
- Two meetings can share a date folder (e.g. Council + CRA the same Tuesday) — filenames
  carry body + clip and `index.csv` rows are keyed (date, body).
- **HPC / Tree Committee / other minor bodies also publish packets** on the same
  ViewPublisher table but are out of scope here (Council/PC/RDA/MBA/CRA only).
- Rebuild: re-run the scrape (method above). The portal has no JSON API; a ViewPublisher
  markup change requires updating the table parser.
