# Agenda packets / supporting documents — availability (Emigration Canyon)

**Source type 1** of the `expand-city-sources` skill. Purely additive — does **not** modify any
existing Emigration Canyon dataset. **As-of: 2026-07-16** (doc_class primary-document text layer
added; source-type-1 packet acquisition as-of 2026-07-14).

Emigration Canyon is a ~1,600-person canyon community (Salt Lake County; **metro township
2017-01-01 → CITY 2024-05-01** via H.B. 35), governed throughout by one 5-member all-at-large
council (peer-selected **voting mayor**, Millcreek pattern) plus its own Planning Commission. It
holds ~11 council meetings/yr + a roughly-monthly PC. A **thin, sparse packet record is the
correct, honest result** — but the town posts unusually rich per-item supporting documents on
Utah Public Notice, so the file count is healthy.

## What "packet" means here + the single portal

Emigration Canyon has **no city document CMS** (no CivicPlus/Granicus/Legistar/GoDaddy). Utah
Public Notice (PMN) is the **only** canonical source; the MSD AgendaCenter is a secondary mirror
not needed for this build. Every meeting notice carries labeled attachments — an **Agenda**,
**Approved Minutes**, one or more **Supporting Documents / item handouts** (all under the PMN
category label `Public Information Handout`, a few mislabeled `Other` / `Audio Recording`), and
often an **Audio Recording (.MP3)**. The **packet** = the Supporting-Documents bundle + the
item-level handouts (resolution/ordinance drafts, interlocal agreements, staff/liaison reports,
exhibits, budgets, hearing notices) attached to a meeting, keyed by `date` + `body` (+
`meeting_type`) so it joins `meeting_minutes/all_votes.csv` and `planning_commission/all_votes.csv`.

| Body | Dates | Source | What it is |
|---|---|---|---|
| **Council** | 2019–2026 | **Utah PMN body 5809** | per-meeting `Public Information Handout` attachments — Supporting-Documents bundles, resolution/ordinance drafts, UPD/UFA liaison reports, budgets, agreements, hearing notices |
| **Planning Commission** | 2019–2026 | **Utah PMN body 1562** (MSD-staffed) | `YYMMDD_EmigrationPC_Packet.pdf` / `_TPC_Packet` bundles, staff reports, public-hearing notices, general-plan / land-use case exhibits |

Unlike the sibling MSD township Copperton (which splits Council between PMN and a GoDaddy town
site), Emigration Canyon publishes **both bodies entirely on PMN** — there is no second portal.

**Fetch mechanics.** The notice **list** pages are enumerated via the cumulative GET
`https://www.utah.gov/pmn/list/notices.html?id=<body>&page=N` — the **`&page=N` form is REQUIRED**
(the bare `?id=` endpoint 500s "Technical Difficulties"); paging is cumulative, so the harvest
walks page 0,1,2,… until the notice-id set stops growing (council 49 pages / 238 notices; PC 61
pages / 290 notices), caching each page under `raw/_pages/`. Each `<tr>` row carries the meeting
date + its `<li>` file links with `aria-label` filenames and category labels, so classification is
done off the **filename** (the `Public Information Handout` label covers agendas, packets, and item
PDFs alike). The documents live at `https://www.utah.gov/pmn/files/<fileId>.pdf` (**⚠ NOT
pmn.utah.gov**; opaque non-sequential ids — harvested, never synthesized) and download through
`scripts/polite_fetch.py` (GET-only, ≥1s/host, browser UA, logged).

## Primary-document text layer (doc_class, 2026-07-16)

The `expand-city-sources` Source-7 classifier (`classify_attachments.py`) was run over the
in-scope attachment rows (362 `supporting_docs` + `staff_report`; the 13 `full_packet` containers
are skipped). Deterministic, rerunnable, and **classify-in-place** — no re-fetch (EC already stores
every raw + a born-digital `text/` sidecar), so it only assigns `doc_class` and links existing text.

**17 classified — a small, correct count for a ~1,600-pop MSD-staffed town:**

| doc_class | rows | ok | needs_ocr |
|---|---|---|---|
| staff_report | 15 | 15 | 0 |
| plan_amendment | 2 | 1 | 1 |
| member_memo | **0 (honest empty)** | — | — |
| development_agreement | **0 (honest empty)** | — | — |

- `staff_report` = MSD land-use/code staff reports (Dark Sky / Night Lighting, Comprehensive Code
  Update, stream-setback overlay, rezone/waiver/APA/conditional-use cases). 14 are title-matched;
  1 (`CUP2025-001542 Fixed.pdf`) is caught by the in-TEXT MSD staff-report template.
- `plan_amendment` = the 2022 GP-adoption ordinance draft + the 2025-O-09 zoning-**map**-change
  ordinance (image-only → `needs_ocr`, the lone unreadable classified doc).
- `member_memo` empty: EC council is narrative-tally (mayor votes) and files no proposal memos;
  the 3 packet "memo" titles are MSD staff/legal/agency memos, verified against their sidecars.
- `development_agreement` empty: the "agreement" titles are interlocal/utility-program agreements;
  "EC DA Ordinance" is a DA-**enabling** ordinance (zoning text), not an instrument.
- **Gates:** precision 100% both non-empty classes (whole-class ground-truthed); recall — full
  sweep of all 345 unclassified in-scope rows found 0 genuine misses (2 documented boundary blanks:
  the 2022 GP "Staff Recommendation" summary and the 2025-11-17 Leick documents+comments bundle).
- **Not re-derived here:** the pre-existing `sha256` city-extra column (16-char prefix of the full
  digest of the stored raw, present for every row) already satisfies the §9 doc_class `sha256`
  provenance — EC retains raw, so nothing is fetched or discarded. Full method + boundary
  rationale: `CLAUDE.md` "Primary-document text layer".

## Coverage retrieved — STORED (1.65 GB)

**375 packet documents stored, 1.65 GB.** All raw originals retained under `raw/<date>/`; per-file
provenance (URL, HTTP status, bytes, **sha256**, retrieved_utc) in each `raw/<date>/_fetch_log.jsonl`.
STORED (not index-only) is the right mode for this tiny town — the whole set is on disk and
re-readable. The total is **modestly above the ~1.5 GB stored-vs-index guideline**, driven almost
entirely by a **handful of oversized general-plan PDFs** (a 472 MB + 137 MB split 2019-01-17
Planning-Commission General-Plan/TPC packet; a 107 MB + 81 MB 2020-11-19 draft General Plan +
appendices; a 59 MB 2025 property-documents exhibit; a 52 MB 2026-02-17 combined agenda-with-
supporting bundle). The other ~365 files are ordinary small staff-report / handout PDFs. Nothing
was capped or dropped for size.

| Body | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Total | Dates |
|---|---|---|---|---|---|---|---|---|---|---|
| **Council** | 1 | 1 | 17 | 81 | 55 | 43 | 49 | 22 | **269** | ~72 |
| **Planning Commission** | 8 | 8 | 9 | 17 | 15 | 11 | 25 | 13 | **106** | ~59 |

- **131 (date, body) combinations**, 2019-01-17 → 2026-07-09.
- **`packet_kind`:** 348 `supporting_docs`, 14 `staff_report`, 13 `full_packet`.
- **`meeting_type`:** mostly blank (filenames say "CC Meeting" / "PC"); 1 `Workshop`, 4 `Emergency`,
  2 `Special` detected from filenames. Same-day **Workshop (6 PM) + Regular (7 PM)** council
  meetings post separate notices; where both carry docs they are disambiguated by date + body (+
  meeting_type when the filename says so).
- **Format:** **350 born-digital `text`** — 324 got a `text/<stem>.txt` sidecar via
  `scripts/extract_packet_text.py`; 24 are `.docx`/`.xlsx` retained raw (no PDF sidecar); 2 are
  oversize PDFs (>120 MB — the 472 MB & 137 MB 2019 GP packet halves; retained raw, no sidecar) —
  **plus 25 `scanned`** image-only PDFs (listed with `extraction_method` noting vision/OCR is needed
  to read them).

## Genuine gaps (not fabricated, not scraper misses)

1. **2017–2018 packet/handout attachments are 404-PURGED (retention) — the effective packet floor
   is 2019, LATER than the 2018-10 *minutes* floor.** PMN keeps a notice's *minutes* attachment far
   longer than its bulkier *handout/packet* attachments. Every 2017 and pre-December-2018 meeting
   notice still lists a Supporting-Docs/packet file-id, but **17 of those attachments return HTTP
   404** — verified this run as failed fetches in `raw/<date>/_fetch_log.jsonl` (2017: 9 · 2018: 8),
   spanning **Council 2017-08 → 2018-12** and **PC 2017-07 → 2018-11**. This is the same retention
   purge documented for this repo's minutes layer (`../CLAUDE.md`: recovered council minutes begin
   2018-10, PC 2018-11; file-id ceiling ≈ 450000). The earliest **surviving** packet is
   **2019-01-17** (PC) / a lone **2019 council** doc; council 2019–2020 is especially thin (1 doc
   each) because the bulk-handout purge boundary runs later for council than the minutes boundary.
   The pre-2019 meetings themselves are real (their notices exist) — only the packet PDFs are gone.
   Town data floor is **2017**; the packet floor is honestly **2019**.
2. **No public-correspondence archive in the packets.** Consistent with the repo's honest-empty
   `public_comments` verdict, the Supporting-Docs bundles carry staff materials, not resident
   written comment (a couple of "CC Meeting - Public Comments" PDFs are the clerk's in-meeting
   speaker handouts, not a correspondence inbox). No comment dataset is created or modified here.

## What was intentionally excluded (kept out of the packet dataset)

- **Meeting Minutes** (label `Meeting Minutes` or a `*minutes*` filename) — already the
  `meeting_minutes/` + `planning_commission/` datasets.
- **Agenda-ONLY documents** — a bare `*Agenda*` PDF that is not also a Supporting-Docs bundle /
  packet (the substantive agenda content is inside the packet bundles that ARE kept).
- **Audio recordings** (`.MP3`/`.wav`/`.m4a`) — out of scope for packets.
- **Meeting-cancellation / no-meeting / annual-schedule notices** (2 WS-meeting "Cancellation
  Notice" PDFs). ⚠ Distinguished from substantive **resolutions** that merely say "cancel" — the
  2021 "Resolution to Cancel Election" and the 2025 "R2025-10 Canceling the 2025 Mayoral Race" are
  **kept** (they are real legislative packet items).
- **Re-posted PRIOR-meeting docs** — a bare `MM-DD-YY.ext` whose date ≠ the notice's meeting date
  (a prior meeting's own agenda/minutes re-attached for approval; the same-date bare-date doc IS
  kept as that meeting's packet).
- **Branding / images** (logos, `IMG_*`).

## How this was checked

`build_packets_index_ec.py --harvest` walked the cumulative PMN notice lists for bodies 5809 and
1562 (`.../list/notices.html?id=<body>&page=N`, caching every page under `raw/_pages/`), classified
every attachment by filename/label, applied the exclusions above, then `--fetch` downloaded the
survivors through `scripts/polite_fetch.py` (**all** candidates attempted, including purged-era ones,
so the 17 × 404 are recorded as evidence in the fetch logs) and `--index` built `index.csv` (reading
`text/_extraction_log.csv` to mark the 25 scanned + 2 oversize + 24 office-doc files). Text corpus
screened with `audit-city-data/scripts/screen_corpus.py` — 0 read errors; every flag benign
(Spanish/sample ballots → low dict-ratio; columnar slides & hearing notices → split-word; packets
with maps/plats & signed ordinances → weird-char). Passes
`expand-city-sources/scripts/validate_dataset.py`.
